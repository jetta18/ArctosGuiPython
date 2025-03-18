from nicegui import ui
from pages import home, control, settings, mks_config
from components.menu import create_menu

# Seiten registrieren
@ui.page('/')
def home_page():
    #create_menu()
    home.create()

@ui.page('/control')
def control_page():
    create_menu()
    control.create()

@ui.page('/settings')
def settings_page():
    create_menu()
    settings.create()

@ui.page('/mks')
def mks_page():
    create_menu()
    mks_config.create()

# Anwendung starten
ui.run(reload=False)
