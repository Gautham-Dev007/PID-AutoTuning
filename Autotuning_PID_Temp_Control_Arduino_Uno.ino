#include <OneWire.h>
#include <DallasTemperature.h>
#include <TimerOne.h>
#include <EEPROM.h>

// Pin definitions
#define ONE_WIRE_BUS 9
#define HEATER_PIN 13

// Control parameters
float tempSetpoint = 75.0;   // Now a variable instead of a constant
#define KP 10.0
#define KI 2.0
#define SAMPLE_TIME 0.1

// EEPROM addresses
#define ADDR_AUTOTUNE_DONE 0
#define ADDR_DELAY_TIME 1
#define ADDR_RISE_TIME 5
#define ADDR_PEAK_TIME 9
#define ADDR_SETTLE_TIME 13
#define ADDR_SETPOINT 17     // EEPROM address for setpoint (4 bytes for float)

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Volatile variables for interrupt
volatile byte heaterDutyCycle = 0;
volatile byte counter = 0;

// Control variables
float integralError = 0.0;
bool autotuneRunning = false;
bool autotuneDone = false;
bool systemRunning = true;   // Tracks system state

// Autotune timing variables
unsigned long delayTime = 0;    // Time to reach 50% of setpoint
unsigned long riseTime = 0;     // Time to reach setpoint
unsigned long peakTime = 0;     // Time to reach peak overshoot
unsigned long settleTime = 0;   // Time for 3 cycles completion
unsigned long autotuneStartTime = 0;
float peakTemp = 0.0;
int cycleCount = 0;
bool prevBelowSetpoint = true;

// Ziegler-Nichols variables
float overshoot = 0.0;
float Ku = 0.0;
float Tu = 0.0;
float calculatedKp = 0.0;
float calculatedKi = 0.0;
float calculatedKd = 0.0;

// Serial command buffer
String serialCommand = "";

void setup() {
  Serial.begin(9600);
  sensors.begin();
  
  pinMode(HEATER_PIN, OUTPUT);
  digitalWrite(HEATER_PIN, LOW);
  
  Timer1.initialize(20000);
  Timer1.attachInterrupt(timerISR);
  
  // Load saved autotune state
  autotuneDone = EEPROM.read(ADDR_AUTOTUNE_DONE);
  if (autotuneDone) {
    delayTime = EEPROM.read(ADDR_DELAY_TIME) | (EEPROM.read(ADDR_DELAY_TIME + 1) << 8) |
                (EEPROM.read(ADDR_DELAY_TIME + 2) << 16) | (EEPROM.read(ADDR_DELAY_TIME + 3) << 24);
    riseTime = EEPROM.read(ADDR_RISE_TIME) | (EEPROM.read(ADDR_RISE_TIME + 1) << 8) |
               (EEPROM.read(ADDR_RISE_TIME + 2) << 16) | (EEPROM.read(ADDR_RISE_TIME + 3) << 24);
    peakTime = EEPROM.read(ADDR_PEAK_TIME) | (EEPROM.read(ADDR_PEAK_TIME + 1) << 8) |
               (EEPROM.read(ADDR_PEAK_TIME + 2) << 16) | (EEPROM.read(ADDR_PEAK_TIME + 3) << 24);
    settleTime = EEPROM.read(ADDR_SETTLE_TIME) | (EEPROM.read(ADDR_SETTLE_TIME + 1) << 8) |
                (EEPROM.read(ADDR_SETTLE_TIME + 2) << 16) | (EEPROM.read(ADDR_SETTLE_TIME + 3) << 24);
  }
  
  // Load last setpoint from EEPROM
  EEPROM.get(ADDR_SETPOINT, tempSetpoint);
  if (isnan(tempSetpoint) || tempSetpoint < 0 || tempSetpoint > 100) {
    tempSetpoint = 75.0;  // Default if invalid or uninitialized
  }
  
  Serial.println("System Ready. Type 'AUTOTUNE' to start autotuning, 'PI' for PI control, 'Sxx.x' to set setpoint, 'STOP' or 'H0' to stop.");
}

void timerISR() {
  counter++;
  if (counter < heaterDutyCycle) {
    digitalWrite(HEATER_PIN, HIGH);
  } else {
    digitalWrite(HEATER_PIN, LOW);
  }
  if (counter >= 100) {
    counter = 0;
  }
}

