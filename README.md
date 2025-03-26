# 🤖 Arctos Robot GUI

Modern web-based control interface for the Arctos Robot, built with NiceGUI and Python.

## 🌟 Features

- Modern Material Design UI 
- Real-time joint and cartesian position updates
- Interactive robot control:
  - Joint control 
  - Cartesian position input
  - Path planning and program execution
  - Gripper control
  - Keyboard shortcuts for fine movement
- MKS Servo configuration interface



## 🛠️ Setup

### Prerequisites

- Python 3.8 or higher
- CAN interface for robot communication
- Access to the Arctos Robot hardware

---

## 🔧 Installation Options

You can install the project in two ways, depending on your preferences and whether you want to use `conda` for environment management.

---

### 🅰️ Option 1: Standard Python Installation (with manual Pinocchio setup)

1. Clone the repository:
   ```bash
   git clone https://github.com/jetta18/ArctosGuiPython.git
   cd ArctosGuiPython
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/macOS
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install **Pinocchio manually** using the official instructions:  
   👉 https://stack-of-tasks.github.io/pinocchio/download.html

---

### 🅱️ Option 2: Conda-based Installation (Recommended for Robotics)

1. Clone the repository:
   ```bash
   git clone https://github.com/jetta18/ArctosGuiPython.git
   cd ArctosGuiPython
   ```

2. Create the Conda environment (the `environment.yml` file is included in the repository):
   ```bash
   conda env create -f environment.yml
   ```

3. Activate the environment:
   ```bash
   conda activate arctos-env
   ```

4. Start the application:
   ```bash
   python src/main.py
   ```

---

### 🎛️ CAN Interface Setup

Set up the CAN interface using the provided script(Important to set this up!):

```bash
cd ~/ArctosGuiPython/scripts
sudo ./setup_canable.sh
```

---

### 🚀 Running the Application

1. Launch the GUI:
   ```bash
   cd ~/ArctosGuiPython/src
   python3 main.py
   ```

2. Open your browser and go to:
   ```
   http://localhost:8080
   ```


## 📁 Project Structure

```
ArctosGuiPython/
├── src/                    # Source code
│   ├── core/              # Core robot functionality
│   ├── config/            # User preferences (Custom settings fur GUI)
│   ├── models/            # Meshes and urdf
│   ├── services/          # Robot services and communication
│   ├── components/        # UI components
│   ├── pages/             # Web pages
│   ├── programs/          # Stored programs from path planning
│   └── utils/             # Utility functions
├── assets/                # Static assets (images, etc.)
├── scripts/               # Script for starting can interface (currently)
├── docs/                  # Documentation
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── environment.yml        # Conda env file
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
