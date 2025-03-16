# Arduino Temperature Control System

This repository contains a complete temperature control system using an Arduino microcontroller and a Python-based graphical user interface (GUI). The project is split into two branches:

- **[Arduino-Code](#arduino-code-branch)**: Contains the Arduino firmware for temperature sensing, heater control, and PI/autotuning functionality.
- **[Python-GUI](#python-gui-branch)**: Contains the Python script for real-time monitoring, control, and safety features via a GUI.

The system integrates a DS18B20 temperature sensor and a heater, controlled via PWM, with serial communication between the Arduino and a Python GUI. It supports PI control, Ziegler-Nichols autotuning, and includes safety features like temperature warnings and an emergency stop.

![System Overview](system_overview.png)
*Diagram illustrating the Arduino and Python GUI integration (to be added).*

## Project Structure
This repository uses branches to organize the codebase:
- **`main`**: This README and general project information.
- **`Arduino-Code`**: Arduino `.ino` file and related documentation.
- **`Python-GUI`**: Python script and related documentation.

## Getting Started
1. **Choose a Branch**:
   - For the Arduino firmware, switch to the [`Arduino-Code` branch](#arduino-code-branch).
   - For the Python GUI, switch to the [`Python-GUI` branch](#python-gui-branch).
2. **Follow Branch-Specific Instructions**: Each branch has its own README with detailed setup and usage instructions.

## Hardware Requirements
- **Arduino**: Any compatible board (e.g., Uno, Nano).
- **DS18B20 Temperature Sensor**: For temperature measurement.
- **Heater**: Controlled via relay/SSR/transistor.
- **Computer**: For running the Python GUI and programming the Arduino.

## Branches

### Arduino-Code Branch
Contains the Arduino firmware for:
- Temperature sensing with DS18B20.
- PWM heater control.
- PI control and Ziegler-Nichols autotuning.
- Serial communication with the Python GUI.

[**Go to Arduino-Code Branch**](
https://github.com/Gautham-Dev007/PID-AutoTuning/tree/Arduino-Code)

### Python-GUI Branch
Contains the Python script for:
- Real-time plotting of temperature, duty cycle, and mode.
- Serial control of the Arduino (setpoint, mode switching, E-Stop).
- Safety alerts and data logging to Excel.

[**Go to Python-GUI Branch**](
https://github.com/Gautham-Dev007/PID-AutoTuning/tree/Python-GUI)

## How to Contribute
- Fork the repository.
- Create a new branch for your feature or bug fix.
- Submit a pull request to the appropriate branch (`Arduino-Code` or `Python-GUI`).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Arduino and Python communities for their extensive libraries and tools.
- Ziegler-Nichols method for PID tuning inspiration.