void saveAutotuneValues() {
  EEPROM.write(ADDR_AUTOTUNE_DONE, 1);
  EEPROM.write(ADDR_DELAY_TIME, delayTime & 0xFF);
  EEPROM.write(ADDR_DELAY_TIME + 1, (delayTime >> 8) & 0xFF);
  EEPROM.write(ADDR_DELAY_TIME + 2, (delayTime >> 16) & 0xFF);
  EEPROM.write(ADDR_DELAY_TIME + 3, (delayTime >> 24) & 0xFF);
  
  EEPROM.write(ADDR_RISE_TIME, riseTime & 0xFF);
  EEPROM.write(ADDR_RISE_TIME + 1, (riseTime >> 8) & 0xFF);
  EEPROM.write(ADDR_RISE_TIME + 2, (riseTime >> 16) & 0xFF);
  EEPROM.write(ADDR_RISE_TIME + 3, (riseTime >> 24) & 0xFF);
  
  EEPROM.write(ADDR_PEAK_TIME, peakTime & 0xFF);
  EEPROM.write(ADDR_PEAK_TIME + 1, (peakTime >> 8) & 0xFF);
  EEPROM.write(ADDR_PEAK_TIME + 2, (peakTime >> 16) & 0xFF);
  EEPROM.write(ADDR_PEAK_TIME + 3, (peakTime >> 24) & 0xFF);
  
  EEPROM.write(ADDR_SETTLE_TIME, settleTime & 0xFF);
  EEPROM.write(ADDR_SETTLE_TIME + 1, (settleTime >> 8) & 0xFF);
  EEPROM.write(ADDR_SETTLE_TIME + 2, (settleTime >> 16) & 0xFF);
  EEPROM.write(ADDR_SETTLE_TIME + 3, (settleTime >> 24) & 0xFF);
}

void autotune(float temperature) {
  unsigned long currentTime = millis() - autotuneStartTime;
  
  // Simple on/off control during autotune
  heaterDutyCycle = (temperature < tempSetpoint) ? 100 : 0;
  
  // Calculate delay time (time to 50% setpoint)
  if (!delayTime && temperature >= tempSetpoint * 0.5) {
    delayTime = currentTime;
  }
  
  // Calculate rise time (time to setpoint)
  if (!riseTime && temperature >= tempSetpoint) {
    riseTime = currentTime;
  }
  
  // Track peak overshoot
  if (temperature > peakTemp) {
    peakTemp = temperature;
    peakTime = currentTime;
    if (peakTemp > tempSetpoint) {
      overshoot = peakTemp - tempSetpoint;
    }
  }
  
  // Count cycles (crossings of setpoint)
  bool currentBelowSetpoint = temperature < tempSetpoint;
  if (prevBelowSetpoint != currentBelowSetpoint) {
    cycleCount++;
    prevBelowSetpoint = currentBelowSetpoint;
  }
  
  // Check for 3 cycles completion
  if (cycleCount >= 6) {  // 6 crossings = 3 full cycles
    settleTime = currentTime;
    autotuneRunning = false;
    autotuneDone = true;
    
    // Calculate Ziegler-Nichols parameters
    Ku = 4 * 100 / (3.14 * overshoot);  // Ultimate gain adjusted for 0-100 scale
    Tu = (float)(settleTime - riseTime) / 3.0;  // Average period of 3 cycles
    
    // Ziegler-Nichols PI tuning
    calculatedKp = 0.45 * Ku;          // PI tuning rule
    calculatedKi = 0.54 * Ku / Tu;     // PI tuning rule
    calculatedKd = 0.0;                // Not using D term
    
    saveAutotuneValues();
    
    Serial.println("Autotune Complete!");
    Serial.print("Delay Time: "); Serial.print(delayTime); Serial.println("ms");
    Serial.print("Rise Time: "); Serial.print(riseTime); Serial.println("ms");
    Serial.print("Peak Time: "); Serial.print(peakTime); Serial.println("ms");
    Serial.print("Settle Time: "); Serial.print(settleTime); Serial.println("ms");
    Serial.print("Overshoot: "); Serial.print(overshoot); Serial.println("C");
    Serial.print("Ku: "); Serial.print(Ku); Serial.println();
    Serial.print("Tu: "); Serial.print(Tu); Serial.println("ms");
    Serial.print("Calculated Kp: "); Serial.print(calculatedKp); Serial.println();
    Serial.print("Calculated Ki: "); Serial.print(calculatedKi); Serial.println();
  }
}

