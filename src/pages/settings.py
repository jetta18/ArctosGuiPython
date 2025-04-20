"""
File: settings.py

This module constructs the Settings page for configuring various aspects of the robot UI,
including theme, live updates, joint parameters, and a Homing Calibration Wizard.
"""
from nicegui import ui
from nicegui.elements.switch import Switch
from typing import Any, Dict, List

from utils.settings_manager import SettingsManager
from core.homing import ZERO_POSITIONS, HOMING_SEQUENCE


def create(settings_manager: SettingsManager, arctos: Any) -> None:
    """
    Construct the Settings page with general options and a
    wizard for homing offset calibration.

    Args:
        settings_manager: SettingsManager instance for persistent settings.
        arctos: Robot controller instance for servo commands.

    Returns:
        None
    """
    settings: Dict[str, Any] = settings_manager.all()

    # Apply theme
    if settings.get("theme") == "Dark":
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()

    # Main container
    with ui.column().classes("p-6 max-w-3xl mx-auto gap-6"):
        ui.label("⚙️ Arctos Settings").classes("text-4xl font-bold mb-2")

        # --- Theme Toggle ---
        with ui.card().classes("w-full shadow-md p-4"):
            ui.label("🌗 Theme").classes("text-xl font-semibold mb-1")
            ui.toggle(
                ["Light", "Dark"],
                value=settings.get("theme", "Light"),
                on_change=lambda e: (
                    settings_manager.set("theme", e.value),
                    ui.dark_mode().enable() if e.value == "Dark" else ui.dark_mode().disable()
                )
            )

        # --- Live Joint Updates ---
        with ui.card().classes("w-full shadow-md p-4"):
            ui.label("📡 Live Joint Updates").classes("text-xl font-semibold mb-1")
            toggle: Switch = ui.switch(
                "Enable Live Updates",
                value=settings.get("enable_live_joint_updates", True)
            )
            toggle.on_value_change(lambda e:
                (ui.notify("Live Updates Enabled" if e.value else "Live Updates Disabled"),
                 settings_manager.set("enable_live_joint_updates", e.value))
            )

        # --- Joint Rotation Directions ---
        with ui.expansion("🌀 Joint Rotation Directions", icon="swap_vert", value=False).classes("shadow-md"):
            directions: Dict[int, int] = settings.get("joint_directions", {i: 1 for i in range(6)})
            for i in range(6):
                current = "Inverted" if directions.get(i, 1) == -1 else "Normal"
                ui.select(
                    ["Normal", "Inverted"],
                    value=current,
                    label=f"Joint {i+1}",
                    on_change=lambda e, idx=i: (
                        settings_manager.set(
                            "joint_directions",
                            {**settings_manager.get("joint_directions", {j: 1 for j in range(6)}), idx: (-1 if e.value == "Inverted" else 1)}
                        ),
                        ui.notify(f"Joint {idx+1} set to {e.value}")
                    )
                ).classes("w-64")

        # --- Joint Speeds ---
        with ui.expansion("⚡ Joint Speeds (RPM)", icon="speed", value=False).classes("shadow-md"):
            speeds: Dict[int, int] = settings.get("joint_speeds", {i: 500 for i in range(6)})
            for i in range(6):
                ui.number(
                    label=f"Joint {i+1}",
                    value=speeds.get(i, 500),
                    min=0, max=3000, step=10,
                    on_change=lambda e, idx=i: (
                        settings_manager.set(
                            "joint_speeds",
                            {**settings_manager.get("joint_speeds", {}), idx: int(e.value or 500)}
                        ),
                        ui.notify(f"Speed J{idx+1} set to {int(e.value)} RPM")
                    )
                ).classes("w-40")

        # --- Joint Accelerations ---
        with ui.expansion("🚀 Joint Accelerations", icon="bolt", value=False).classes("shadow-md"):
            accels: Dict[int, int] = settings.get("joint_accelerations", {i: 150 for i in range(6)})
            for i in range(6):
                ui.number(
                    label=f"Joint {i+1}",
                    value=accels.get(i, 150),
                    min=0, max=255, step=5,
                    on_change=lambda e, idx=i: (
                        settings_manager.set(
                            "joint_accelerations",
                            {**settings_manager.get("joint_accelerations", {}), idx: int(e.value or 150)}
                        ),
                        ui.notify(f"Acceleration J{idx+1} set to {int(e.value)}")
                    )
                ).classes("w-40")


        # --- Homing Offsets Display ---
        with ui.card().classes("w-full shadow-md p-4"):
            ui.label("📐 Homing Offsets").classes("text-xl font-semibold mb-1")
            offsets: Dict[int, int] = settings_manager.get("homing_offsets", {i: 0 for i in range(6)})
            rows: List[Dict[str, Any]] = [
                {"Axis": f"J{axis}", "Offset": offsets.get(axis-1, 0)}
                for axis in HOMING_SEQUENCE
            ]
            ui.table(
                columns=[{"name": "Axis", "label": "Axis"}, {"name": "Offset", "label": "Offset (units)"}],
                rows=rows
            ).classes("w-full mb-6")

        # --- Homing Calibration Wizard ---
        with ui.card().classes("w-full shadow-md p-4 border-blue-400"):
            ui.label("🛠 Homing Calibration Wizard").classes("text-xl font-semibold mb-2")

            # 1) Axis selection
            axis_select = ui.select(
                options=[f"Axis {i}" for i in HOMING_SEQUENCE],
                label="Select Axis",
                value=f"Axis {HOMING_SEQUENCE[0]}"
            ).classes("w-1/2")

            # 2) Home to physical limit (resets encoder to zero)
            home_button = ui.button('Home Selected Axis').classes("bg-blue-500 text-white mt-4")
            homing_status = ui.label(" ").classes("mt-2 text-sm text-blue-700")

            # 3) Manual stepwise adjustment
            step_input = ui.number(
                label='Step Size (units)',
                value=500,
                min=1,
                step=50
            ).classes("w-40 mt-2")
            move_negative = ui.button('< Move -').classes("bg-gray-200 px-3 py-1 rounded-lg mt-2 mr-2")
            move_positive = ui.button('Move + >').classes("bg-gray-200 px-3 py-1 rounded-lg mt-2")
            current_pos_label = ui.label("Current Position: --").classes("mt-2 font-mono")

            # 4) Save offset at desired position
            save_button = ui.button('Save Offset').classes("bg-green-500 text-white mt-4")

            def on_home_click() -> None:
                """
                Perform homing on selected axis to reset encoder to zero.
                """
                idx = int(axis_select.value.split()[-1]) - 1
                arctos.servos[idx].b_go_home()
                arctos.wait_for_motors_to_stop()
                homing_status.text = f'Axis {idx+1} homed: encoder reset to 0'
                current_pos_label.text = 'Current Position: 0'

            def on_move_click(direction: int) -> None:
                """
                Move selected axis stepwise in given direction.

                Args:
                    direction: -1 for negative, +1 for positive movement.
                """
                idx = int(axis_select.value.split()[-1]) - 1
                step = int(step_input.value or 0)
                raw_step = step * direction
                # Retrieve speed/accel settings
                speed = settings_manager.get('joint_speeds', {}).get(idx, 500)
                accel = settings_manager.get('joint_accelerations', {}).get(idx, 150)
                arctos.servos[idx].run_motor_relative_motion_by_axis(speed, accel, raw_step)
                arctos.wait_for_motors_to_stop()
                # Read current encoder value
                raw_val = arctos.servos[idx].read_encoder_value_addition() or 0
                current_pos_label.text = f'Current Position: {raw_val}'

            def on_save_click() -> None:
                """
                Save current encoder value as new homing offset.
                """
                idx = int(axis_select.value.split()[-1]) - 1
                raw_val = arctos.servos[idx].read_encoder_value_addition() or 0
                offsets_dict = settings_manager.get('homing_offsets', {i: 0 for i in range(6)})
                offsets_dict[idx] = raw_val
                settings_manager.set('homing_offsets', offsets_dict)
                ui.notify(f'Offset for Axis {idx+1} saved: {raw_val}', color='positive')

            # Bind event handlers
            home_button.on('click', on_home_click)
            move_negative.on('click', lambda: on_move_click(-1))
            move_positive.on('click', lambda: on_move_click(1))
            save_button.on('click', on_save_click)

        # --- Reset All Settings ---
        ui.button(
            "🔄 Reset All Settings",
            on_click=lambda: (
                [settings_manager.set(k, v) for k, v in {
                    "theme": "Light",
                    "enable_live_joint_updates": True,
                    "joint_directions": {i: 1 for i in range(6)},
                    "joint_speeds": {i: 500 for i in range(6)},
                    "joint_accelerations": {i: 150 for i in range(6)},
                    "homing_offsets": {i: 0 for i in range(6)}
                }.items()],
                ui.notify("All settings have been reset!", color="primary")
            )
        ).classes("bg-red-500 text-white px-4 py-2 rounded-lg self-start")

