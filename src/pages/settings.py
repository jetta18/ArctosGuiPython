"""
Module: settings.py

This module defines the settings page for the Arctos Robot GUI, allowing users to configure
various settings such as theme, live joint updates, and joint rotation directions.
"""

from nicegui import ui

def create(settings_manager):
    """
    Creates the settings page for general configurations.

    This function constructs the settings page, which includes UI elements to modify
    various aspects of the application's behavior. It reads and updates settings via
    the provided `settings_manager`.

    Args:
        settings_manager: An object that provides methods to get and set application settings.

    Returns:
        None
    """
    # Retrieve all current settings from the settings manager
    settings = settings_manager.all()

    # Set the initial theme based on the 'theme' setting
    if settings.get("theme") == "Dark":
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()

    # Create the main column for the settings page
    with ui.column().classes('p-4'):
        # Page header
        ui.label("⚙️ Settings").classes('text-3xl font-bold')

        # Theme Setting
        with ui.row():
            # Theme label
            ui.label("🌗 Theme")
            # Theme toggle
            ui.toggle(["Light", "Dark"], value=settings["theme"], 
                      on_change=lambda e: (
                          # Update the theme setting
                          settings_manager.set("theme", e.value),
                          # Enable or disable dark mode based on the selected theme
                          ui.dark_mode().enable() if e.value == "Dark" else ui.dark_mode().disable()
                      ))

        # Live Joint Updates Setting
        with ui.row():
            # Label for the live joint updates toggle
            ui.label("📡 Enable Live Joint Updates")
            # Toggle switch for enabling/disabling live joint updates
            live_toggle = ui.switch(value=settings.get("enable_live_joint_updates", True))
            # Action when the toggle changes
            live_toggle.on_value_change(lambda e: (
                ui.notify("Live Joint Updates Enabled" if e.value else "Disabled"),
                settings_manager.set("enable_live_joint_updates", e.value)
            ))

        # Joint Direction Settings
        with ui.expansion("🌀 Joint Rotation Directions", icon="swap_vert", value=False):
            # Get the current joint directions from the settings
            directions = settings.get("joint_directions", {i: 1 for i in range(6)})
            # Create a select for each joint
            for i in range(6):
                # Determine if the joint direction is inverted or normal
                current = "Inverted" if directions.get(i, 1) == -1 else "Normal"
                # Select box for the direction
                ui.select(["Normal", "Inverted"],
                          value=current,
                          label=f"Joint {i+1} Direction",
                          on_change=lambda e, index=i: (
                              # Update the joint direction setting
                              settings_manager.set("joint_directions", {
                                  # Merge the updated direction with the existing directions
                                  **settings_manager.get("joint_directions", {i: 1 for i in range(6)}),
                                  index: -1 if e.value == "Inverted" else 1
                              }),
                              # Notify the user about the change
                              ui.notify(f"Joint {index+1} direction set to {e.value}")
                          )).classes("w-64")

        # Reset Settings Button
        ui.button("🔄 Reset Settings", on_click=lambda: (
            # Reset settings to default values
            [settings_manager.set(k, v) for k, v in {
                # Default Settings
                "theme": "Light",
                "language": "English",
                "enable_live_joint_updates": True,
                "joint_directions": {i: 1 for i in range(6)}
            }.items()],
            # Notify the user that the settings have been reset
            ui.notify("Settings have been reset!")
        )).classes('bg-red-500 text-white px-4 py-2 rounded-lg')