void checkSerialCommand() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      serialCommand.trim();
      if (serialCommand.equalsIgnoreCase("AUTOTUNE") && !autotuneRunning) {
        systemRunning = true;  // Ensure system runs
        autotuneRunning = true;
        autotuneDone = false;
        autotuneStartTime = millis();
        delayTime = 0;
        riseTime = 0;
        peakTime = 0;
        settleTime = 0;
        peakTemp = 0.0;
        cycleCount = 0;
        integralError = 0.0;
        overshoot = 0.0;
        Serial.println("Autotune Started via serial");
      } else if (serialCommand.equalsIgnoreCase("PI")) {
        systemRunning = true;  // Start or resume system
        autotuneRunning = false;  // Switch to PI control
        Serial.println("Switched to PI control via serial");
      } else if (serialCommand.startsWith("S")) {
        String setpointStr = serialCommand.substring(1);
        tempSetpoint = setpointStr.toFloat();
        EEPROM.put(ADDR_SETPOINT, tempSetpoint);  // Save to EEPROM
        Serial.print("Setpoint changed to ");
        Serial.print(tempSetpoint);
        Serial.println(" via serial");
      } else if (serialCommand.equalsIgnoreCase("STOP") || serialCommand.equalsIgnoreCase("H0")) {
        systemRunning = false;  // Stop the system
        autotuneRunning = false;  // Stop autotune if running
        heaterDutyCycle = 0;  // Immediately turn off heater
        digitalWrite(HEATER_PIN, LOW);
        Serial.println("System stopped via serial");
      }
      serialCommand = "";
    } else {
      serialCommand += c;
    }
  }
}

void loop() {
  // Check for serial commands
  checkSerialCommand();
  
  sensors.requestTemperatures();
  float temperature = sensors.getTempCByIndex(0);
  
  if (temperature != DEVICE_DISCONNECTED_C) {
    if (systemRunning) {
      if (autotuneRunning) {
        autotune(temperature);
      } else {
        // Normal PI control - using calculated values if available
        float kp = (autotuneDone && calculatedKp > 0) ? calculatedKp : KP;
        float ki = (autotuneDone && calculatedKi > 0) ? calculatedKi : KI;
        
        float error = tempSetpoint - temperature;
        float pTerm = kp * error;
        float iTerm = ki * integralError;
        
        if (error >= 4) {
          integralError = 0;
        } else {
          integralError += error * SAMPLE_TIME;
          iTerm = ki * integralError;
        }
        
        float controlOutput = pTerm + iTerm;
        heaterDutyCycle = constrain(controlOutput, 0, 100);
      }
    } else {
      heaterDutyCycle = 0;
      digitalWrite(HEATER_PIN, LOW);  // Ensure heater is off when system is stopped
    }
    
    // Serial output with setpoint included
    Serial.print("Setpoint: "); Serial.print(tempSetpoint);
    Serial.print(", Temp: "); Serial.print(temperature);
    Serial.print(" C, Duty: "); Serial.print(heaterDutyCycle);
    Serial.print("%, Mode: "); Serial.print(systemRunning ? (autotuneRunning ? "AUTOTUNE" : "PI") : "STOPPED");
    if (autotuneDone) {
      Serial.print(", DT: "); Serial.print(delayTime);
      Serial.print(", RT: "); Serial.print(riseTime);
      Serial.print(", PT: "); Serial.print(peakTime);
      Serial.print(", ST: "); Serial.print(settleTime);
      Serial.print(", Kp: "); Serial.print(calculatedKp);
      Serial.print(", Ki: "); Serial.print(calculatedKi);
    }
    Serial.println();
  } else {
    Serial.println("Error: Could not read temperature data");
    heaterDutyCycle = 0;
    digitalWrite(HEATER_PIN, LOW);
    integralError = 0.0;
    autotuneRunning = false;
  }
  
  delay(100);
}