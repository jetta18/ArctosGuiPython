from nicegui import ui
from pages.settings.handler_factories import make_joint_handler, make_ratio_handler

def joints_tab(settings_manager, arctos, settings, open_ratio_wizard):
    """
    Build the Joints tab UI for settings (directions, speeds, accelerations, gear ratios).

    Args:
        settings_manager: The settings manager instance.
        arctos: The robot controller instance.
        settings: The current settings dictionary.
        open_ratio_wizard (Callable): Function to open the gear-ratio wizard dialog.

    Returns:
        None
    """
    from typing import Any, Dict
    with ui.row().classes("flex-wrap gap-4"):
        for title, key, default, label_fmt, tooltip in [
            ("Joint Directions", "joint_directions", {i: 1 for i in range(6)}, "Joint {}", "Set joint direction (Normal/Inverted)"),
            ("Joint Speeds", "joint_speeds", {i: 500 for i in range(6)}, "J{}", "Set max speed in RPM"),
            ("Joint Accelerations", "joint_accelerations", {i: 150 for i in range(6)}, "J{}", "Set max acceleration")
        ]:
            with ui.card().classes("p-4 grow md:max-w-[30%]"):
                with ui.row().classes("items-center mb-2 gap-1"):
                    ui.label(title).classes("text-xl font-semibold")
                    if title == "Joint Directions":
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            with ui.tooltip().classes("text-body2 text-left"):
                                ui.html(
                                    """
                                    <strong>Joint Directions:</strong> <br>
                                    Set each joint's rotation direction:<br>
                                    <ul style='margin: 0 0 0 1em; padding: 0; list-style: disc;'>
                                      <li><b>Normal</b>: Default direction (matches positive command).</li>
                                      <li><b>Inverted</b>: Reverses joint movement (use if robot moves opposite to command).</li>
                                    </ul>
                                    <em>Change only if your robot's wiring or mechanics require it.</em>
                                    """
                                )
                    elif title == "Joint Speeds":
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            with ui.tooltip().classes("text-body2 text-left"):
                                ui.html(
                                    """
                                    <strong>Joint Speeds:</strong> <br>
                                    Set the rotation speed for each joint (in RPM).<br>
                                    <ul style='margin: 0 0 0 1em; padding: 0; list-style: disc;'>
                                      <li>Higher values = faster motion, but may reduce precision or safety.</li>
                                      <li>Lower values = slower, safer, more precise movement.</li>
                                      <li>Adjust only if needed for your application or hardware limits.</li>
                                    </ul>
                                    <em>Default is 500 RPM for all joints.</em>
                                    """
                                )
                    elif title == "Joint Accelerations":
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            with ui.tooltip().classes("text-body2 text-left"):
                                ui.html(
                                    """
                                    <strong>Joint Acceleration:</strong> <br>
                                    Set the acceleration for each joint (in encoder units/s²).<br>
                                    <ul style='margin: 0 0 0 1em; padding: 0; list-style: disc;'>
                                      <li>Higher values = joints reach speed faster, but may cause jerky motion.</li>
                                      <li>Lower values = smoother, more controlled starts and stops.</li>
                                      <li>Adjust for your robot's mass and application needs.</li>
                                    </ul>
                                    <em>Default is 150 for all joints.</em>
                                    """
                                )
                    else:
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            ui.tooltip(tooltip)
                vals: Dict[int, int] = settings.get(key, default)
                with ui.row().classes("flex-wrap gap-2"):
                    for i in range(6):
                        widget = ui.select if title == "Joint Directions" else ui.number
                        val_i = vals.get(i)
                        init_val = (
                            "Inverted" if title == "Joint Directions" and val_i == -1 else (val_i if title != "Joint Directions" else "Normal")
                        )
                        params = {"label": label_fmt.format(i + 1), "value": init_val}
                        if widget is ui.select:
                            params["options"] = ["Normal", "Inverted"]
                        else:
                            params.update({
                                "min": 0,
                                "max": 3000 if key == "joint_speeds" else 255,
                                "step": 10 if key == "joint_speeds" else 5
                            })
                        widget(**params,
                               on_change=make_joint_handler(settings_manager, key, i, default, title))\
                            .classes("w-24 sm:w-28 md:w-32")
        # Gear Ratios Card
        with ui.card().classes("p-4 grow md:max-w-[30%]"):
            with ui.row().classes("items-center mb-2 gap-1"):
                ui.label("Gear Ratios").classes("text-xl font-semibold")
                with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                    with ui.tooltip().classes("text-body2 text-left"):
                        ui.html(
                            """
                            <strong>Gear Ratios:</strong> <br>
                            Each value defines the gear reduction for a joint (motor turns : output turns).<br>
                            <ul style='margin: 0 0 0 1em; padding: 0; list-style: disc;'>
                              <li>Adjust only if you have physically changed the robot or calibrated with the wizard.</li>
                              <li>Use the <b>Gear-Ratio Wizard</b> for assisted calibration.</li>
                              <li>Typical values: J1 (13.5), J2/J3 (150), J4 (48), J5/J6 (~34).</li>
                            </ul>
                            <em>Incorrect values may cause inaccurate movement.</em>
                            """
                        )
            ratios = settings_manager.get("gear_ratios", [13.5, 150, 150, 48, 67.82 / 2, 67.82 / 2])
            with ui.row().classes("flex-wrap gap-2"):
                for i in range(6):
                    ui.number(
                        label=f"J{i + 1}",
                        value=ratios[i],
                        min=1, step=0.1,
                        on_change=make_ratio_handler(settings_manager, arctos, i)
                    ).classes("w-24 sm:w-28 md:w-32")
                ui.button("⚙️ Gear-Ratio Wizard", on_click=open_ratio_wizard).props("color=secondary").classes("mt-2")