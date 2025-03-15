```markdown
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
   ```
2. Open the `.ino` file in the Arduino IDE.
3. Connect your Arduino board to your computer via USB.
4. Select your board and port under `Tools` in the Arduino IDE.
5. Upload the code to your Arduino.

## Usage
1. **Initial Setup**: Wire the hardware as described above.
2. **Power On**: Connect the Arduino to power and open the Serial Monitor (9600 baud).
3. **Monitor Output**: The system will display the current setpoint, temperature, duty cycle, and mode.
4. **Commands**:
   - Type `AUTOTUNE` to start the autotuning process.
   - Type `PI` to switch to PI control using either default or autotuned parameters.
   - Type `Sxx.x` (e.g., `S80.0`) to change the setpoint.
   - Type `STOP` or `H0` to stop the system.
5. **Autotune Results**: After autotuning completes, the system saves the calculated `Kp` and `Ki` values to EEPROM and uses them in PI mode.

### Example Serial Output
```
Setpoint: 75.00, Temp: 25.50 C, Duty: 100%, Mode: AUTOTUNE
Setpoint: 75.00, Temp: 76.20 C, Duty: 0%, Mode: PI, DT: 5000, RT: 8000, PT: 9000, ST: 15000, Kp: 12.50, Ki: 1.80
```

## Notes
- **Default Setpoint**: 75.0°C (configurable via serial or stored in EEPROM).
- **Safety**: Ensure proper heat sinking and safety mechanisms for the heater to prevent overheating.
- **Tuning**: Autotuning requires the system to oscillate, so monitor it closely during this phase.

## Contributing
Feel free to submit issues or pull requests if you have suggestions or improvements!

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


```

### Customization Tips
1. **Repository Name**: Replace `yourusername/your-repo-name` with your actual GitHub username and repository name.
2. **License**: If you want a different license (e.g., GPL, Apache), update the `License` section and add a `LICENSE` file to your repository.
3. **Additional Sections**: Add sections like "Troubleshooting" or "Future Improvements" if needed.
4. **Images**: You could add a wiring diagram or photo of your setup by including a line like `![Wiring Diagram](wiring_diagram.png)` and uploading the image to your repo.

Let me know if you'd like help refining this further!
