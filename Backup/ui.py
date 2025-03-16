import os
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import JointState
from geometry_msgs.msg import TransformStamped
from PIL import Image, ImageTk
import sv_ttk
import threading
import math

# Import local modules
from arctos_controller import ArctosController
from path_planning import PathPlanner
import homing
import Backup.move_can as move_can

# ------------------------------
# CONFIGURATION
# ------------------------------

# Change this according to your folder 
user_path = "/home/michael/arctosgui"

Arctos = ArctosController()

root = tk.Tk()
root.title("Arctos CAN controller")

planner = PathPlanner()

# ------------------------------
# GLOBAL VARIABLES
# ------------------------------
last_joint_states = None
last_cartesian_position = None
is_closed_loop = True  # New variable for loop mode

# Initialize all required lists and dictionaries at the start
joint_state_sliders = []
joint_state_entries = []
cartesian_path_sliders = []
joint_name_to_slider = {}


# ------------------------------
# CLASSES
# ------------------------------
class CanvasButton:
    """
    A class to create a button inside a Tkinter canvas.
    
    This class allows embedding an image-based button into a Tkinter canvas,
    enabling customized button placements and actions within the graphical interface.
    
    Attributes:
        canvas (tk.Canvas): The Tkinter canvas where the button will be placed.
        x (int): The x-coordinate of the button on the canvas.
        y (int): The y-coordinate of the button on the canvas.
        width (int): The width of the button.
        height (int): The height of the button.
        image_path (str): The file path to the button's image.
        name (str): A unique name identifier for the button.
        command (function): The function to execute when the button is clicked.
        btn_image (ImageTk.PhotoImage): The processed image used for the button.
        button (int): The canvas object ID of the button.
    
    Methods:
        __init__: Initializes the button with an image and places it on the canvas.
    """
    def __init__(self, canvas: tk.Canvas, x: int, y: int, width: int, height: int, image_path: str, name: str, command):
        """
        Initializes the CanvasButton and places it on the given canvas.
        
        :param canvas: The Tkinter canvas widget where the button will be placed.
        :param x: The x-coordinate position on the canvas.
        :param y: The y-coordinate position on the canvas.
        :param width: The width of the button image.
        :param height: The height of the button image.
        :param image_path: Path to the image file used for the button.
        :param name: The unique identifier name for the button.
        :param command: The function to execute when the button is clicked.
        """
        x, y = canvas.canvasx(x), canvas.canvasy(y)  # Adjust coordinates to canvas space
        self.name = name
        self.canvas = canvas
        self.command = command
        
        # Load and process the button image
        self.btn_image = Image.open(image_path)
        self.btn_image = self.btn_image.resize((width, height), Image.LANCZOS)
        self.btn_image = ImageTk.PhotoImage(self.btn_image)
        
        # Create button on the canvas
        self.button = canvas.create_image(x, y, anchor='nw', image=self.btn_image, tags=self.name)



# ------------------------------
# FRAME FOR PATH PLANNING
# ------------------------------
path_frame = ttk.LabelFrame(root, text="Path Planning")
path_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

# Listbox to display saved poses
poses_listbox = tk.Listbox(path_frame, height=6, width=80)
poses_listbox.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

def save_pose() -> None:
    """
    Saves the current robot pose by retrieving joint states from MoveIt!
    and storing them using the planner. The pose list in the UI is updated accordingly.
    """
    print("Waiting for MoveIt! /joint_states...")
    rospy.sleep(2)  # Wait to ensure ROS has time to send the pose
    msg: JointState = rospy.wait_for_message("/joint_states", JointState)  # Get the latest joint state message
    planner.capture_pose(msg)  # Store the pose using the planner
    update_pose_list()  # Refresh the UI list

def save_program() -> None:
    """
    Saves the entire sequence of poses stored in the planner to a file or memory.
    Updates the pose list in the UI after saving.
    """
    planner.save_program()  # Save the program
    update_pose_list()  # Refresh the UI list

def load_program() -> None:
    """
    Loads a previously saved sequence of poses into the planner.
    Updates the pose list in the UI after loading.
    """
    planner.load_program()  # Load the program
    update_pose_list()  # Refresh the UI list

