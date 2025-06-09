from nicegui import ui
from .speed_scale import speed_scale
from .joint_control import joint_control
from .end_effector_control import end_effector_control
from .gripper_control import gripper_control
from .path_planning import path_planning
from .buttons import home_button, sleep_button, reset_to_zero_button, start_movement_button, emergency_stop_button
from .visualization_keyboard import visualization_keyboard
from .live_joint_states import live_joint_states
from utils import utils

def create(Arctos, robot, planner, settings_manager):
    """Assembles the complete control page by composing modular sections.

    Args:
        Arctos: The main robot control interface or object.
        robot: The robot instance for which the control page is being generated.
        planner: The path planning module or object.
        settings_manager: The settings manager for user preferences and state.

    Returns:
        None. The function builds the UI directly using NiceGUI components.

    Raises:
        None.
    """
    """
    Assemble the complete control page by composing modular sections.
    """
    # Theme
    if settings_manager.get("theme") == "Dark":
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()
    #ui.label("Control Page").classes('text-3xl font-bold text-left mt-2 mb-2 px-2')

    # --- Control Buttons at Top ---
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

    # Speed scale section
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
        ui.notify(f'Speed scale set to {int(val*100)} %', color='positive')

    joint_positions_encoder = live_joint_states(settings_manager)

    with ui.row().classes('w-full h-[calc(100vh-60px)] gap-2 items-stretch'):
        with ui.column().classes('flex-2 min-w-0 gap-2 items-stretch w-[550px]'):
            speed_scale(settings_manager, apply_speed)
            joint_positions = joint_control(robot)
            ee_position_labels, ee_orientation_labels = end_effector_control(robot)
            gripper_control(Arctos)
            path_planning(planner, robot, Arctos, settings_manager)

        with ui.column().classes('flex-1 min-w-0 gap-2 items-stretch h-full'):
            # Setup keyboard controller
            step_size_slider = None
            visualization_keyboard(robot, Arctos, step_size_slider, settings_manager)
    # Timers
    ui.timer(0.25, lambda: utils.update_joint_states(robot, joint_positions))
    ui.timer(0.25, lambda: utils.live_update_ee_postion(robot, ee_position_labels))
    ui.timer(0.25, lambda: utils.live_update_ee_orientation(robot, ee_orientation_labels))
    if settings_manager.get("enable_live_joint_updates", True):
        ui.timer(0.2, lambda: utils.threaded_initialize_current_joint_states(robot, Arctos, settings_manager))
        ui.timer(0.2, lambda: utils.update_joint_states_encoder(robot, joint_positions_encoder))
