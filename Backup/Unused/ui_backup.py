import os
import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
import can
from ttkthemes import ThemedStyle
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import JointState
from geometry_msgs.msg import TransformStamped
from PIL import Image, ImageTk
import sv_ttk
import math
import serial
import time
import threading

def read_serial_responses(ser):
   """
   Continuously read and display serial responses
   """
   while True:
       try:
           # Check if data is available
           if ser.in_waiting > 0:
               response = ser.readline().decode('utf-8', errors='ignore').strip()
               if response:
                   update_message(f"GRBL Response: {response}")
       except Exception as e:
           update_message(f"Serial read error: {e}")
           break

# Change this according to your folder 
user_path = "/home/michael/arctosgui"

root = tk.Tk()
root.title("Arctos CAN controller")

# Global variables

is_relative_mode = False
joint_offsets = [0.0] * 6  # Offsets for X, Y, Z, A, B, C
cartesian_offsets = [0.0] * 3  # Offsets for X, Y, Z
tool_frame_visible = True
visual_frame_visible = True
selected_port = None
connected = False
bus = None
last_modified = None
last_joint_states = None
last_cartesian_position = None
is_closed_loop = True  # New variable for loop mode

# Initialize all required lists and dictionaries at the start
joint_state_sliders = []
joint_state_entries = []
joint_state_values = []
cartesian_path_sliders = []
cartesian_path_values = []
joint_name_to_slider = {}

class CanvasButton:
    def __init__(self, canvas, x, y, width, height, image_path, name, command):
        x, y = canvas.canvasx(x), canvas.canvasy(y)
        self.name = name
        self.canvas = canvas
        self.command = command
        self.btn_image = Image.open(image_path)
        self.btn_image = self.btn_image.resize((width, height), Image.LANCZOS)
        self.btn_image = ImageTk.PhotoImage(self.btn_image)
        self.button = canvas.create_image(x, y, anchor='nw', image=self.btn_image, tags=self.name)


def toggle_tool_frame():
    global tool_frame_visible
    tool_frame_visible = not tool_frame_visible
    if tool_frame_visible:
        tool_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        tool_hide_btn.configure(text="Hide Tool Jog")
    else:
        tool_frame.grid_remove()
        tool_hide_btn.configure(text="Show Tool Jog")

def toggle_visual_frame():
    global visual_frame_visible
    visual_frame_visible = not visual_frame_visible
    if visual_frame_visible:
        canvas_frame.grid(row=0, column=2, padx=10, pady=5, sticky="nsew")
        visual_hide_btn.configure(text="Hide Visual Control")
    else:
        canvas_frame.grid_remove()
        visual_hide_btn.configure(text="Show Visual Control")




def btn_clicked(button_name):
    increment = {'X+': 0.03, 'X-': -0.03, 'Y+': -0.03, 'Y-': 0.03, 'Z+': -0.03, 'Z-': 0.03}
    if button_name in increment:
        dx, dy, dz = 0, 0, 0
        if button_name.startswith('X'): dx = increment[button_name]
        elif button_name.startswith('Y'): dy = increment[button_name]
        elif button_name.startswith('Z'): dz = increment[button_name]
        
        current_x = cartesian_path_sliders[0].get()
        current_y = cartesian_path_sliders[1].get()
        current_z = cartesian_path_sliders[2].get()
        
        cartesian_path_sliders[0].set(current_x + dx)
        cartesian_path_sliders[1].set(current_y + dy)
        cartesian_path_sliders[2].set(current_z + dz)
        
        plan_cartesian_path()

def run_gcode_script():
    os.system("python3 rosjog.py")
    os.system("python3 sendgcode.py")

def console_script():
    os.system("python3 console.py")

##############################################################################
# HINZUFÜGEN: Hilfsfunktionen für Slider und Entry in Tool Jog
##############################################################################

def update_tool_slider_and_entry(index, value):
    """
    Setzt den Slider und den zugehörigen Entry auf den gleichen Wert.
    Rundet auf 2 Nachkommastellen.
    """
    slider = cartesian_path_sliders[index]
    entry = cartesian_path_entries[index]

    # Slider setzen
    slider.set(value)

    # Entry-Feld setzen (gerundet)
    entry.delete(0, tk.END)
    entry.insert(0, f"{value:.2f}")

