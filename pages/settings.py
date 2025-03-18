from nicegui import ui

def create():
    """
    Settings page for general configurations.
    
    This page provides UI elements for modifying application settings, such as enabling or disabling dark mode.
    """
    with ui.column().classes('p-4'):
        ui.label("⚙️ Settings").classes('text-3xl font-bold')
        
        dark_mode = ui.dark_mode()
        dark_mode_switch = ui.switch("Dark Mode")
        dark_mode_switch.on_value_change(lambda e: dark_mode.enable() if e.value else dark_mode.disable())
