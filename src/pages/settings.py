from nicegui import ui
from nicegui.elements.toggle import Toggle
from nicegui.elements.switch import Switch
from typing import Any


def create(settings_manager: Any) -> None:
    """
    Construct the settings page for configuring various aspects of the robot UI and behavior.

    This function builds a user interface using NiceGUI, where users can:
    - Switch between light and dark theme
    - Enable or disable live joint updates
    - Configure per-joint direction, speed (RPM), and acceleration
    - Reset all settings to defaults

    Args:
        settings_manager (Any): An instance managing the persistent settings, providing `get` and `set` methods.

    Returns:
        None
    """
    settings = settings_manager.all()

    # Set theme
    if settings.get("theme") == "Dark":
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()

    with ui.column().classes("p-6 max-w-3xl mx-auto gap-6"):
        ui.label("⚙️ Arctos Settings").classes("text-4xl font-bold mb-2")

        # --- Theme Toggle ---
        with ui.card().classes("w-full shadow-md p-4"):
            ui.label("🌗 Theme").classes("text-xl font-semibold mb-1")
            ui.toggle(["Light", "Dark"], value=settings.get("theme", "Light"),
                      on_change=lambda e: (
                          settings_manager.set("theme", e.value),
                          ui.dark_mode().enable() if e.value == "Dark" else ui.dark_mode().disable()
                      ))

        # --- Live Joint Updates ---
        with ui.card().classes("w-full shadow-md p-4"):
            ui.label("📡 Live Joint Updates").classes("text-xl font-semibold mb-1")
            toggle: Switch = ui.switch("Enable Live Updates",
                                       value=settings.get("enable_live_joint_updates", True))
            toggle.on_value_change(lambda e:
                (ui.notify("Live Updates Enabled" if e.value else "Disabled"),
                 settings_manager.set("enable_live_joint_updates", e.value)))

        # --- Joint Rotation Directions ---
        with ui.expansion("🌀 Joint Rotation Directions", icon="swap_vert", value=False).classes("shadow-md"):
            directions = settings.get("joint_directions", {i: 1 for i in range(6)})
            for i in range(6):
                current = "Inverted" if directions.get(i, 1) == -1 else "Normal"
                ui.select(["Normal", "Inverted"],
                          value=current,
                          label=f"Joint {i + 1}",
                          on_change=lambda e, index=i: (
                              settings_manager.set("joint_directions", {
                                  **settings_manager.get("joint_directions", {i: 1 for i in range(6)}),
                                  index: -1 if e.value == "Inverted" else 1
                              }),
                              ui.notify(f"Joint {index + 1} set to {e.value}")
                          )).classes("w-64")

        # --- Joint Speeds ---
        with ui.expansion("⚡ Joint Speeds (RPM)", icon="speed", value=False).classes("shadow-md"):
            speeds = settings.get("joint_speeds", {i: 500 for i in range(6)})
            for i in range(6):
                ui.number(
                    label=f"Joint {i + 1}",
                    value=speeds.get(i, 500),
                    min=0, max=3000, step=10,
                    on_change=lambda e, idx=i: (
                        settings_manager.set("joint_speeds", {
                            **settings_manager.get("joint_speeds", {}),
                            idx: int(e.value or 500)
                        }),
                        ui.notify(f"Speed J{idx + 1} set to {int(e.value)} RPM")
                    )
                ).classes("w-40")

        # --- Joint Accelerations ---
        with ui.expansion("🚀 Joint Accelerations", icon="bolt", value=False).classes("shadow-md"):
            accels = settings.get("joint_accelerations", {i: 150 for i in range(6)})
            for i in range(6):
                ui.number(
                    label=f"Joint {i + 1}",
                    value=accels.get(i, 150),
                    min=0, max=255, step=5,
                    on_change=lambda e, idx=i: (
                        settings_manager.set("joint_accelerations", {
                            **settings_manager.get("joint_accelerations", {}),
                            idx: int(e.value or 150)
                        }),
                        ui.notify(f"Acceleration J{idx + 1} set to {int(e.value)}")
                    )
                ).classes("w-40")

        # --- Reset All Settings ---
        ui.button("🔄 Reset All Settings", on_click=lambda: (
            [settings_manager.set(k, v) for k, v in {
                "theme": "Light",
                "enable_live_joint_updates": True,
                "joint_directions": {i: 1 for i in range(6)},
                "joint_speeds": {i: 500 for i in range(6)},
                "joint_accelerations": {i: 150 for i in range(6)}
            }.items()],
            ui.notify("All settings have been reset!", color="primary")
        )).classes("bg-red-500 text-white px-4 py-2 rounded-lg self-start")