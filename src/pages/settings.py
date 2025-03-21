from nicegui import ui
import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '../config/user_preferences.json')

# Load settings from JSON file
try:
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {
        "theme": "Light",
        "language": "English",
        "ui_color_theme": "Blue",
        "max_fps": 30,
        "auto_update_saved_poses": False
    }

# Save settings to JSON file
def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def create():
    """
    Settings page for general configurations.
    """

    with ui.column().classes('p-4'):
        ui.label("⚙️ Settings").classes('text-3xl font-bold')

        # Dark Mode Toggle
        with ui.row():
            ui.label("🌗 Theme")
            theme_toggle = ui.toggle(["Light", "Dark"], value=settings["theme"], on_change=lambda e: (ui.dark_mode().enable() if e.value == "Dark" else ui.dark_mode().disable(), settings.update({"theme": e.value}), save_settings()))

        # Language Selection
        with ui.row():
            ui.label("🌍 Language")
            language_toggle = ui.toggle(["English", "Deutsch"], value=settings["language"], on_change=lambda e: (ui.notify(f"Language set to: {e.value}"), settings.update({"language": e.value}), save_settings()))

        # UI Color Theme
        with ui.row():
            ui.label("🎨 UI Color Theme")
            ui.select(["Blue", "Green", "Red", "Gray"], value=settings["ui_color_theme"], on_change=lambda e: (ui.notify(f"Color set to: {e.value}"), settings.update({"ui_color_theme": e.value}), save_settings()))

        # FPS Slider
        with ui.row():
            ui.label("⚡ Performance Mode")
            ui.slider(min=1, max=60, value=settings["max_fps"], step=1, on_change=lambda e: (ui.notify(f"Max FPS set to: {e.value}"), settings.update({"max_fps": e.value}), save_settings()))

        # Auto-Update Saved Poses
        with ui.row():
            ui.label("🔄 Auto-Update Saved Poses")
            auto_update = ui.switch(value=settings["auto_update_saved_poses"])
            auto_update.on_value_change(lambda e: (ui.notify("Auto-Update Enabled" if e.value else "Auto-Update Disabled"), settings.update({"auto_update_saved_poses": e.value}), save_settings()))

        # Reset Button
        ui.button("🔄 Reset Settings", on_click=lambda: (settings.update({"theme": "Light", "language": "English", "ui_color_theme": "Blue", "max_fps": 30, "auto_update_saved_poses": False}), save_settings(), ui.notify("Settings have been reset!"))).classes('bg-red-500 text-white px-4 py-2 rounded-lg')
