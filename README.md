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



## 🛠️ Setup & Installation

### Prerequisites
- **Python 3.8+** (if not using Docker)
- **CAN interface** for robot communication
- **Arctos Robot hardware** (for full functionality)
- **[Optional] Conda** (recommended for robotics users)
- **[Optional] Docker & Docker Compose** (recommended for easiest setup)

---

## 🚦 Quick Start Table

| Method                 | Recommended For         | Requirements                | Notes                                   |
|------------------------|------------------------|-----------------------------|-----------------------------------------|
| Docker (Quick Start)   | Most users             | Docker, Docker Compose      | Easiest, no Python setup needed         |
| Conda Environment      | Robotics users         | Conda/Miniconda             | Handles most dependencies automatically |
| Manual Python + venv   | Advanced users         | Python, pip, venv           | Manual dependency management            |

---

## 🔧 Installation Methods

### 🐳 1. Docker (Recommended for Most Users)

**No need to install Python or dependencies manually.**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jetta18/ArctosGuiPython.git
   cd ArctosGuiPython
   ```
2. **Build and run with Docker Compose:**
   ```bash
   # Build the GUI and visualization server
   docker compose -f docker/docker-compose.yml build
   # Run the GUI and visualization server
   docker compose -f docker/docker-compose.yml up
   ```
   - The GUI will be available at [http://localhost:8080](http://localhost:8080)
   - The MeshCat visualizer will be at [http://localhost:7000/static/](http://localhost:7000/static/)

> **Tip:** Make sure Docker and Docker Compose are installed and running.

**(Optional) Use a prebuilt Docker image**  
*Not available yet. When available:*
```bash
docker run --rm -p 8080:8080 -p 7000:7000 yourusername/arctos-gui:latest
```
Replace `yourusername/arctos-gui:latest` with the actual image name.

---

### 🅱️ 2. Conda-based Installation (Recommended for Robotics)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jetta18/ArctosGuiPython.git
   cd ArctosGuiPython
   ```
2. **Create the Conda environment:**
   ```bash
   conda env create -f environment.yml
   ```
3. **Activate the environment:**
   ```bash
   conda activate arctos-env
   ```
4. **Start the application:**
   ```bash
   python src/main.py
   ```

> **Tip:** If you don’t have Conda, install [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

---

### 🅰️ 3. Manual Python Installation (Advanced/Custom)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jetta18/ArctosGuiPython.git
   cd ArctosGuiPython
   ```
2. **(Recommended) Create and activate a virtual environment:**
   - Linux/macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Windows:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Install Pinocchio manually** ([instructions](https://stack-of-tasks.github.io/pinocchio/download.html))

---

### ⚡ Next Steps: CAN Interface Setup & Running

- **Set up the CAN interface:**
  ```bash
  cd scripts
  sudo ./setup_canable.sh
  ```
- **Run the application:**
  ```bash
  cd src
  python main.py
  ```
- **Open your browser:** [http://localhost:8080](http://localhost:8080)

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
