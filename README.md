# Arctos Robot Control GUI

A modern web-based control interface for the Arctos robot arm, built with NiceGUI and Python. This application provides an intuitive and responsive interface for controlling and monitoring the robot's movements, position, and orientation in real-time.

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
  - Real-time trajectory visualization

- **3D Visualization**:
  - Real-time 3D robot model visualization using MeshCat
  - Live updates of robot state and position
  - Interactive viewing angles

- **Real-time Feedback**:
  - Joint angle display in degrees
  - End-effector position monitoring (mm)
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
  - Included as a submodule in `mks_servo_can/`

## Installation

1. Clone the repository with submodules:
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
   - MKS Servo motors (tested with MKS-Servo57D)
   - Proper CAN bus configuration (500kbps)

## Usage

1. Start the application:
```bash
python main.py
```

2. Open your web browser and navigate to:
```
http://localhost:8080
```

3. Initialize the Robot:
   - Click "Initialize Robot" button
   - Wait for the connection confirmation
   - The 3D visualization will appear when ready

4. Control Methods:
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

## Technical Details

- **Framework**: NiceGUI for modern web interface
- **Kinematics**: Pinocchio library for robot calculations
- **Visualization**: MeshCat for 3D rendering
- **Motor Control**: 
  - MKS Servo CAN protocol
  - 500kbps CAN bus communication
  - Real-time position and speed control
- **Movement Control**: 
  - Direct joint control
  - Inverse kinematics for Cartesian control
  - Path planning for programmed movements

## Requirements

- Python 3.8+
- NiceGUI 1.4.0+
- Pinocchio 2.6.17+
- MeshCat 0.3.2+
- python-can with SLCAN support
- MKS Servo motors
- Modern web browser
- Other dependencies listed in `requirements.txt`

## License

This project is licensed under [Your License]. Note that the included MKS-Servo CAN library is licensed under the GNU General Public License v3.0.

## Acknowledgments

- MKS-Servo CAN library
- NiceGUI framework for the modern web interface
- Pinocchio team for robotics calculations
- MeshCat for 3D visualization
