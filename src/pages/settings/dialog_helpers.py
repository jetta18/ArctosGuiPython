"""dialog_helpers.py

Dialog creation utilities for the Arctos settings page.
Provides helpers for settings reset and gear-ratio wizard dialogs.
"""

from nicegui import ui

def create_gear_ratio_wizard(settings_manager, arctos, get_current_ratio):
    """Create the Gear-Ratio Wizard dialog and return its open function.

    Args:
        settings_manager: Instance managing persistent settings.
        arctos: The main robot controller object (must provide encoder_resolution and servos).
        get_current_ratio: Function taking axis index and returning the current gear ratio.

    Returns:
        Callable: Function to open the gear-ratio wizard dialog.

    Raises:
        Exception: If dialog creation fails due to missing dependencies or UI errors.
    """
    with ui.dialog() as dlg_ratio, ui.card().classes("p-4 w-[26rem]"):
        with ui.row().classes("items-center mb-2 gap-1"):
            ui.label("Gear-Ratio Wizard").classes("text-xl font-semibold")
            with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                with ui.tooltip().classes("text-body2 text-left"):
                    ui.html(
                        """
                        <strong>How to use the Gear-Ratio Wizard:</strong><br>
                        1. ⚙️ <strong>Select</strong> the joint axis you want to calibrate.<br>
                        2. ⟳ <strong>Rotate</strong> – click 'Rotate' to move the joint by 90°.<br>
                        3. 📏 <strong>Measure</strong> – use a protractor or angle tool to measure the actual angle moved.<br>
                        4. 📝 <strong>Enter</strong> the measured angle in degrees.<br>
                        5. 💾 <strong>Save</strong> – update the gear ratio for more accurate motion.<br><br>
                        <em>This process helps calibrate your robot's joint ratios for precise movement.</em>
                        """
                    )
        ui.label("Rotate ~90 ° by current ratio → measure → save")
        axis_sel_wz = ui.select([f"Axis {i+1}" for i in range(6)], value="Axis 1", label="Axis").classes("w-full")
        with ui.row().classes("gap-3 mt-4"):
            btn_rotate = ui.button("Rotate 90 °").props("color=primary")
            angle_in   = ui.number(label="Measured °", min=0.1, step=0.1).classes("w-32")
            btn_save   = ui.button("Save").props("color=positive")
        with ui.row():
            info_lbl = ui.label("").classes("mt-3 font-mono")
        def _rotate():
            """Rotate the selected axis by approximately 90 degrees."""
            idx = int(axis_sel_wz.value.split()[-1]) - 1
            r   = get_current_ratio(idx)
            ticks = int(r * arctos.encoder_resolution / 4)
            arctos.servos[idx].run_motor_relative_motion_by_axis(300, 150, ticks)
            ui.notify(f"Axis rotated (~90° based on {r:.3f}). Measure angle.", color="info")
        btn_rotate.on("click", lambda _: _rotate())
        def _save():
            """Save the measured angle and update the gear ratio."""
            idx  = int(axis_sel_wz.value.split()[-1]) - 1
            meas = angle_in.value
            if not meas:
                ui.notify("Enter measured angle!", color="negative"); return
            r_cur = get_current_ratio(idx)
            r_new = r_cur * 90 / float(meas)
            ratios = list(settings_manager.get("gear_ratios", []))
            ratios[idx] = r_new
            settings_manager.set("gear_ratios", ratios)
            if hasattr(arctos, "set_gear_ratios"):
                arctos.set_gear_ratios(ratios, settings_manager.get("joint_directions", {i: 1 for i in range(6)}))
            info_lbl.text = f"Axis {idx+1}: {r_cur:.3f} → {r_new:.3f}  (saved)"
            ui.notify(f"Gear ratio J{idx+1} updated to {r_new:.3f}", color="positive")
        btn_save.on("click", lambda _: _save())
    def open_ratio_wizard():
        """Open the gear-ratio wizard dialog."""
        dlg_ratio.open()
    return open_ratio_wizard

def create_reset_dialog(settings_manager):
    """Create the reset settings dialog and return its open function.

    Args:
        settings_manager: Instance managing persistent settings.

    Returns:
        Callable: Function to open the reset dialog.

    Raises:
        Exception: If dialog creation fails due to UI errors.
    """
    with ui.dialog() as dlg, ui.card().classes("p-4"):
        ui.label("Confirm Reset").classes("text-xl font-semibold mb-2")
        ui.label("Are you sure you want to reset all settings? This cannot be undone.")
        with ui.row().classes("justify-end mt-4 gap-2"):
            ui.button("Cancel", on_click=dlg.close).props('color=negative').classes('text-white')
            ui.button("Confirm").props('color=positive').classes('text-white').on('click', lambda: (
                [settings_manager.set(k, v) for k, v in {
                    "theme": "Light",
                    "joint_speeds": {i: 500 for i in range(6)},
                    'joint_acceleration': {i: 150 for i in range(6)},
                    "joint_directions": {i: 1 for i in range(6)},
                    "speed_scale": 1.0,
                    "enable_live_joint_updates": False,
                    "homing_offsets": {i: 0 for i in range(6)},
                    "gear_ratios": [13.5, 150, 150, 48, 33.91, 33.91],
                }.items()],
                ui.notify("Settings reset to defaults."), dlg.close()
            ))
    return dlg.open
