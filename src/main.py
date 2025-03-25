from nicegui import ui
from pages import home, control, settings, mks_config
from components.menu import create_menu
from core.ArctosController import ArctosController
from core.PathPlanner import PathPlanner
from core.ArctosPinocchio import ArctosPinocchioRobot


Arctos = ArctosController()
robot = ArctosPinocchioRobot()
planner = PathPlanner()


# Seiten registrieren
@ui.page('/')
def home_page():
    #create_menu()
    home.create()

@ui.page('/control')
def control_page():
    create_menu()
    control.create(Arctos, robot, planner)

@ui.page('/settings')
def settings_page():
    create_menu()
    settings.create()

@ui.page('/mks')
def mks_page():
    create_menu()
    mks_config.create(Arctos)


# Anwendung starten
ui.run(title="Arctos Robot Control", reload=False, show=False )
