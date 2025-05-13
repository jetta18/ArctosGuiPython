# 🤖 Arctos Robot GUI

Modern web-based control interface for the Arctos Robot, built with NiceGUI and Python.

## 🌟 Features

- **Modern UI**: Material Design interface with real-time updates
- **Robot Control**:
  - Joint and Cartesian position control
  - Path planning and program execution
  - Gripper control
  - Keyboard shortcuts for fine movement
- **Configuration**:
  - MKS Servo configuration
  - Customizable settings

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **CAN interface** for robot communication
- **Arctos Robot hardware** (for full functionality)
- **Recommended**: Conda/Miniconda for dependency management

### Installation Methods

#### 🐍 Option 1: Conda (Recommended for Windows)

1. Clone the repository:
   ```bash
   git clone https://github.com/jetta18/ArctosGuiPython.git
   cd ArctosGuiPython
   ```

2. Create and activate the Conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate arctos-env
   ```

> 💡 Don't have Conda? Install Anaconda (https://www.anaconda.com/download)

#### 🛠️ Option 2: Manual Python Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jetta18/ArctosGuiPython.git
   cd ArctosGuiPython
   ```

2. Create and activate a virtual environment:
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Pinocchio manually:
   [Pinocchio Installation Guide](https://stack-of-tasks.github.io/pinocchio/download.html)

## 🔌 Hardware Setup

### CAN Interface Configuration

> **Note:** The following steps are only necessary for Linux systems. On Windows, CAN interface setup is not required. By default, COM5 is used as the CAN interface on Windows.

1. Navigate to the scripts directory:
   ```bash
   cd ~/ArctosGuiPython/scripts
   ```

2. Run the setup script (requires sudo):
   ```bash
   sudo ./setup_canable.sh
   ```

## 🖥️ Running the Application

1. Activate your environment:
   ```bash
   # For Conda
   conda activate arctos-env
   
   # For venv
   # Linux/macOS: source venv/bin/activate
   # Windows: .\venv\Scripts\activate
   ```

2. Start the application:
   ```bash
   cd ~/ArctosGuiPython/src
   python main.py
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:8080
   ```

## 📁 Project Structure

```
ArctosGuiPython/
├── src/                    # Source code
│   ├── core/              # Core robot functionality
│   ├── config/            # User preferences and settings
│   ├── models/            # 3D models and URDF files
│   ├── services/          # Robot services and communication
│   ├── components/        # UI components
│   ├── pages/             # Application pages
│   ├── programs/          # Stored motion programs
│   └── utils/             # Utility functions
│   └── main.py            # Application entry point
├── assets/                # Static assets (icon.png, etc.)
├── scripts/               # System scripts (setup_canable.sh)
├── docs/                  # Documentation (ARCHITECTURE.md, etc.)
├── requirements.txt       # Python dependencies
└── environment.yml        # Conda environment
```

## 📝 License

This project is licensed under [MIT License](LICENSE).

**Note:** The included MKS-Servo CAN library is licensed under the GNU General Public License v3.0.

## 👥 Credits

- **MKS-Servo CAN library** - For servo control
- **NiceGUI** - Modern web interface
- **Pinocchio** - Robotics calculations
- **MeshCat** - 3D visualization

## 🔗 Useful Links

- [Documentation](https://arctosrobotics.com/docs/)
- [Assembly Manuals](https://arctosrobotics.com/#Assembly)
- [CAD Files](https://arctosrobotics.com/#Assembly)
