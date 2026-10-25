# --- Imports ---
import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, TextBox, RadioButtons
import pandas as pd
from datetime import datetime
import time
import tkinter as tk
from tkinter import messagebox
import winsound  # For audible alerts (Windows)
import os
import openpyxl
import matplotlib.patches as patches  # Added for E-Stop indicator

# --- Constants ---
BAUD_RATE = 9600
DEFAULT_COM_PORT = 'COM7'
DEFAULT_SETPOINT = 75
MAX_SETPOINT = 85
HIGH_SETPOINT_THRESHOLD = 80
TEMP_WARNING_THRESHOLD = 100
TEMP_CRITICAL_THRESHOLD = 115
WARNING_TIMEOUT = 5  # Seconds for warning timer
HIDE_TEST_FEATURES = True  # Set to True to hide all test-related elements

# --- Global Variables ---
ser = None
connected = False
start_time = None
timestamps = []
temperatures = []
duty_cycles = []
modes = []
data_df = pd.DataFrame({
    'Timestamp': pd.Series(dtype='float64'),
    'Setpoint': pd.Series(dtype='float64'),
    'Temperature': pd.Series(dtype='float64'),
    'Duty_Cycle': pd.Series(dtype='float64'),
    'Mode': pd.Series(dtype='int32')
})
heater_on = True
test_mode = False
test_temperature = None
warning_active = False
estop_engaged = False  # Tracks E-Stop state

