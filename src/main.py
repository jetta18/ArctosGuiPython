# File: main.py

from nicegui import ui
from pages import home, control, settings, mks_config
from components.menu import create_menu
from core.ArctosController import ArctosController
from core.PathPlanner import PathPlanner
from core.ArctosPinocchio import ArctosPinocchioRobot
from utils.settings_manager import SettingsManager  # ✅ NEW: Import settings manager

# Initialize core logic components
settings_manager = SettingsManager()  # ✅ Initialize global settings handler
Arctos = ArctosController(settings_manager=settings_manager)
robot = ArctosPinocchioRobot()
planner = PathPlanner()

# Apply global settings like theme
if settings_manager.get("theme") == "Dark":
    ui.dark_mode().enable()
else:
    ui.dark_mode().disable()

# Define app pages with injected dependencies
@ui.page('/')
def home_page():
    home.create()

@ui.page('/control')
def control_page():
    create_menu()
    control.create(Arctos, robot, planner, settings_manager)  # ✅ Pass settings

@ui.page('/settings')
def settings_page():
    create_menu()
    settings.create(settings_manager)  # ✅ Pass settings

@ui.page('/mks')
def mks_page():
    create_menu()
    mks_config.create(Arctos)  # ✅ Pass settings

# Launch application
ui.run(title="Arctos Robot Control", reload=False, show=False )
