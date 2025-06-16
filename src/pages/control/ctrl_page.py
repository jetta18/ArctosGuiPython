from nicegui import ui
import numpy as np
from nicegui.events import KeyEventArguments
from .speed_scale import speed_scale
from .joint_control import joint_control
from .end_effector_control import end_effector_control
from .gripper_control import gripper_control
from .path_planning import path_planning
from .buttons import home_button, sleep_button, reset_to_zero_button, start_movement_button, emergency_stop_button
from .visualization_keyboard import visualization_keyboard
from .live_joint_states import live_joint_states
from utils import utils

def create(Arctos, robot, planner, settings_manager, trajectory_planner):
    """Assembles the complete control page by composing modular sections.

    Args:
        Arctos: The main robot control interface or object.
        robot: The robot instance for which the control page is being generated.
        planner: The path planning module or object.
        settings_manager: The settings manager for user preferences and state.
        trajectory_planner: The trajectory planner module or object.

    Returns:
        None. The function builds the UI directly using NiceGUI components.

    Raises:
        None.
    """
    # Theme
    if settings_manager.get("theme") == "Dark":
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()

    # Speed scale function
    def apply_speed(val):
        try:
            val = float(val)
        except (TypeError, ValueError):
            ui.notify('Please enter a valid number for speed scale', color='negative')
            return
        if not (0.1 <= val <= 2.0):
            ui.notify('Please enter a value between 0.1 and 2.0', color='negative')
            return
        utils.set_speed_scale(val)
        settings_manager.set('speed_scale', val)
        ui.notify(f'Speed scale set to {int(val*100)} %', color='positive')
        
    # Initialize joint positions for encoder
    joint_positions_encoder = live_joint_states(settings_manager)
    
    # Create a container for the entire page
    with ui.element('div').classes('w-full h-screen fixed inset-0'):
        # 1. Background iframe with full pointer events
        ui.html(f'''<iframe src="{robot.meshcat_url}" style="width: 100%; height: 100%; border: none;"></iframe>''')\
                .classes('absolute inset-0 w-full h-full')

        # 2. Top control buttons (sticky header) - positioned below menu bar
        with ui.element('div').classes('absolute top-[56px] left-0 right-0 z-10'):
            with ui.card().classes(
                'w-full flex flex-col items-center bg-white/90 backdrop-blur-md border border-blue-200 rounded-md shadow-xl p-4 mb-1'
            ).style(
                'position:sticky;top:56px;z-index:50;opacity:0.5;transition:opacity 0.25s;backdrop-filter:blur(8px);'
            ).on('mouseenter', lambda e: e.sender.style('position:sticky;top:56px;z-index:50;opacity:1.0;transition:opacity 0.25s;backdrop-filter:blur(8px);')) \
             .on('mouseleave', lambda e: e.sender.style('position:sticky;top:56px;z-index:50;opacity:0.5;transition:opacity 0.25s;backdrop-filter:blur(8px);')):
                with ui.row().classes('gap-4 mb-1'):
                    start_movement_button(robot, Arctos, settings_manager)
                    reset_to_zero_button(robot)
                    home_button(Arctos, settings_manager)
                    sleep_button(Arctos, settings_manager)
                    emergency_stop_button(Arctos)
        
        # 3. Left side control panel (floating)
        with ui.element('div').classes('absolute left-4 top-40 bottom-4 z-20').style('width: 550px;'):
            # Create a scrollable container for controls
            with ui.card().classes('bg-white/10 backdrop-blur-sm border border-blue-200 rounded-md shadow-lg p-4 max-h-[calc(100vh-12rem)]'):
                with ui.column().classes('w-full gap-4 overflow-y-auto'):
                    # Speed scale section
                    speed_scale(settings_manager, apply_speed)
                    
                    # Joint control section
                    joint_positions = joint_control(robot)
                    
                    # End effector control section
                    ee_position_labels, ee_orientation_labels = end_effector_control(robot)
                    
                    # Gripper control section
                    gripper_control(Arctos, robot)
                    
                    # Path planning section
                    path_planning(planner, robot, Arctos, settings_manager)
                    
                    # Keyboard section
                    step_size_slider = None
                    visualization_keyboard(robot, Arctos, step_size_slider, settings_manager)
        
    # Timers
    ui.timer(0.25, lambda: utils.update_joint_states(robot, joint_positions))
    ui.timer(0.25, lambda: utils.live_update_ee_postion(robot, ee_position_labels))
    ui.timer(0.25, lambda: utils.live_update_ee_orientation(robot, ee_orientation_labels))
    if settings_manager.get("enable_live_joint_updates", True):
        # A single timer now handles both fetching hardware data and updating the UI for maximum efficiency.
        ui.timer(0.02, lambda: utils.update_robot_joint_states_async(robot, Arctos, settings_manager, joint_positions_encoder))