def on_tool_slider_change(index, event=None):
    """
    Wird aufgerufen, wenn ein Tool-Slider bewegt wird.
    Liest den Sliderwert und aktualisiert Slider & Entry.
    """
    if 0 <= index < len(cartesian_path_sliders):
        value = cartesian_path_sliders[index].get()
        update_tool_slider_and_entry(index, value)
    else:
        print(f"Fehler: Ungültiger Index {index} für cartesian_path_sliders (Länge: {len(cartesian_path_sliders)})")


def on_tool_entry_change(index, event=None):
    """
    Wird aufgerufen, wenn im Entry-Feld (Tool Jog) <Return> gedrückt wird.
    Liest den Entry-Wert und aktualisiert Slider & Entry.
    """
    entry_text = cartesian_path_entries[index].get()
    try:
        float_value = float(entry_text)
        update_tool_slider_and_entry(index, float_value)
    except ValueError:
        # Ungültige Eingabe? Nichts machen
        pass


def update_joint_sliders(data):
    global last_joint_states
    if last_joint_states is None or data.position != last_joint_states.position:
        last_joint_states = data
        for i, joint in enumerate(data.name):
            if joint in joint_name_to_slider:
                slider = joint_name_to_slider[joint]
                if is_relative_mode:
                    relative_position = data.position[i] - joint_offsets[i]
                    slider.set(relative_position)
                    update_joint_entry(i, relative_position * (180 / math.pi))
                else:
                    slider.set(data.position[i])
                    update_joint_entry(i, data.position[i] * (180 / math.pi))


def update_cartesian_sliders(data):
    global last_cartesian_position
    if last_cartesian_position is None or \
       data.transform.translation.x != last_cartesian_position.transform.translation.x or \
       data.transform.translation.y != last_cartesian_position.transform.translation.y or \
       data.transform.translation.z != last_cartesian_position.transform.translation.z:

        last_cartesian_position = data

        if is_relative_mode:
            x_val = data.transform.translation.x - cartesian_offsets[0]
            y_val = data.transform.translation.y - cartesian_offsets[1]
            z_val = data.transform.translation.z - cartesian_offsets[2]
        else:
            x_val = data.transform.translation.x
            y_val = data.transform.translation.y
            z_val = data.transform.translation.z

        # Slider & Entry aktualisieren
        update_tool_slider_and_entry(0, x_val)
        update_tool_slider_and_entry(1, y_val)
        update_tool_slider_and_entry(2, z_val)


def refresh_ports():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    port_combobox['values'] = ports
    port_combobox.current(0)

