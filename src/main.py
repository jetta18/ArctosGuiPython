"""
Main entry point for the Arctos Robot GUI application.

This script initializes the core components of the Arctos Robot control interface, 
registers the web pages, configures global settings, and starts the NiceGUI 
web server. It demonstrates the integration of various modules, including 
robot control, path planning, settings management, and web UI components.
"""

from nicegui import ui
from pages import home, mks_config
from pages.settings import set_page
from pages.control import ctrl_page
from components.menu import create_menu
from core.ArctosController import ArctosController
from core.PathPlanner import PathPlanner
from core.CanBusManager import CanBusManager
from core.ArctosPinocchio import ArctosPinocchioRobot  # Import for robot kinematics
from utils.settings_manager import SettingsManager  # Import to manage settings
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize core logic components and settings
settings_manager = SettingsManager()  # Initialize the settings manager

logger.info("⚙️ Settings Manager initialized")

try:
    can_bus_manager = CanBusManager()
    logger.info("CAN Bus initialized")
    Arctos = ArctosController(can_bus_manager=can_bus_manager, settings_manager=settings_manager)  # Initialize the robot controller
    logger.info("🤖 Arctos Controller initialized")
    robot = ArctosPinocchioRobot()  # Initialize the robot kinematics
    logger.info("🦾 Arctos Pinocchio Robot initialized")
    planner = PathPlanner()  # Initialize the path planner
    logger.info("🗺️ Path Planner initialized")
except Exception as e:
    logger.error(f"❌ Error initializing core components: {e}")
    raise


# Apply global settings like theme (Dark/Light Mode)
if settings_manager.get("theme") == "Dark":
    ui.dark_mode().enable()  # Enable dark mode
    logger.info("🌑 Dark mode enabled")
else:
    ui.dark_mode().disable()  # Disable dark mode
    logger.info("🌕 Light mode enabled")

# Define app pages with injected dependencies and create them
# The UI pages are defined here and are created when the app is started.
@ui.page('/')
def home_page():
    """Creates and displays the home page."""
    home.create()

@ui.page('/control')
def control_page():
    """Creates and displays the robot control page.
    This page allows to control the robot.
    """
    create_menu()
    ctrl_page.create(Arctos, robot, planner, settings_manager)

@ui.page('/settings')
def settings_page():
    create_menu()
    set_page.create(settings_manager, arctos=Arctos)

@ui.page('/mks')
def mks_page():
    """Creates and displays the MKS servo configuration page.
    This page allows to configure the mks servos.
    """
    create_menu()
    mks_config.create(Arctos, settings_manager)


# Launch the NiceGUI application
ui.run(title="Arctos Robot Control", reload=False, show=False)
logger.info("🚀 Arctos Robot GUI application started")