def execute_path() -> None:
    """
    Executes the planned path using a separate thread to prevent UI freezing.
    """
    path_thread = threading.Thread(target=planner.execute_path, args=(Arctos,))
    path_thread.start()  # Start execution in a new thread

def update_pose_list() -> None:
    """
    Refreshes the Listbox in the UI to display the updated list of saved poses.
    """
    poses_listbox.delete(0, tk.END)  # Clear existing entries
    for idx, pose in enumerate(planner.poses):
        poses_listbox.insert(tk.END, f"Pose {idx+1}: {pose}")  # Insert updated poses

# Buttons to interact with path planning functionalities
save_pose_btn = ttk.Button(path_frame, text="Save Pose", command=save_pose)
save_pose_btn.grid(row=1, column=0, padx=5, pady=5)

save_program_btn = ttk.Button(path_frame, text="Save Program", command=save_program)
save_program_btn.grid(row=1, column=1, padx=5, pady=5)

load_program_btn = ttk.Button(path_frame, text="Load Program", command=load_program)
load_program_btn.grid(row=2, column=0, padx=5, pady=5)

execute_path_btn = ttk.Button(path_frame, text="Execute Program", command=execute_path)
execute_path_btn.grid(row=2, column=1, padx=5, pady=5)



# ------------------------------
# GUI FUNCTIONS
# ------------------------------
def console_script() -> None:
    """
    Executes the console script by running 'console.py' using the system's Python 3 interpreter.
    """
    os.system("python3 console.py")

def update_joint_sliders(data: JointState) -> None:
    """
    Updates the joint sliders with the latest joint positions received from ROS.
    
    Args:
        data (JointState): ROS message containing joint names and their respective positions.
    """
    global last_joint_states
    if last_joint_states is None or data.position != last_joint_states.position:
        last_joint_states = data
        for i, joint in enumerate(data.name):
            if joint in joint_name_to_slider:
                slider = joint_name_to_slider[joint]
                slider.set(data.position[i])
                update_joint_entry(i, data.position[i] * (180 / math.pi))

def update_cartesian_sliders(data) -> None:
    """
    Updates the cartesian sliders with the latest translation data.
    
    Args:
        data: ROS transform message containing x, y, and z translation values.
    """
    global last_cartesian_position
    if last_cartesian_position is None or \
        data.transform.translation.x != last_cartesian_position.transform.translation.x or \
        data.transform.translation.y != last_cartesian_position.transform.translation.y or \
        data.transform.translation.z != last_cartesian_position.transform.translation.z:
        
        last_cartesian_position = data

        x_value = data.transform.translation.x
        y_value = data.transform.translation.y
        z_value = data.transform.translation.z

        # Update entry fields
        x_entry.delete(0, tk.END)
        x_entry.insert(0, f"{x_value:.3f}")

        y_entry.delete(0, tk.END)
        y_entry.insert(0, f"{y_value:.3f}")

        z_entry.delete(0, tk.END)
        z_entry.insert(0, f"{z_value:.3f}")

def clear_messages() -> None:
    """
    Clears the message text box in the UI.
    """
    messages_text.config(state=tk.NORMAL)
    messages_text.delete('1.0', tk.END)
    messages_text.config(state=tk.DISABLED)

def update_message(message: str) -> None:
    """
    Updates the message text box with a new message.
    
    Args:
        message (str): The message to display in the UI.
    """
    messages_text.config(state=tk.NORMAL)
    messages_text.insert(tk.END, message + "\n")
    messages_text.see(tk.END)
    messages_text.config(state=tk.DISABLED)
    print("Message updated:", message)

def run_move_can() -> None:
    """
    Retrieves joint states and moves the robot accordingly.
    """
    joint_positions_rad = move_can.get_joint_states()
    if joint_positions_rad is None:
        rospy.logwarn("Movement aborted, no valid joint positions received.")
        return
    
    move_can.wait_for_motors_to_stop(Arctos)
    Arctos.move_to_angles(joint_positions_rad)

def update_joint_state_value(index: int):
    """
    Creates a callback function to update the joint state based on user input.
    
    Args:
        index (int): Index of the joint.
    """
    def callback(_):
        try:
            value = float(joint_state_entries[index].get())
            joint_state_sliders[index].set(value * (math.pi / 180))
        except ValueError:
            pass
    return callback