def connect():
    global selected_port, connected, bus
    port = port_combobox.get()
    if not port:
        update_message("Please select a port.")
        return
    try:
        # Open serial port with specific settings
        ser = serial.Serial(
            port=port, 
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        
        # Optional: Send a soft reset to ensure GRBL is ready
        ser.write(b'\x18')  # Ctrl-X soft reset
        time.sleep(0.5)
        
        # Try to get GRBL version
        ser.write(b'$$\n')
        time.sleep(0.5)
        
        connected = True
        selected_port = port
        update_message(f"Connected to port {port}.")
        
        # Start a background thread to continuously read responses
        response_thread = threading.Thread(target=read_serial_responses, args=(ser,), daemon=True)
        response_thread.start()

    except serial.SerialException as e:
        update_message(f"Error connecting: {str(e)}")


def disconnect():
    global connected, bus
    if connected:
        try:
            bus.shutdown()
            connected = False
            update_message(f"Disconnected from port {selected_port}.")
        except Exception as e:
            update_message(f"Error disconnecting: {str(e)}")
    else:
        update_message("Not connected to any port.")

def send():
    os.system("python3 convert.py")
    os.system("python3 gcode2jog.py")
    os.system("python3 send.py")

def clear_messages():
    messages_text.config(state=tk.NORMAL)
    messages_text.delete('1.0', tk.END)
    messages_text.config(state=tk.DISABLED)

def update_message(message):
    messages_text.config(state=tk.NORMAL)
    messages_text.insert(tk.END, message + "\n")
    messages_text.see(tk.END)
    messages_text.config(state=tk.DISABLED)
    print("Message updated:", message)

# Function to run the ROS script
def run_ros_script():
    os.system("python3 rosjog.py")
    os.system("python3 roscan.py")
    os.system("python3 ros.py")

def update_joint_state_value(index):
    def callback(_):
        try:
            value = float(joint_state_entries[index].get())
            joint_state_sliders[index].set(value * (math.pi / 180))
        except ValueError:
            pass
    return callback



def update_joint_entry(index, value):
    if index < len(joint_state_entries):
        joint_state_entries[index].delete(0, tk.END)
        joint_state_entries[index].insert(0, f"{value:.2f}")

def reset_axis(axis_index, axis_name):
    # Send G92 command
    gcode_command = f"G92 {axis_name}0"
    if not is_closed_loop:
        gcode_entry.delete(0, tk.END)
        gcode_entry.insert(0, gcode_command)
    # Reset slider and entry
    joint_state_sliders[axis_index].set(0)
    update_joint_entry(axis_index, 0)
    update_message(f"Reset {axis_name} axis")



def reset_all_axes() -> None:
    """
    Sends the 'G92 X0 Y0 Z0 A0 B0 C0' G-code command to the device over a serial connection.
    """
    try:
        with serial.Serial(selected_port, 115200, timeout=1) as ser:
            command = "G92 X0 Y0 Z0 A0 B0 C0"
            ser.write((command + '\n').encode())
            print(f"Sent: {command}")

            # Optionally wait for the device to acknowledge the command
            response = ser.readline().decode().strip()
            if response:
                print(f"Received: {response}")

    except serial.SerialException as e:
        print(f"Serial error: {e}")

def toggle_loop_mode():
    global is_closed_loop
    is_closed_loop = not is_closed_loop
    if is_closed_loop:
        closed_loop_frame.pack(fill=tk.X, pady=5)
        gcode_entry.pack_forget()
    else:
        gcode_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        closed_loop_frame.pack_forget()

def go_to_joint_state():
    joint_state_values = [slider.get() for slider in joint_state_sliders]
    if is_relative_mode:
        # Add offsets to convert relative positions to absolute
        joint_state_values = [val + offset for val, offset in zip(joint_state_values, joint_offsets)]
    ui_command_pub.publish("go_to_joint_state," + ','.join(map(str, joint_state_values)))

# Replace the existing plan_cartesian_path function
# Function to update cartesian path with manual input
def plan_cartesian_path():
    x_value = float(x_entry.get()) if x_entry.get() else cartesian_path_sliders[0].get()
    y_value = float(y_entry.get()) if y_entry.get() else cartesian_path_sliders[1].get()
    z_value = float(z_entry.get()) if z_entry.get() else cartesian_path_sliders[2].get()
    ui_command_pub.publish(f"plan_cartesian_path,{x_value},{y_value},{z_value}")

def open_gripper():
    global is_closed_loop
    if is_closed_loop:
        # Closed loop version: write 07FF to gcode.txt
        try:
            with open("gcode.txt", "w") as gcode_file:
                gcode_file.write("07FF")
            update_message("Open gripper command (07FF) written to 'gcode.txt'.")
            os.system("python3 send.py")
        except Exception as e:
            update_message(f"Error writing open gripper command: {e}")
    else:
        # Open loop version: write specific G-code commands
        try:
            with open("gcode.tap", "w") as gcode_file:
                gcode_file.write("""G4 P0
M97 B100 T0.5
G4 P0""")
            update_message("Open gripper G-code commands written to 'gcode.tap'.")
            # Assuming you want to use the serial port for open loop
            try:
                with serial.Serial(selected_port, 115200, timeout=1) as ser:
                    ser.write(b"G4 P0\nM97 B100 T0.5\nG4 P0\n")
                    update_message("Open gripper commands sent via serial.")
            except serial.SerialException as e:
                update_message(f"Serial error for open gripper: {e}")
        except Exception as e:
            update_message(f"Error writing open gripper G-code: {e}")

def close_gripper():
    global is_closed_loop
    if is_closed_loop:
        # Closed loop version: write 0700 to gcode.txt
        try:
            with open("gcode.txt", "w") as gcode_file:
                gcode_file.write("0700")
            update_message("Close gripper command (0700) written to 'gcode.txt'.")
            os.system("python3 send.py")
        except Exception as e:
            update_message(f"Error writing close gripper command: {e}")
    else:
        # Open loop version: write specific G-code commands
        try:
            with open("gcode.tap", "w") as gcode_file:
                gcode_file.write("""G4 P0
M97 B-20 T0.5
G4 P0""")
            update_message("Close gripper G-code commands written to 'gcode.tap'.")
            # Assuming you want to use the serial port for open loop
            try:
                with serial.Serial(selected_port, 115200, timeout=1) as ser:
                    ser.write(b"G4 P0\nM97 B-20 T0.5\nG4 P0\n")
                    update_message("Close gripper commands sent via serial.")
            except serial.SerialException as e:
                update_message(f"Serial error for close gripper: {e}")
        except Exception as e:
            update_message(f"Error writing close gripper G-code: {e}")

def send_data():
    global selected_port
    if not selected_port:
        update_message("No port selected!")
        return

    try:
        # Open serial port with specific settings for GRBL
        ser = serial.Serial(
            port=selected_port, 
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,  # Very short timeout
            write_timeout=1
        )

        # Start a background thread to read responses
        response_thread = threading.Thread(target=read_serial_responses, args=(ser,), daemon=True)
        response_thread.start()

        # Get the command from the entry
        command = gcode_entry.get()
        
        # Ensure command ends with newline
        if not command.endswith('\n'):
            command += '\n'

        # Send the command
        try:
            ser.write(command.encode('utf-8'))
            update_message(f"Sent: {command.strip()}")
            
            # Give some time for response
            time.sleep(0.5)

        except serial.SerialTimeoutException:
            update_message("Write timeout occurred")
        except Exception as e:
            update_message(f"Send error: {e}")

    except serial.SerialException as e:
        update_message(f"Serial connection error: {e}")
    except Exception as e:
        update_message(f"Unexpected error: {e}")


def load_icon(image_path, width):
    try:
        image = Image.open(image_path).convert("RGBA")  # Ensure transparency
        image = image.resize((width, width), Image.LANCZOS)  # Resize while maintaining aspect ratio
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Error loading icon {image_path}: {e}")
        return None

def create_manual_jog_controls(movement_frame):
    # Create a frame for the manual jog controls
    jog_frame = ttk.LabelFrame(movement_frame, text="Manual Jog")
    jog_frame.grid(row=0, column=3, padx=10, pady=5, sticky="nsew")
    
    # Create buttons grid
    buttons_frame = ttk.Frame(jog_frame)
    buttons_frame.pack(pady=5)
    
    # Button configuration
    buttons = [
        ('Y+', 0, 1), ('Z+', 0, 3),
        ('X-', 1, 0), ('X+', 1, 2),
        ('Y-', 2, 1), ('Z-', 2, 3),
        ('A-', 3, 0), ('A+', 3, 1), ('B-', 3, 2), ('B+', 3, 3),
        ('C-', 4, 0), ('C+', 4, 1)
    ]
    
    def send_jog_command(axis, direction):
        try:
            step_size = float(step_size_var.get())
            feed_rate = float(feed_rate_var.get())
            
            # Calculate actual step size based on direction
            actual_step = step_size if direction == '+' else -step_size
            
            # Construct G-code command
            gcode = f"G91 {axis}{actual_step} F{feed_rate}"
            
            # Send the command using the existing serial connection
            try:
                with serial.Serial(selected_port, 115200, timeout=1) as ser:
                    ser.write((gcode + '\n').encode())
                    update_message(f"Sent: {gcode}")
                    
                    # Optional: wait for response
                    response = ser.readline().decode().strip()
                    if response:
                        update_message(f"Received: {response}")
                        
            except serial.SerialException as e:
                update_message(f"Serial error: {e}")
                
        except ValueError as e:
            update_message("Invalid step size or feed rate value")
    
    # Create and place all buttons
    for (label, row, col) in buttons:
        axis = label[0]  # First character is the axis
        direction = label[1]  # Second character is the direction
        btn = ttk.Button(
            buttons_frame, 
            text=label,
            command=lambda a=axis, d=direction: send_jog_command(a, d),
            width=4
        )
        btn.grid(row=row, column=col, padx=2, pady=2)


# Create input fields frame
    inputs_frame = ttk.Frame(jog_frame)
    inputs_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Step size input
    step_size_label = ttk.Label(inputs_frame, text="Step size:")
    step_size_label.pack(side=tk.LEFT, padx=(0, 5))
    
    step_size_var = tk.StringVar(value="1")
    step_size_entry = ttk.Entry(inputs_frame, textvariable=step_size_var, width=8)
    step_size_entry.pack(side=tk.LEFT, padx=5)
    
    # Feed rate input
    feed_rate_label = ttk.Label(inputs_frame, text="Feed rate:")
    feed_rate_label.pack(side=tk.LEFT, padx=(10, 5))
    
    feed_rate_var = tk.StringVar(value="300")
    feed_rate_entry = ttk.Entry(inputs_frame, textvariable=feed_rate_var, width=8)
    feed_rate_entry.pack(side=tk.LEFT, padx=5)
    
    return jog_frame



# Create main frames in correct order
header_frame = ttk.Frame(root)
header_frame.grid(row=0, column=0, columnspan=6, sticky="ew", padx=10, pady=5)

control_frame = ttk.Frame(root)
control_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=5)