# --- Helper Functions ---
def format_time(seconds):
    """Convert seconds to mm:ss format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def parse_serial_line(line):
    """Parse a line of serial data into setpoint, temperature, duty cycle, and mode."""
    try:
        setpoint = float(line.split("Setpoint: ")[1].split(",")[0])
        temp = float(line.split("Temp: ")[1].split(" C")[0])
        duty = float(line.split("Duty: ")[1].split("%")[0])
        mode_str = line.split("Mode: ")[1].split(",")[0]
        mode = 1 if mode_str == "AUTOTUNE" else 0
        return setpoint, temp, duty, mode
    except:
        return None, None, None, None

def turn_off_heater():
    """Turn off the heater if connected and not in test mode."""
    global heater_on, estop_engaged
    if connected and ser and heater_on and not test_mode:
        ser.write(b'H0\n')
        print("Heater stop command sent")
    else:
        print("Heater turned off (Simulated in test mode or not connected)")
    heater_on = False
    estop_engaged = True
    update_estop_indicator()

def append_data(time_diff, setpoint, temperature, duty_cycle, mode):
    """Append data to DataFrame and save to Excel every 10 readings."""
    new_data = pd.DataFrame({
        'Timestamp': [time_diff],
        'Setpoint': [setpoint],
        'Temperature': [temperature],
        'Duty_Cycle': [duty_cycle],
        'Mode': [mode]
    })
    global data_df
    data_df = pd.concat([data_df, new_data], ignore_index=True)
    if len(data_df) % 10 == 0:
        data_df.to_excel('temperature_data.xlsx', index=False)

# --- Warning Dialogs with Timer and Safety ---
def show_setpoint_warning():
    """Show a warning if setpoint exceeds maximum limit."""
    winsound.Beep(1000, 500)
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning("Setpoint Limit Exceeded", f"Setpoint cannot be set to {MAX_SETPOINT}°C or higher (Sensor limit: 125°C).")
    root.destroy()

def show_high_setpoint_confirmation(setpoint):
    """Ask for confirmation if setpoint exceeds high threshold."""
    winsound.Beep(1200, 300)
    root = tk.Tk()
    root.withdraw()
    result = messagebox.askyesno("High Setpoint Confirmation", f"Setpoint {setpoint}°C exceeds {HIGH_SETPOINT_THRESHOLD}°C. Confirm?")
    root.destroy()
    return result

def show_temp_warning_100(temp):
    """Display a warning dialog for temperatures exceeding 100°C."""
    global warning_active
    if warning_active:
        return
    warning_active = True
    winsound.Beep(1500, 1000)
    root = tk.Tk()
    root.title("Temperature Warning")
    root.geometry("400x300")
    root.configure(bg="yellow")

    tk.Label(root, text=f"WARNING: Temperature {temp:.2f}°C exceeds 100°C!", fg="red", bg="yellow", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(root, text="Risk: Potential sensor damage.", font=("Arial", 10), bg="yellow").pack(pady=5)
    timer_label = tk.Label(root, text=f"Auto shutdown in {WARNING_TIMEOUT} seconds", font=("Arial", 10), bg="yellow")
    timer_label.pack(pady=5)

    def update_timer(remaining):
        if remaining > 0 and root.winfo_exists():
            timer_label.config(text=f"Auto shutdown in {remaining} seconds")
            root.after(1000, update_timer, remaining - 1)
        elif root.winfo_exists():
            turn_off_heater()
            root.destroy()
            global warning_active
            warning_active = False

    warning_label = tk.Label(root, text="High Temperature Alert", fg="red", bg="yellow", font=("Arial", 14))
    warning_label.pack(pady=10)
    flash_id = None
    def flash():
        nonlocal flash_id
        if root.winfo_exists():
            current_color = warning_label.cget("fg")
            warning_label.config(fg="white" if current_color == "red" else "red")
            flash_id = root.after(500, flash)
        else:
            if flash_id:
                root.after_cancel(flash_id)

    flash()
    tk.Button(root, text="Override", command=lambda: [root.destroy(), set_warning_active(False)]).pack(side=tk.LEFT, padx=20, pady=20)
    tk.Button(root, text="Power Off Heater", command=lambda: [turn_off_heater(), root.destroy(), set_warning_active(False)]).pack(side=tk.RIGHT, padx=20, pady=20)

    root.after(1000, update_timer, WARNING_TIMEOUT - 1)
    root.protocol("WM_DELETE_WINDOW", lambda: [root.destroy(), set_warning_active(False)])
    root.mainloop()

def show_temp_critical_warning(temp):
    """Display a critical warning for temperatures exceeding 115°C."""
    global warning_active
    if warning_active:
        return
    warning_active = True
    winsound.Beep(2500, 2000)
    turn_off_heater()
    root = tk.Tk()
    root.title("CRITICAL TEMPERATURE ALERT")
    root.geometry("500x300")
    root.configure(bg="red")

    tk.Label(root, text="!!! CRITICAL !!!", fg="white", bg="red", font=("Arial", 24, "bold")).pack(pady=10)
    tk.Label(root, text=f"Temperature {temp:.2f}°C exceeds {TEMP_CRITICAL_THRESHOLD}°C!", fg="white", bg="red", font=("Arial", 16)).pack(pady=5)
    tk.Label(root, text="Heater has been automatically disabled.", fg="white", bg="red", font=("Arial", 14)).pack(pady=5)
    tk.Label(root, text="Please check the system immediately.", fg="white", bg="red", font=("Arial", 14)).pack(pady=5)

    flash_label = tk.Label(root, text="ACTION REQUIRED", fg="yellow", bg="red", font=("Arial", 18, "bold"))
    flash_label.pack(pady=10)
    flash_id = None
    def flash():
        nonlocal flash_id
        if root.winfo_exists():
            current_color = flash_label.cget("fg")
            flash_label.config(fg="red" if current_color == "yellow" else "yellow")
            flash_id = root.after(500, flash)
        else:
            if flash_id:
                root.after_cancel(flash_id)

    flash()
    tk.Button(root, text="OK", command=lambda: [root.destroy(), set_warning_active(False)], font=("Arial", 14)).pack(pady=20)
    root.protocol("WM_DELETE_WINDOW", lambda: [root.destroy(), set_warning_active(False)])
    root.mainloop()

def show_estop_warning():
    """Display a warning dialog for emergency stop activation."""
    global warning_active
    if warning_active:
        return
    warning_active = True
    winsound.Beep(2000, 1000)
    root = tk.Tk()
    root.title("EMERGENCY STOP ACTIVATED")
    root.geometry("400x250")
    root.configure(bg="red")

    tk.Label(root, text="!!! EMERGENCY STOP !!!", fg="white", bg="red", font=("Arial", 20, "bold")).pack(pady=10)
    tk.Label(root, text="Heater has been manually disabled.", fg="white", bg="red", font=("Arial", 14)).pack(pady=5)
    tk.Label(root, text="Please verify system safety.", fg="white", bg="red", font=("Arial", 14)).pack(pady=5)

    flash_label = tk.Label(root, text="SYSTEM HALTED", fg="yellow", bg="red", font=("Arial", 16, "bold"))
    flash_label.pack(pady=10)
    flash_id = None
    def flash():
        nonlocal flash_id
        if root.winfo_exists():
            current_color = flash_label.cget("fg")
            flash_label.config(fg="red" if current_color == "yellow" else "yellow")
            flash_id = root.after(500, flash)
        else:
            if flash_id:
                root.after_cancel(flash_id)

    flash()
    tk.Button(root, text="OK", command=lambda: [root.destroy(), set_warning_active(False)], font=("Arial", 14)).pack(pady=20)
    root.protocol("WM_DELETE_WINDOW", lambda: [root.destroy(), set_warning_active(False)])
    root.mainloop()

def set_warning_active(value):
    """Helper to set the warning_active flag."""
    global warning_active
    warning_active = value

# --- Plot Setup ---
plt.style.use('seaborn-v0_8')
fig = plt.figure(figsize=(14, 6))

ax1 = fig.add_axes([0.1, 0.2, 0.75, 0.6])
ax2 = ax1.twinx()
ax3 = ax1.twinx()
ax3.spines["right"].set_position(("axes", 1.2))

line_temp, = ax1.plot([], [], 'b-', label='Temperature (°C)')
ax1.set_title('Setpoint: -- °C | Temp: -- °C | Duty: --% | Mode: --', fontsize=12)
ax1.set_xlabel('Time (mm:ss)', fontsize=10)
ax1.set_ylabel('Temperature (°C)', color='b', fontsize=10)
ax1.set_ylim(0, 130)
ax1.tick_params(axis='y', labelcolor='b')
ax1.grid(True, linestyle='--', alpha=0.7)
setpoint_line = ax1.axhline(y=DEFAULT_SETPOINT, color='g', linestyle='--', label=f'Setpoint ({DEFAULT_SETPOINT}°C)')

line_duty, = ax2.plot([], [], 'r-', label='Duty Cycle (%)')
ax2.set_ylim(-5, 105)
ax2.tick_params(axis='y', labelcolor='r')
ax2.set_ylabel('Duty Cycle (%)', color='r', fontsize=10)

line_mode, = ax3.plot([], [], 'm--', label='Mode (0=PI, 1=Autotune)', alpha=0.5)
ax3.set_ylim(-0.5, 1.35)
ax3.set_yticks([])

lines = [line_temp, line_duty, line_mode, setpoint_line]
ax1.legend(lines, [l.get_label() for l in lines], loc='upper right', bbox_to_anchor=(1.15, 1.15), fontsize=9)

# --- Widget Setup ---
ax_comport = plt.axes([0.1, 0.9, 0.15, 0.05])
textbox_comport = TextBox(ax_comport, 'COM Port: ', initial=DEFAULT_COM_PORT)

ax_connect = plt.axes([0.26, 0.9, 0.1, 0.05])
button_connect = Button(ax_connect, 'Connect', color='lightgreen')

ax_button_autotune = plt.axes([0.6, 0.05, 0.1, 0.05])
button_autotune = Button(ax_button_autotune, 'Autotune', color='lightblue')

ax_button_pi = plt.axes([0.71, 0.05, 0.1, 0.05])
button_pi = Button(ax_button_pi, 'PI', color='lightblue')

ax_textbox_setpoint = plt.axes([0.1, 0.05, 0.15, 0.05])
textbox_setpoint = TextBox(ax_textbox_setpoint, 'Setpoint: ', initial=str(DEFAULT_SETPOINT))

ax_button_reset = plt.axes([0.26, 0.05, 0.1, 0.05])
button_reset = Button(ax_button_reset, 'Reset Plot', color='salmon')

ax_button_estop = plt.axes([0.37, 0.05, 0.1, 0.05])
button_estop = Button(ax_button_estop, 'E-Stop', color='red')

# Improved E-Stop Indicator
ax_estop_indicator = plt.axes([0.55, 0.90, 0.08, 0.06])
estop_patch = patches.Rectangle((0, 0), 1, 1, transform=ax_estop_indicator.transAxes, color='green', alpha=0.8)
ax_estop_indicator.add_patch(estop_patch)
estop_text = plt.Text(0.5, 0.5, 'ON', transform=ax_estop_indicator.transAxes, ha='center', va='center', fontsize=12, color='white', weight='bold')
ax_estop_indicator.add_artist(estop_text)
ax_estop_indicator.set_axis_off()

if not HIDE_TEST_FEATURES:
    ax_button_test_mode = plt.axes([0.85, 0.9, 0.1, 0.05])
    button_test_mode = Button(ax_button_test_mode, 'Test Mode: OFF', color='lightgray')

    ax_test_dropdown = plt.axes([0.4, 0.85, 0.15, 0.15])
    test_options = ['None', 'Setpoint 85', 'Temp 105', 'Temp 120']
    test_dropdown = RadioButtons(ax_test_dropdown, test_options, active=0)
    ax_test_dropdown.set_visible(False)

# --- Callback Functions ---
def update_estop_indicator():
    """Update the E-Stop indicator based on its state."""
    if estop_engaged:
        estop_patch.set_color('red')
        estop_text.set_text('OFF')
    else:
        estop_patch.set_color('green')
        estop_text.set_text('ON')
    fig.canvas.draw_idle()

def on_connect_clicked(event):
    """Handle connect/disconnect button clicks."""
    global ser, connected, start_time
    if connected:
        ser.close()
        connected = False
        button_connect.label.set_text('Connect')
        print("Disconnected")
    else:
        comport = textbox_comport.text
        try:
            ser = serial.Serial(comport, BAUD_RATE, timeout=0.1)
            time.sleep(2)
            connected = True
            start_time = datetime.now()
            button_connect.label.set_text('Disconnect')
            print(f"Connected to {comport}")
        except Exception as e:
            print(f"Failed to connect: {e}")

def on_autotune_clicked(event):
    """Send AUTOTUNE command to the device."""
    if connected and ser and not test_mode:
        ser.write(b'AUTOTUNE\n')
        print("Sent AUTOTUNE command")
    else:
        print("Not connected or in test mode")

def on_pi_clicked(event):
    """Send PI command to the device."""
    if connected and ser and not test_mode:
        ser.write(b'PI\n')
        print("Sent PI command")
    else:
        print("Not connected or in test mode")

def on_setpoint_submit(text):
    """Handle setpoint submission with safety checks."""
    global estop_engaged
    try:
        setpoint = float(text)
        if setpoint >= MAX_SETPOINT:
            show_setpoint_warning()
            textbox_setpoint.set_val(str(DEFAULT_SETPOINT))
        elif setpoint > HIGH_SETPOINT_THRESHOLD:
            if show_high_setpoint_confirmation(setpoint):
                apply_setpoint(setpoint)
                estop_engaged = False
                update_estop_indicator()
            else:
                textbox_setpoint.set_val(str(DEFAULT_SETPOINT))
        else:
            apply_setpoint(setpoint)
            estop_engaged = False
            update_estop_indicator()
    except ValueError:
        print("Invalid setpoint: Enter a number")
        textbox_setpoint.set_val(str(DEFAULT_SETPOINT))

def apply_setpoint(setpoint):
    """Apply the setpoint to the device and update the plot."""
    if connected and ser and not test_mode:
        ser.write(f'S{setpoint}\n'.encode())
        print(f"Sent setpoint: S{setpoint}")
    setpoint_line.set_ydata([setpoint, setpoint])
    setpoint_line.set_label(f'Setpoint ({setpoint}°C)')
    ax1.legend(lines, [l.get_label() for l in lines], loc='upper right', bbox_to_anchor=(1.15, 1.15))
    fig.canvas.draw_idle()
    if test_mode:
        print(f"Test mode: Setpoint set to {setpoint}")

def on_reset_clicked(event):
    """Reset the plot and data."""
    global timestamps, temperatures, duty_cycles, modes, start_time, heater_on, estop_engaged
    timestamps, temperatures, duty_cycles, modes = [], [], [], []
    start_time = datetime.now()
    heater_on = True
    estop_engaged = False
    update_estop_indicator()
    line_temp.set_data([], [])
    line_duty.set_data([], [])
    line_mode.set_data([], [])
    ax1.set_title('Setpoint: -- °C | Temp: -- °C | Duty: --% | Mode: --')
    fig.canvas.draw_idle()

def on_estop_clicked(event):
    """Handle emergency stop button click."""
    turn_off_heater()
    show_estop_warning()
    print("Emergency stop activated")

if not HIDE_TEST_FEATURES:
    def on_test_mode_clicked(event):
        """Toggle test mode and update UI accordingly."""
        global test_mode, connected, ser, test_temperature, start_time
        test_mode = not test_mode
        if test_mode:
            if connected and ser:
                ser.close()
                connected = False
                button_connect.label.set_text('Connect')
            button_test_mode.label.set_text('Test Mode: ON')
            ax_test_dropdown.set_visible(True)
            test_temperature = None
            timestamps.clear()
            temperatures.clear()
            duty_cycles.clear()
            modes.clear()
            start_time = datetime.now()
            print("Test mode enabled")
        else:
            button_test_mode.label.set_text('Test Mode: OFF')
            ax_test_dropdown.set_visible(False)
            test_temperature = None
            timestamps.clear()
            temperatures.clear()
            duty_cycles.clear()
            modes.clear()
            print("Test mode disabled")
        fig.canvas.draw()

    def on_test_select(label):
        """Handle test mode dropdown selections."""
        global test_temperature, start_time
        if not test_mode:
            print("Enable Test Mode first")
            test_dropdown.set_active(0)
            return
        if label == 'None':
            test_temperature = None
            print("Test mode: No simulation")
        elif label == 'Setpoint 85':
            textbox_setpoint.set_val("85")
            on_setpoint_submit("85")
        elif label == 'Temp 105':
            test_temperature = 105
            print("Test mode: Simulating temperature at 105°C")
        elif label == 'Temp 120':
            test_temperature = 120
            print("Test mode: Simulating temperature at 120°C")
        start_time = datetime.now()

# Connect callbacks
button_connect.on_clicked(on_connect_clicked)
button_autotune.on_clicked(on_autotune_clicked)
button_pi.on_clicked(on_pi_clicked)
textbox_setpoint.on_submit(on_setpoint_submit)
button_reset.on_clicked(on_reset_clicked)
button_estop.on_clicked(on_estop_clicked)
if not HIDE_TEST_FEATURES:
    button_test_mode.on_clicked(on_test_mode_clicked)
    test_dropdown.on_clicked(on_test_select)

# --- Animation Update Function ---
last_warning_100 = False
last_warning_115 = False

def update(frame):
    """Update the plot and handle safety checks."""
    global last_warning_100, last_warning_115, start_time
    setpoint = float(textbox_setpoint.text) if textbox_setpoint.text.isdigit() else DEFAULT_SETPOINT

    if test_mode and not HIDE_TEST_FEATURES:
        if test_temperature is not None:
            if start_time is None:
                start_time = datetime.now()
            time_diff = (datetime.now() - start_time).total_seconds()
            temperature = test_temperature
            duty_cycle = 50
            mode = 0
            timestamps.append(time_diff)
            temperatures.append(temperature)
            duty_cycles.append(duty_cycle)
            modes.append(mode)

            append_data(time_diff, setpoint, temperature, duty_cycle, mode)

            if temperature > TEMP_CRITICAL_THRESHOLD and not last_warning_115:
                show_temp_critical_warning(temperature)
                last_warning_115 = True
            elif temperature > TEMP_WARNING_THRESHOLD and not last_warning_100 and not last_warning_115:
                plt.gcf().canvas.manager.window.after(100, show_temp_warning_100, temperature)
                last_warning_100 = True
            elif temperature <= TEMP_WARNING_THRESHOLD:
                last_warning_100 = False
            elif temperature <= TEMP_CRITICAL_THRESHOLD:
                last_warning_115 = False

            line_temp.set_data(timestamps, temperatures)
            line_duty.set_data(timestamps, duty_cycles)
            line_mode.set_data(timestamps, modes)
            setpoint_line.set_ydata([setpoint, setpoint])
            update_plot_limits_and_title(setpoint, temperature, duty_cycle, mode)
    elif connected and ser:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                setpoint, temperature, duty_cycle, mode = parse_serial_line(line)
                if temperature is not None:
                    time_diff = (datetime.now() - start_time).total_seconds()
                    timestamps.append(time_diff)
                    temperatures.append(temperature)
                    duty_cycles.append(duty_cycle)
                    modes.append(mode)

                    append_data(time_diff, setpoint, temperature, duty_cycle, mode)

                    if temperature > TEMP_CRITICAL_THRESHOLD and not last_warning_115:
                        show_temp_critical_warning(temperature)
                        last_warning_115 = True
                    elif temperature > TEMP_WARNING_THRESHOLD and not last_warning_100 and not last_warning_115:
                        plt.gcf().canvas.manager.window.after(100, show_temp_warning_100, temperature)
                        last_warning_100 = True
                    elif temperature <= TEMP_WARNING_THRESHOLD:
                        last_warning_100 = False
                    elif temperature <= TEMP_CRITICAL_THRESHOLD:
                        last_warning_115 = False

                    line_temp.set_data(timestamps, temperatures)
                    line_duty.set_data(timestamps, duty_cycles)
                    line_mode.set_data(timestamps, modes)
                    setpoint_line.set_ydata([setpoint, setpoint])
                    update_plot_limits_and_title(setpoint, temperature, duty_cycle, mode)
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        except Exception as e:
            print(f"Error: {e}")
    fig.canvas.draw_idle()
    return line_temp, line_duty, line_mode

def update_plot_limits_and_title(setpoint, temperature, duty_cycle, mode):
    """Update plot limits, title, and legend."""
    if timestamps:
        xmin, xmax = min(timestamps), max(timestamps) if len(timestamps) > 1 else min(timestamps) + 1
        ax1.set_xlim(xmin, xmax)
        num_ticks = 10
        if xmax > xmin:
            step = (xmax - xmin) / (num_ticks - 1)
            tick_locs = [xmin + i * step for i in range(num_ticks)]
        else:
            tick_locs = [xmin]
        ax1.set_xticks(tick_locs)
        ax1.set_xticklabels([format_time(t) for t in tick_locs])
    ax1.set_title(
        f'Setpoint: {setpoint:.1f} °C | Temp: {temperature:.2f} °C | Duty: {duty_cycle:.1f}% | Mode: {"AUTOTUNE" if mode == 1 else "PI"}',
        fontsize=12
    )
    ax1.legend(lines, [l.get_label() for l in lines], loc='upper right', bbox_to_anchor=(1.15, 1.15))

# --- Animation ---
ani = FuncAnimation(fig, update, interval=100, blit=False, cache_frame_data=False)

# --- Show Plot ---
update_estop_indicator()  # Initial update of E-Stop indicator
plt.show()

# --- Cleanup ---
if ser and ser.is_open:
    ser.close()
data_df.to_excel('temperature_data.xlsx', index=False)
print("Program ended, data saved.")