def update_joint_entry(index: int, value: float) -> None:
    """
    Updates the entry field for a joint state.
    
    Args:
        index (int): Index of the joint.
        value (float): Joint angle in degrees.
    """
    if index < len(joint_state_entries):
        joint_state_entries[index].delete(0, tk.END)
        joint_state_entries[index].insert(0, f"{value:.2f}")

def go_to_joint_state() -> None:
    """
    Publishes a command to move the robot to a specified joint state.
    """
    joint_state_values = [slider.get() for slider in joint_state_sliders]
    ui_command_pub.publish("go_to_joint_state," + ','.join(map(str, joint_state_values)))

def set_zero_postion() -> None:
    """
    Moves the robot to a zero position where all joints are set to 0 degrees.
    """
    joint_state_values = [0.0] * 6
    ui_command_pub.publish("go_to_joint_state," + ','.join(map(str, joint_state_values)))

def open_gripper() -> None:
    """
    Sends a command to open the gripper.
    """
    Arctos.open_gripper()

def close_gripper() -> None:
    """
    Sends a command to close the gripper.
    """
    Arctos.close_gripper()

def load_icon(image_path: str, width: int) -> ImageTk.PhotoImage:
    """
    Loads an image and converts it to an icon.
    
    Args:
        image_path (str): Path to the image file.
        width (int): Desired width of the icon.
    
    Returns:
        ImageTk.PhotoImage: The processed image ready for use in the UI.
    """
    try:
        image = Image.open(image_path).convert("RGBA")  # Ensure transparency
        image = image.resize((width, width), Image.LANCZOS)  # Resize while maintaining aspect ratio
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Error loading icon {image_path}: {e}")
        return None


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


toggle_button = ttk.Button(control_frame, image=toggle, command=sv_ttk.toggle_theme)
toggle_button.pack(side=tk.RIGHT, padx=5)

# Add the new "Run CL" button
run_cl_button = ttk.Button(control_frame, text="Start Movement", image=play, compound=tk.LEFT, command=run_move_can)
run_cl_button.pack(side=tk.LEFT, padx=5)

# Messages section (row 2)
messages_label = ttk.Label(messages_frame, text="Messages:")
messages_label.pack(side=tk.LEFT)

clear_button = ttk.Button(messages_frame, image=er, command=clear_messages)
clear_button.pack(side=tk.RIGHT)

messages_text = tk.Text(messages_frame, height=8, width=50, state=tk.DISABLED)
messages_text.pack(fill=tk.X, pady=5)


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


# ------------------------------
# CARTESIAN CONTROL - START
# ------------------------------

# Step size for incremental position adjustments
STEP_SIZE = 0.001  # Can be adjusted as needed

# Dictionary to track which keys are pressed
key_states = {}

def move_robot_to_xyz() -> None:
    """
    Moves the robot to a specified XYZ position using Cartesian path planning.
    
    Retrieves the X, Y, and Z values from user input fields and publishes a movement command.
    """
    try:
        x_pos = float(x_entry.get())
        y_pos = float(y_entry.get())
        z_pos = float(z_entry.get())
        
        cartesian_path_values = [x_pos, y_pos, z_pos]
        ui_command_pub.publish("plan_cartesian_path," + ','.join(map(str, cartesian_path_values)))
        
        update_message(f"Moving to XYZ: {x_pos}, {y_pos}, {z_pos}")
    
    except ValueError:
        update_message("Invalid input! Please enter numerical values for X, Y, and Z.")

def adjust_position(axis: str, delta: float):
    try:
        new_value_x = float(x_entry.get())
        new_value_y = float(y_entry.get())
        new_value_z = float(z_entry.get())

        previous_values = [new_value_x, new_value_y, new_value_z]  # Save old values

        if axis == 'x':
            new_value_x += delta
            x_entry.delete(0, tk.END)
            x_entry.insert(0, str(new_value_x))
        elif axis == 'y':
            new_value_y += delta
            y_entry.delete(0, tk.END)
            y_entry.insert(0, str(new_value_y))
        elif axis == 'z':
            new_value_z += delta
            z_entry.delete(0, tk.END)
            z_entry.insert(0, str(new_value_z))

        updated_values = [new_value_x, new_value_y, new_value_z]

        # Only send movement command if values actually changed
        if updated_values != previous_values:
            ui_command_pub.publish("plan_cartesian_path," + ','.join(map(str, updated_values)))

    except ValueError:
        update_message(f"Invalid input in {axis.upper()} field!")