messages_frame = ttk.Frame(root)
messages_frame.grid(row=2, column=0, columnspan=6, sticky="ew", padx=10, pady=5)

input_frame = ttk.Frame(root)
input_frame.grid(row=3, column=0, columnspan=6, sticky="ew", padx=10, pady=5)

movement_frame = ttk.Frame(root)
movement_frame.grid(row=4, column=0, columnspan=6, sticky="ew", padx=10, pady=5)

control_buttons_frame = ttk.Frame(movement_frame)
control_buttons_frame.grid(row=1, column=0, columnspan=3, pady=10)

# Basic movement buttons
joint_state_button = ttk.Button(control_buttons_frame, text="Move joints", command=go_to_joint_state)
joint_state_button.pack(side=tk.LEFT, padx=5)

cartesian_path_button = ttk.Button(control_buttons_frame, text="Move tool", command=plan_cartesian_path)
cartesian_path_button.pack(side=tk.LEFT, padx=5)

open_gripper_button = ttk.Button(control_buttons_frame, text="Open Gripper", command=open_gripper)
open_gripper_button.pack(side=tk.LEFT, padx=5)

close_gripper_button = ttk.Button(control_buttons_frame, text="Close Gripper", command=close_gripper)
close_gripper_button.pack(side=tk.LEFT, padx=5)




