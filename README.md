# Arduino Temperature Control System

This project implements a temperature control system using an Arduino microcontroller with a Dallas DS18B20 temperature sensor and a heater controlled via PWM. It supports both manual PI (Proportional-Integral) control and an automated Ziegler-Nichols autotuning process to optimize control parameters. The system saves tuning data and setpoint values to EEPROM for persistence across power cycles.

## Features
- **Temperature Sensing**: Uses a DS18B20 sensor via the OneWire protocol.
- **Heater Control**: PWM-based heater control using Timer1 for precise duty cycle adjustments.
- **PI Control**: Implements Proportional-Integral control with configurable or autotuned gains.
- **Autotuning**: Automatically tunes PI parameters using the Ziegler-Nichols method based on system response.
- **EEPROM Storage**: Saves autotune results and setpoint for persistence.
- **Serial Interface**: Allows real-time monitoring and control via serial commands:
  - `AUTOTUNE`: Starts the autotuning process.
  - `PI`: Switches to PI control mode.
  - `Sxx.x`: Sets a new temperature setpoint (e.g., `S75.5`).
  - `STOP` or `H0`: Stops the system and turns off the heater.
- **Real-Time Monitoring**: Outputs temperature, setpoint, duty cycle, and mode to the Serial Monitor.

## Hardware Requirements
- **Arduino Board**: Any Arduino compatible board (e.g., Uno, Nano, Mega).
- **DS18B20 Temperature Sensor**: Connected via OneWire protocol (digital pin 9).
- **Heater**: Controlled via a relay, transistor, or SSR (connected to pin 13).
- **Pull-up Resistor**: 4.7kΩ resistor between the DS18B20 data line and 5V.
- **Power Supply**: Suitable for your heater and Arduino.

### Wiring
| Component         | Arduino Pin | Notes                          |
|-------------------|-------------|--------------------------------|
| DS18B20 Data      | 9           | 4.7kΩ pull-up to 5V required  |
| Heater Control    | 13          | Via relay/SSR/transistor       |
| DS18B20 VCC       | 5V          |                                |
| DS18B20 GND       | GND         |                                |

## Software Requirements
- **Arduino IDE**: For compiling and uploading the code.
- **Libraries**:
  - `OneWire` (by Paul Stoffregen)
  - `DallasTemperature` (by Miles Burton)
  - `TimerOne` (by Paul Stoffregen)
  - `EEPROM` (built-in Arduino library)

Install these libraries via the Arduino Library Manager:
1. Open Arduino IDE.
2. Go to `Sketch > Include Library > Manage Libraries`.
3. Search for and install `OneWire`, `DallasTemperature`, and `TimerOne`.

## Installation
1. Clone or download this repository:
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
