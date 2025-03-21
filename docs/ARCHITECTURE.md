# Arctos Robot GUI Architecture

## Overview

The Arctos Robot GUI is a modern web-based control interface built with NiceGUI and Python. It provides real-time control and monitoring of the Arctos robot arm through a user-friendly interface.

## Project Structure

### Core (`src/core/`)
- `ArctosController.py`: Main robot control interface
- `ArctosPinocchio.py`: Kinematics and dynamics calculations
- `PathPlanner.py`: Path planning and trajectory generation
- `homing.py`: Robot homing and calibration procedures

### Services (`src/services/`)
- `mks_servo_can/`: CAN communication library for MKS servos
  - Motor control and configuration
  - Real-time feedback and monitoring

### UI Components (`src/components/`)
- `menu.py`: Navigation menu component
- Future components for reusable UI elements

### Pages (`src/pages/`)
- `home.py`: Landing page
- `control.py`: Main robot control interface
- `settings.py`: Application settings
- `mks_config.py`: Motor configuration interface

### Utils (`src/utils/`)
- Helper functions and utilities
- Keyboard control handlers
- Common calculations and conversions

## Key Features

1. **Robot Control**
   - Joint position control
   - Cartesian position control
   - Path planning and execution
   - Gripper control

2. **User Interface**
   - Real-time position updates
   - 3D visualization
   - Interactive controls
   - Status messages and console

3. **Safety Features**
   - Joint limit checking
   - Movement validation
   - Emergency stop functionality

## Communication Flow

1. User Interface (NiceGUI) → Control Commands
2. Path Planning → Trajectory Generation
3. Kinematics Calculation → Joint Positions
4. CAN Communication → Motor Control
5. Motor Feedback → UI Updates

## Dependencies

- NiceGUI: Web interface framework
- Pinocchio: Robot kinematics
- python-can: CAN bus communication
- MeshCat: 3D visualization