# Load icons
toggle = load_icon(os.path.join(user_path, "img/toggle-on-solid.png"), 25)
connekt = load_icon(os.path.join(user_path, "img/plug-solid.png"), 15)
ref = load_icon(os.path.join(user_path, "img/sync-alt-solid.png"), 20)
play = load_icon(os.path.join(user_path, "img/play-solid.png"), 15)
stop = load_icon(os.path.join(user_path, "img/stop-solid.png"), 15)
er = load_icon(os.path.join(user_path, "img/eraser-solid.png"), 20)

ico = Image.open(os.path.join(user_path, 'img/icon.png'))
photo = ImageTk.PhotoImage(ico)
root.wm_iconphoto(False, photo)


# Header section (row 0)
refresh_button = ttk.Button(header_frame, image=ref, command=refresh_ports)
refresh_button.pack(side=tk.LEFT, padx=(0, 5))

port_combobox = ttk.Combobox(header_frame, width=25)
port_combobox.pack(side=tk.LEFT, padx=5)

connect_button = ttk.Button(header_frame, text="Connect", image=connekt, compound=tk.LEFT, command=connect)
connect_button.pack(side=tk.LEFT, padx=5)

disconnect_button = ttk.Button(header_frame, text="Disconnect", command=disconnect)
disconnect_button.pack(side=tk.LEFT, padx=5)

