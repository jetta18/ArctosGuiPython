# File: settings.py

from nicegui import ui

def create(settings_manager):
    """
    Settings page for general configurations.
    Reads and updates settings via the global SettingsManager.
    """
    settings = settings_manager.all()

    if settings.get("theme") == "Dark":
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()

    with ui.column().classes('p-4'):
        ui.label("⚙️ Settings").classes('text-3xl font-bold')

        # Theme
        with ui.row():
            ui.label("🌗 Theme")
            ui.toggle(["Light", "Dark"], value=settings["theme"], 
                      on_change=lambda e: (
                          settings_manager.set("theme", e.value),
                          ui.dark_mode().enable() if e.value == "Dark" else ui.dark_mode().disable()
                      ))

        # ✅ NEW: Toggle for Live Joint State Updates
        with ui.row():
            ui.label("📡 Enable Live Joint Updates")
            live_toggle = ui.switch(value=settings.get("enable_live_joint_updates", True))
            live_toggle.on_value_change(lambda e: (
                ui.notify("Live Joint Updates Enabled" if e.value else "Disabled"),
                settings_manager.set("enable_live_joint_updates", e.value)
            ))

        # Joint Direction Settings
        with ui.expansion("🌀 Joint Rotation Directions", icon="swap_vert", value=False):
            directions = settings.get("joint_directions", {i: 1 for i in range(6)})
            for i in range(6):
                current = "Inverted" if directions.get(i, 1) == -1 else "Normal"
                ui.select(["Normal", "Inverted"],
                          value=current,
                          label=f"Joint {i+1} Direction",
                          on_change=lambda e, index=i: (
                              settings_manager.set("joint_directions", {
                                  **settings_manager.get("joint_directions", {i: 1 for i in range(6)}),
                                  index: -1 if e.value == "Inverted" else 1
                              }),
                              ui.notify(f"Joint {index+1} direction set to {e.value}")
                          )).classes("w-64")

        # Reset
        ui.button("🔄 Reset Settings", on_click=lambda: (
            [settings_manager.set(k, v) for k, v in {
                "theme": "Light",
                "language": "English",
                "enable_live_joint_updates": True,
                "joint_directions": {i: 1 for i in range(6)}
            }.items()],
            ui.notify("Settings have been reset!")
        )).classes('bg-red-500 text-white px-4 py-2 rounded-lg')