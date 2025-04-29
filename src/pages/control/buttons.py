from nicegui import ui
from core import homing
import utils.utils as utils

def home_button(Arctos):
    """Create a button to home the robot.

    Args:
        Arctos: The main robot control interface or object.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    return ui.button("\U0001F3E0 Move to Home Pose", on_click=lambda: homing.move_to_zero_pose(Arctos)) \
        .tooltip("Send robot to predefined 'home' configuration") \
        .classes('bg-purple-500 text-white px-4 py-2 rounded-lg shadow hover:bg-purple-700')

def sleep_button(Arctos):
    """Create a button to put the robot into sleep mode.

    Args:
        Arctos: The main robot control interface or object.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    return ui.button("\U0001F634 Move to Sleep Pose", on_click=lambda: homing.move_to_sleep_pose(Arctos)) \
        .tooltip("Send robot to safe resting position (sleep pose)") \
        .classes('bg-gray-500 text-white px-4 py-2 rounded-lg shadow hover:bg-gray-700')

def reset_to_zero_button(robot):
    """Create a button to reset the robot's joints to zero.

    Args:
        robot: The robot instance to reset.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    return ui.button("Reset to Zero", on_click=lambda: utils.reset_to_zero_position(robot)) \
        .tooltip("Move all joints to 0° without using homing or encoders") \
        .classes('bg-gray-700 text-white px-4 py-2 rounded-lg')

def start_movement_button(robot, Arctos, settings_manager):
    """Create a button to start robot movement.

    Args:
        robot: The robot instance to move.
        Arctos: The main robot control interface or object.
        settings_manager: The settings manager for user preferences and state.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    return ui.button("Start Movement", on_click=lambda: utils.run_move_can(robot, Arctos, settings_manager)) \
        .tooltip("Execute the currently set joint angles on the physical robot") \
        .classes('bg-red-500 text-white px-4 py-2 rounded-lg')

def emergency_stop_button(Arctos):
    """Create a prominently styled EMERGENCY STOP button for the GUI.

    Args:
        Arctos: The main robot control interface or object.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    return ui.button(
        "\U0001F6D1 EMERGENCY STOP",
        on_click=lambda: Arctos.safe_emergency_stop()
    ).tooltip(
        "Emergency stop: If any motor is above 1000 RPM, decelerate rapidly; otherwise, stop instantly. Use ONLY in case of emergency!"
    ).classes('bg-gray-700 text-white px-4 py-2 rounded-lg')