toggle_button = ttk.Button(header_frame, image=toggle, command=sv_ttk.toggle_theme)
toggle_button.pack(side=tk.RIGHT, padx=5)

# Control buttons (row 1)
run_gcode_button = ttk.Button(control_frame, text="Run OL", image=play, compound=tk.LEFT, command=run_gcode_script)
run_gcode_button.pack(side=tk.LEFT, padx=5)

# Add the new "Run CL" button
run_cl_button = ttk.Button(control_frame, text="Run CL", image=play, compound=tk.LEFT, command=run_ros_script)
run_cl_button.pack(side=tk.LEFT, padx=5)

send_button = ttk.Button(control_frame, text="Run RoboDK", image=play, compound=tk.LEFT, command=send)
send_button.pack(side=tk.LEFT, padx=5)

stop_button = ttk.Button(control_frame, text="Stop", image=stop, compound=tk.LEFT)
stop_button.pack(side=tk.LEFT, padx=5)

# Messages section (row 2)
messages_label = ttk.Label(messages_frame, text="Messages:")
messages_label.pack(side=tk.LEFT)

clear_button = ttk.Button(messages_frame, image=er, command=clear_messages)
clear_button.pack(side=tk.RIGHT)

messages_text = tk.Text(messages_frame, height=8, width=50, state=tk.DISABLED)
messages_text.pack(fill=tk.X, pady=5)

# Input section (row 3)
input_container = ttk.Frame(input_frame)
input_container.pack(fill=tk.X)

gcode_entry = ttk.Entry(input_container, width=20)
gcode_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
gcode_entry.grid_remove()

# Button to send the data - Position it to the left of the loop toggle
send_button = ttk.Button(input_container, text="Send", command=send_data)
send_button.pack(side=tk.LEFT, padx=(0, 5))  # Adjust padding as needed

loop_toggle = ttk.Button(input_container, image=toggle, command=toggle_loop_mode)
loop_toggle.pack(side=tk.RIGHT)
loop_toggle.grid_remove()

# Closed loop frame
closed_loop_frame = ttk.Frame(input_frame)
closed_loop_frame.pack(fill=tk.X, pady=5)


# Closed loop controls
address_label = ttk.Label(closed_loop_frame, text="Address")
address_label.grid(row=0, column=0, padx=5, pady=5)

label_texts = ["Mode", "Speed", "", "Acc", "", "Position", "", "CRC"]
data_labels = [ttk.Label(closed_loop_frame, text=text) for text in label_texts]
for idx, label in enumerate(data_labels):
    label.grid(row=0, column=idx+2, padx=5, pady=5)

address_entry = ttk.Entry(closed_loop_frame, width=2)
address_entry.grid(row=1, column=0, padx=5, pady=5)

data_entries = [ttk.Entry(closed_loop_frame, width=2) for _ in range(8)]
for idx, entry in enumerate(data_entries):
    entry.grid(row=1, column=idx+2, padx=5, pady=5)


# Joint State Controls with improved layout
joint_frame = ttk.LabelFrame(movement_frame, text="Joint jog")
joint_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

for i, label in enumerate(['X', 'Y', 'Z', 'A', 'B', 'C']):
    slider_frame = ttk.Frame(joint_frame)
    slider_frame.grid(row=i, column=0, sticky="ew", pady=2)
    
    # Label is now part of the slider frame
    ttk.Label(slider_frame, text=label, width=2).pack(side=tk.LEFT, padx=(5, 10))
    
    # Slider
    slider = ttk.Scale(slider_frame, from_=-3.14, to=3.14, orient=tk.HORIZONTAL, length=200)
    slider.set(0)
    slider.pack(side=tk.LEFT, padx=5)
    joint_state_sliders.append(slider)
    
    # Value entry
    entry = ttk.Entry(slider_frame, width=6)
    entry.pack(side=tk.LEFT, padx=5)
    entry.bind('<Return>', update_joint_state_value(i))
    joint_state_entries.append(entry)
    
    
    joint_name_to_slider[f"joint{i+1}"] = slider


