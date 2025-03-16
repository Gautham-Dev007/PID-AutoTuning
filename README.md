
# Arduino Temperature Monitoring and Control GUI

![Project Banner](https://github.com/Gautham-Dev007/PID-AutoTuning/blob/GIT_Support/Arduino_Uno(Photos)/arduino_banner.png/800x200.png) <!-- Replace with actual banner image URL -->

This Python script provides a graphical user interface (GUI) for monitoring and controlling an Arduino-based temperature control system. It communicates with the Arduino via a serial connection, plots real-time temperature, duty cycle, and mode data, and includes safety features like temperature warnings and an emergency stop (E-Stop). The script uses Matplotlib for plotting and Tkinter for dialogs, with data logging to an Excel file.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [License](#license)

## Features
- **Real-Time Plotting**: Displays temperature (°C), duty cycle (%), and mode (PI or Autotune) over time.
- **Serial Communication**: Connects to an Arduino via a specified COM port (default: COM7).
- **Control Commands**: Send `AUTOTUNE`, `PI`, `Sxx.x` (setpoint), and `H0` (stop) commands to the Arduino.
- **Safety Features**:
  - Temperature warnings at 100°C and critical shutdown at 115°C.
  - Emergency Stop (E-Stop) button to disable the heater.
  - Setpoint limits (max 85°C) with confirmation for high values (>80°C).
- **Data Logging**: Saves timestamped data (setpoint, temperature, duty cycle, mode) to `temperature_data.xlsx`.
- **Interactive Controls**:
  - Connect/Disconnect button for serial communication.
  - Setpoint input with validation.
  - Autotune and PI mode buttons.
  - Reset plot button.
  - E-Stop indicator showing heater status.
- **Test Mode (optional)**: Simulate temperature data for debugging (hidden by default).

## Requirements
- **Python 3.x**: Install from [python.org](https://www.python.org/).
- **Libraries**:
  - `pyserial`: For serial communication.
  - `matplotlib`: For plotting.
  - `pandas`: For data handling and Excel export.
  - `openpyxl`: For Excel file writing.
  - `tkinter`: Built-in with Python for dialogs.

Install dependencies via pip:
```bash
pip install pyserial matplotlib pandas openpyxl
```

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/arduino-temperature-control-gui.git
   cd arduino-temperature-control-gui
   ```
2. Install the required Python libraries (see [Requirements](#requirements)).
3. Ensure your Arduino is connected and configured to send data in the format: `Setpoint: X, Temp: Y C, Duty: Z%, Mode: W`.

## Usage
1. Run the script:
   ```bash
   python temperature_monitor.py
   ```
2. Enter the COM port (e.g., `COM7`) and click "Connect".
3. Set a setpoint (e.g., `75`) and press Enter.
4. Use "Autotune" or "PI" buttons to switch modes, "Reset Plot" to clear data, or "E-Stop" to halt the heater.
5. Monitor the live plot and respond to safety alerts as needed.

**Test Mode** (optional):
- Edit the script to set `HIDE_TEST_FEATURES = False`.
- Enable "Test Mode" to simulate temperature scenarios (e.g., 105°C).

## Screenshots
1. **Main GUI Interface**  
   ![Main Interface](https://via.placeholder.com/600x400.png) <!-- Replace with actual URL -->  
   Real-time plots of temperature, duty cycle, and mode with interactive controls.

2. **Setpoint Confirmation Dialog**  
   ![Setpoint Confirmation](https://via.placeholder.com/300x200.png) <!-- Replace with actual URL -->  
   Confirmation prompt for setpoints exceeding 80°C.

3. **100°C Temperature Warning**  
   ![100°C Warning](https://via.placeholder.com/400x300.png) <!-- Replace with actual URL -->  
   Yellow warning dialog with a 5-second shutdown timer.

4. **115°C Critical Alert**  
   ![115°C Critical](https://via.placeholder.com/500x300.png) <!-- Replace with actual URL -->  
   Red critical alert with automatic heater shutdown.

5. **E-Stop Activation**  
   ![E-Stop Warning](https://via.placeholder.com/400x250.png) <!-- Replace with actual URL -->  
   Emergency stop dialog indicating heater disablement.

6. **E-Stop Indicator**  
   ![E-Stop Indicator](https://via.placeholder.com/200x100.png) <!-- Replace with actual URL -->  
   Close-up of the green/red E-Stop status indicator.

7. **Test Mode Interface**  
   ![Test Mode](https://via.placeholder.com/600x400.png) <!-- Replace with actual URL -->  
   GUI with test mode enabled, showing simulation options.

8. **Excel Data Output**  
   ![Excel Data](https://via.placeholder.com/500x300.png) <!-- Replace with actual URL -->  
   Sample of logged data in `temperature_data.xlsx`.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```

### Additional Image Placeholders
I've added the following new image placeholders to enrich your README:
- **Setpoint Confirmation Dialog**: Shows the high setpoint (>80°C) confirmation prompt.
- **E-Stop Indicator**: Highlights the green/red status indicator separately.
- **Test Mode Interface**: Displays the GUI with test mode activated and options visible.
- **Excel Data Output**: Provides a visual of the logged data in Excel.

### How to Use This Markdown File
1. **Save as `README.md`**: Copy this content into a file named `README.md` in your project directory.
2. **Replace Image URLs**: Capture the screenshots listed above, upload them to your GitHub repository (e.g., in a `screenshots/` folder) or an external host (e.g., Imgur), and update the placeholder URLs:
   - GitHub example: `https://raw.githubusercontent.com/yourusername/arduino-temperature-control-gui/main/screenshots/main_interface.png`
   - External example: Use the direct image link from your hosting service.
3. **Update Repository URL**: Replace `https://github.com/yourusername/arduino-temperature-control-gui.git` with your actual repository URL.
4. **Add a License File**: If using the MIT License, create a `LICENSE` file with the MIT License text.

This version provides a concise yet comprehensive overview with ample visual documentation opportunities. Let me know if you'd like further adjustments!
