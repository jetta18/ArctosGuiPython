# Arctos Robot Control GUI

A modern web-based control interface for the Arctos robot arm, built with NiceGUI and Python. This application provides an intuitive and responsive interface for controlling and monitoring the robot's movements, position, and orientation.


🟡⚠ **WARNING: THIS PROJECT IS IN DEVELOPMENT!** ⚠🟡  
🚨 **Use with caution and at your own risk.**  
Unexpected behavior may occur, and there is **no guarantee of stability**.  
Make sure to follow all **safety precautions** when operating the robot.


## Table of Contents
- [Features](#features)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
- [Keyboard Controls](#keyboard-controls)
- [Project Structure](#project-structure)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Useful Links](#useful-links)



## Features

- **Modern Web Interface**: 
  - Built with NiceGUI framework for a responsive and user-friendly experience
  - Real-time status updates

- **Robot Control**:
  - Joint position control with numerical inputs
  - Cartesian position control (X, Y, Z coordinates)
  - End-effector orientation control (Roll, Pitch, Yaw)
  - Gripper open/close functionality
  - Fine movement control via keyboard

- **Path Planning & Programs**:
  - Save current robot poses
  - Create movement programs
  - Save and load programs
  - Execute planned paths

- **3D Visualization**:
  - Real-time 3D robot model visualization using MeshCat
  - Live updates of robot state and position
  - Interactive viewing angles

- **Real-time Feedback**:
  - Joint angle display in degrees
  - End-effector position monitoring (m)
  - System status messages in console
  - Visual notifications for actions

## Dependencies

This project uses several key libraries:

- **NiceGUI**: Modern web interface framework
- **Pinocchio**: Robot kinematics and dynamics calculations
- **MeshCat**: 3D visualization
- **MKS-Servo CAN**: Library for MKS Servo motor control via CAN
  - Used for motor communication and control
  - GNU General Public License v3.0

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jetta18/ArctosGuiPython.git
cd ArctosGuiPython
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Hardware Requirements:
   - CAN interface compatible with python-can
   - MKS Servo motors (tested with MKS-Servo57D/42D)
   - Proper CAN bus configuration (500kbps)

## Usage
Before starting make sure everything is conencted and configured. The MKS CANable must be visible on a /dev/ttyACM* port.
You can check that with:
```bash
 ls /dev/ttyACM*
```
You should recieve something like /dev/ttyACM1 as output.

1. Move to the repo folder:
```bash
cd ArctosGuiPython
```

2. Start the application:
```bash
python main.py
```

3. Open your web browser and navigate to (just if it don't open up itself):
```
http://localhost:8080
```

4. Initialize the Robot:
   - On "Home" page click "control"
   - Click "Initialize Robot" button
   - Wait for the connection confirmation
   - The 3D visualization will appear when ready

5. Control Methods:
   - **Joint Control**: Enter specific angles for each joint
   - **Cartesian Control**: Set X, Y, Z coordinates
   - **Keyboard Control**: Use WASD-QE keys for fine movement
   - **Program Creation**: Save poses and create movement sequences

## Keyboard Controls

When keyboard control is enabled via the toggle switch:
- `W/S`: Forward/Backward movement (Y-axis)
- `A/D`: Left/Right movement (X-axis)
- `Q/E`: Up/Down movement (Z-axis)

Movement increment: 2mm per keypress

Note that currently cartesian control uses meter(m). Z = 0.5 means 500mm.

## Project Structure

- `main.py`: Application entry point and page routing
- `pages/`: Web interface components
  - `control.py`: Main robot control interface
  - `home.py`: Landing page
  - `settings.py`: Configuration interface
  - `mks_config.py`: MKS servo configuration
- `components/`: Reusable UI components
  - `menu.py`: Navigation menu
- `arctos_controller.py`: Robot hardware interface
- `ArctosPinocchio.py`: Kinematics and dynamics calculations
- `path_planning.py`: Path planning and program execution
- `utils.py`: Utility functions and keyboard control
- `meshes/`: 3D model files for visualization
- `mks_servo_can/`: MKS Servo CAN interface library (GPL-3.0)


## License

This project is licensed under [Your License]. Note that the included MKS-Servo CAN library is licensed under the GNU General Public License v3.0.

## Acknowledgments

- MKS-Servo CAN library
- NiceGUI framework for the modern web interface
- Pinocchio team for robotics calculations
- MeshCat for 3D visualization

## Useful Links

- [Documentation](https://arctosrobotics.com/docs/)
- [Manuals](https://arctosrobotics.com/#Assembly)
- [CAD Files](https://arctosrobotics.com/#Assembly)