reset_all_button = ttk.Button(joint_frame, text="Reset Zero", command=reset_all_axes)
reset_all_button.grid(row=6, column=0, pady=5)


###########################
# Create movement frame
movement_frame = ttk.Frame(root)
movement_frame.grid(row=4, column=0, columnspan=6, sticky="ew", padx=10, pady=5)

# Create entry fields for X, Y, Z
entry_frame = ttk.LabelFrame(movement_frame, text="Enter Cartesian Coordinates")
entry_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

x_label = ttk.Label(entry_frame, text="X:")
x_label.grid(row=0, column=0)
x_entry = ttk.Entry(entry_frame, width=10)
x_entry.grid(row=0, column=1)

y_label = ttk.Label(entry_frame, text="Y:")
y_label.grid(row=1, column=0)
y_entry = ttk.Entry(entry_frame, width=10)
y_entry.grid(row=1, column=1)

z_label = ttk.Label(entry_frame, text="Z:")
z_label.grid(row=2, column=0)
z_entry = ttk.Entry(entry_frame, width=10)
z_entry.grid(row=2, column=1)

# Create a button to trigger the movement
move_button = ttk.Button(entry_frame, text="Move to XYZ", command=plan_cartesian_path)
move_button.grid(row=3, column=0, columnspan=2, pady=5)
################################



##############################################################################
# ALTER CODE-BLOCK FÜR TOOL JOG ERSETZEN durch diesen
##############################################################################
tool_frame = ttk.LabelFrame(movement_frame, text="Tool jog")
tool_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

cartesian_path_entries = []  # Falls die Liste der Entry-Felder existiert

for i, label in enumerate(['X', 'Y', 'Z']):
    slider_frame = ttk.Frame(tool_frame)
    slider_frame.grid(row=i, column=0, sticky="ew", pady=2)
    
    ttk.Label(slider_frame, text=label, width=2).pack(side=tk.LEFT, padx=(5, 10))
    
    # Slider erstellen, aber erst später die `command`-Zuweisung machen
    slider = ttk.Scale(
        slider_frame, 
        from_=-1.0,       # Beispielwerte, anpassen falls nötig
        to=1.0, 
        orient=tk.HORIZONTAL, 
        length=200
    )
    slider.set(0)
    slider.pack(side=tk.LEFT, padx=5)
    cartesian_path_sliders.append(slider)  # **Hier wird die Liste befüllt**

    # Entry-Feld hinzufügen
    entry = ttk.Entry(slider_frame, width=8)
    entry.pack(side=tk.LEFT, padx=(5, 10))
    entry.bind("<Return>", lambda e, idx=i: on_tool_entry_change(idx))
    cartesian_path_entries.append(entry)

    # Initialwerte setzen
    update_tool_slider_and_entry(i, 0.0)

# **Jetzt die `command`-Zuweisung vornehmen, um Rekursion zu vermeiden**
for idx, slider in enumerate(cartesian_path_sliders):
    slider.configure(command=lambda v, idx=idx: root.after(10, lambda: on_tool_slider_change(idx)))



# Add hide button for Tool jog
tool_hide_btn = ttk.Button(movement_frame, text="Hide Tool Jog", command=toggle_tool_frame)
tool_hide_btn.grid(row=2, column=1, pady=(0, 5), sticky="n")

# Visual control canvas
canvas_frame = ttk.LabelFrame(movement_frame, text="Visual Control")
canvas_frame.grid(row=0, column=2, padx=10, pady=5, sticky="nsew")

# Add hide button for Visual Control
visual_hide_btn = ttk.Button(movement_frame, text="Hide Visual Control", command=toggle_visual_frame)
visual_hide_btn.grid(row=2, column=2, pady=(0, 5), sticky="n")