def on_key_press(event):
    """
    Starts the continuous movement when a key is pressed.
    """
    key = event.keysym
    if key not in key_states:  # Prevent duplicate calls
        key_states[key] = True
        update_position()

def on_key_release(event):
    """
    Stops the continuous movement when a key is released.
    """
    key = event.keysym
    if key in key_states:
        key_states.pop(key)

def update_position():
    """
    Continuously updates the position while keys are held down.
    """
    if 'Left' in key_states:
        adjust_position('x', -STEP_SIZE)
    if 'Right' in key_states:
        adjust_position('x', STEP_SIZE)
    if 'Up' in key_states:
        adjust_position('z', STEP_SIZE)
    if 'Down' in key_states:
        adjust_position('z', -STEP_SIZE)
    if 'w' in key_states:
        adjust_position('y', STEP_SIZE)
    if 's' in key_states:
        adjust_position('y', -STEP_SIZE)

    # Continue updating if any key is still pressed
    if key_states:
        root.after(100, update_position)  # Adjust delay for speed




# Frame for XYZ position input
xyz_frame = ttk.LabelFrame(movement_frame, text="Move to XYZ")
xyz_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

# X input field
ttk.Label(xyz_frame, text="X:").grid(row=0, column=0, padx=5, pady=2)
x_entry = ttk.Entry(xyz_frame, width=10)
x_entry.grid(row=0, column=1, padx=5, pady=2)
x_entry.insert(0, "0.0")  # Set default value

# Y input field
ttk.Label(xyz_frame, text="Y:").grid(row=1, column=0, padx=5, pady=2)
y_entry = ttk.Entry(xyz_frame, width=10)
y_entry.grid(row=1, column=1, padx=5, pady=2)
y_entry.insert(0, "0.0")  # Set default value

# Z input field
ttk.Label(xyz_frame, text="Z:").grid(row=2, column=0, padx=5, pady=2)
z_entry = ttk.Entry(xyz_frame, width=10)
z_entry.grid(row=2, column=1, padx=5, pady=2)
z_entry.insert(0, "0.0")  # Set default value

# Button to send XYZ values
move_xyz_button = ttk.Button(xyz_frame, text="Move to XYZ", command=move_robot_to_xyz)
move_xyz_button.grid(row=3, column=0, columnspan=2, pady=5)

# Bind keyboard events for incremental movement
root.bind("<Left>", on_key_press)   # Decrease X
root.bind("<Right>", on_key_press)  # Increase X
root.bind("<Up>", on_key_press)     # Increase Z
root.bind("<Down>", on_key_press)   # Decrease Z
root.bind("w", on_key_press)        # Increase Y
root.bind("s", on_key_press)        # Decrease Y

# Bind keyboard events for continuous movement
root.bind("<KeyPress>", on_key_press)   # Start movement
root.bind("<KeyRelease>", on_key_release)  # Stop movement

# ------------------------------
# CARTESIAN CONTROL - END
# ------------------------------


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

move_to_zero_button = ttk.Button(control_buttons_frame, text="Move to zero pose", command=lambda: homing.move_to_zero_pose(Arctos))
move_to_zero_button.pack(side=tk.LEFT, padx=5, pady=6)

move_to_sleep_button = ttk.Button(control_buttons_frame, text="Move to sleep pose", command=lambda: homing.move_to_sleep_pose(Arctos))
move_to_sleep_button.pack(side=tk.LEFT, padx=5, pady=6)

set_zero_postion_button = ttk.Button(control_buttons_frame, text="Set zero position", command=set_zero_postion)
set_zero_postion_button.pack(side=tk.LEFT, padx=5)

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

buttons = []

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

# Update the movement_frame grid configuration
movement_frame.columnconfigure(3, weight=1)  # Add column weight for the new frame
# Start the main loop
root.mainloop()