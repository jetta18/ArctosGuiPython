# 🤖 Arctos Robot GUI

Modern web-based control interface for the Arctos Robot, built with NiceGUI and Python.

## 🌟 Features

- Modern Material Design UI with dark mode support
- Real-time joint and cartesian position updates
- Interactive robot control:
  - Joint control with sliders
  - Cartesian position input
  - Path planning and program execution
  - Gripper control
  - Keyboard shortcuts for fine movement
- Integrated message display and console
- MKS Servo configuration interface

## 🛠️ Setup

### Prerequisites

- Python 3.8 or higher
- CAN interface for robot communication
- Access to the Arctos Robot hardware

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jetta18/ArctosGuiPython.git
   cd ArctosGuiPython
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up CAN interface (if needed):
   ```bash
   sudo ./setup_canable.sh
   ```

## 🚀 Usage

1. Start the application:
   ```bash
   python main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8080
   ```

## 📁 Project Structure

```
ArctosGuiPython/
├── src/                    # Source code
│   ├── core/              # Core robot functionality
│   ├── services/          # Robot services and communication
│   ├── components/        # UI components
│   ├── pages/             # Web pages
│   └── utils/             # Utility functions
├── assets/                # Static assets (images, etc.)
├── docs/                  # Documentation
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🧪 Testing

Test files are located in the `tests/` directory. To run tests:

```bash
python -m pytest tests/
```

## 📝 License

This project is licensed under [Your License]. Note that the included MKS-Servo CAN library is licensed under the GNU General Public License v3.0.

## 👥 Contributing

- MKS-Servo CAN library
- NiceGUI framework for the modern web interface
- Pinocchio team for robotics calculations
- MeshCat for 3D visualization

## Useful Links

- [Documentation](https://arctosrobotics.com/docs/)
- [Manuals](https://arctosrobotics.com/#Assembly)
- [CAD Files](https://arctosrobotics.com/#Assembly)