canvas = tk.Canvas(canvas_frame, height=302, width=302, bd=0, highlightthickness=0, relief="ridge")
canvas.pack(padx=5, pady=5)


# Control buttons frame
control_buttons_frame = ttk.Frame(movement_frame)
control_buttons_frame.grid(row=1, column=0, columnspan=3, pady=10)

# Update movement frame grid configuration
movement_frame.rowconfigure(0, weight=1)  # Main controls row
movement_frame.rowconfigure(1, weight=0)  # Spacer row
movement_frame.rowconfigure(2, weight=0)  # Hide buttons row
movement_frame.rowconfigure(3, weight=0)  # Control buttons row

joint_state_button = ttk.Button(control_buttons_frame, text="Move joints", command=go_to_joint_state)
joint_state_button.pack(side=tk.LEFT, padx=5)

cartesian_path_button = ttk.Button(control_buttons_frame, text="Move tool", command=plan_cartesian_path)
cartesian_path_button.pack(side=tk.LEFT, padx=5)

open_gripper_button = ttk.Button(control_buttons_frame, text="Open Gripper", command=open_gripper)
open_gripper_button.pack(side=tk.LEFT, padx=5)

close_gripper_button = ttk.Button(control_buttons_frame, text="Close Gripper", command=close_gripper)
close_gripper_button.pack(side=tk.LEFT, padx=5)

# Configure grid weights for better resizing
movement_frame.columnconfigure(0, weight=1)
movement_frame.columnconfigure(1, weight=1)
movement_frame.columnconfigure(2, weight=1)

# Set initial theme
sv_ttk.set_theme("light")


# Load and setup background images
BACKGROUND_IMAGE_PATH = os.path.join(user_path, "img/strelice.png")
BUTTON_IMAGE_PATH = os.path.join(user_path, "img/bg.png")

background_img = Image.open(BACKGROUND_IMAGE_PATH)
zoom_level = 0.8
new_width = int(background_img.width * zoom_level)
new_height = int(background_img.height * zoom_level)
background_img = background_img.resize((new_width, new_height), Image.LANCZOS)
background_img = ImageTk.PhotoImage(background_img)
background = canvas.create_image(151, 151, image=background_img)

# Define button positions and create canvas buttons
button_info = [
    ((48, 28), 65, 59, "Z+"),
    ((185, 28), 65, 59, "Z-"),
    ((110, 100), 73, 40, "Y-"),
    ((12, 145), 79, 46, "X-"),
    ((200, 145), 79, 46, "X+"),
    ((95, 200), 100, 70, "Y+")
]

buttons = []
for (x, y), width, height, name in button_info:
    button = CanvasButton(canvas, x, y, width, height, BUTTON_IMAGE_PATH, name, btn_clicked)
    buttons.append(button)

def on_click(event):
    x, y = event.x, event.y
    for button in buttons:
        if x >= button.canvas.coords(button.button)[0] and \
           y >= button.canvas.coords(button.button)[1] and \
           x <= button.canvas.coords(button.button)[0] + button.btn_image.width() and \
           y <= button.canvas.coords(button.button)[1] + button.btn_image.height():
            button.command(button.name)
            break

# Bind click event
root.bind("<Button-1>", on_click)

# Initialize ROS node and publishers/subscribers
rospy.init_node('arctos_control_gui', anonymous=True)
ui_command_pub = rospy.Publisher('/ui_command', String, queue_size=10)
joint_states_sub = rospy.Subscriber('/joint_states', JointState, update_joint_sliders)
transformed_tf_sub = rospy.Subscriber('/transformed_tf', TransformStamped, update_cartesian_sliders)

# Configure grid weights
for i in range(21):
    root.rowconfigure(i, weight=1)
for i in range(6):
    root.columnconfigure(i, weight=1)

# Set initial theme
sv_ttk.set_theme("light")
# Add this to your existing code, just before root.mainloop():
manual_jog_frame = create_manual_jog_controls(movement_frame)

# Update the movement_frame grid configuration
movement_frame.columnconfigure(3, weight=1)  # Add column weight for the new frame
# Start the main loop
root.mainloop()
