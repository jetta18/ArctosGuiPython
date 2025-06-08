"""handler_factories.py

Handler factory functions for the Arctos settings page.
Provides event handler generators for UI controls.
"""

from nicegui import ui
from typing import Any, Dict

def make_joint_handler(settings_manager, k: str, idx: int, default: Dict[int, int], title: str):
    """Create a handler for joint settings (directions, speeds, accelerations).

    Args:
        settings_manager: The settings manager instance.
        k (str): The key for the setting (e.g., 'joint_directions').
        idx (int): Index of the joint (0-based).
        default (Dict[int, int]): Default values for the setting.
        title (str): Human-readable name for notifications.

    Returns:
        Callable: Handler function for UI events.

    Raises:
        ValueError: If an invalid value is passed for a numeric field.
    """
    def _handler(e):
        if k == "joint_directions":
            # Accept both string and int values
            if e.value == "Inverted":
                raw_val = -1
            elif e.value == "Normal":
                raw_val = 1
            else:
                try:
                    raw_val = int(e.value)
                except Exception:
                    raw_val = 1
        else:
            try:
                raw_val = int(e.value) if e.value is not None else 0
            except (ValueError, TypeError):
                raw_val = 0
                ui.notify(f"Invalid value for {title.lower()}, using 0", type='warning')
        settings_manager.set(k, {**settings_manager.get(k, default), idx: raw_val})
        ui.notify(f"{title.split()[1]} {idx + 1} set to {e.value}")
    return _handler

def make_ratio_handler(settings_manager, arctos, idx: int):
    """Create a handler for updating a gear ratio.

    Args:
        settings_manager: The settings manager instance.
        arctos: The robot controller instance.
        idx (int): Index of the joint (0-based).

    Returns:
        Callable: Handler function for gear ratio input events.

    Raises:
        ValueError: If the value cannot be converted to float.
    """
    def _handler(e):
        ratios = list(settings_manager.get("gear_ratios", []))
        ratios[idx] = float(e.value or 0)
        settings_manager.set("gear_ratios", ratios)
        arctos.set_gear_ratios(ratios, settings_manager.get("joint_directions", {i: 1 for i in range(6)}))
        ui.notify(f"Gear ratio J{idx + 1} set to {e.value}")
    return _handler

def make_homing_handlers(settings_manager, arctos, axis_sel, step_in, pos_lbl):
    """Create handlers for the homing calibration wizard (home, move, save).

    Args:
        settings_manager: The settings manager instance.
        arctos: The robot controller instance.
        axis_sel: UI select element for axis choice.
        step_in: UI number input for step size.
        pos_lbl: UI label for displaying position.

    Returns:
        Tuple[Callable, Callable, Callable]:
            - on_home: Handler for homing the joint.
            - on_move: Handler for jogging the joint.
            - on_save: Handler for saving the encoder offset.

    Raises:
        Exception: If hardware access fails.
    """
    def on_home():
        idx = int(axis_sel.value.split()[-1]) - 1
        arctos.servos[idx].b_go_home()
        pos_lbl.text = "Position: 0"
    def on_move(dir_: int):
        idx = int(axis_sel.value.split()[-1]) - 1
        raw = int(step_in.value or 0) * dir_
        sp = settings_manager.get("joint_speeds", {}).get(idx, 500)
        ac = settings_manager.get("joint_accelerations", {}).get(idx, 150)
        arctos.servos[idx].run_motor_relative_motion_by_axis(sp, ac, raw)
        val = arctos.servos[idx].read_encoder_value_addition() or 0
        pos_lbl.text = f"Position: {val}"
    def on_save():
        idx = int(axis_sel.value.split()[-1]) - 1
        val = arctos.servos[idx].read_encoder_value_addition() or 0
        d = settings_manager.get("homing_offsets", {})
        d[idx] = val
        settings_manager.set("homing_offsets", d)
        ui.notify(f"Saved offset J{idx + 1}: {val}")
    return on_home, on_move, on_save
