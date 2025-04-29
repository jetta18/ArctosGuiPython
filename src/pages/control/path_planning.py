from nicegui import ui

def path_planning(planner, robot, Arctos, settings_manager):
    """Create the path planning expansion for the robot.

    Args:
        planner: The path planning module or object.
        robot: The robot instance for which paths are being planned.
        Arctos: The main robot control interface or object.
        settings_manager: The settings manager for user preferences and state.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    with ui.expansion('Path Planning', icon='map', value=False).classes('w-full bg-gradient-to-br from-green-50 to-blue-100 border border-green-200 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
        with ui.row().classes('items-center mb-1'):
            ui.icon('map').classes('text-2xl text-green-700 mr-2')
            ui.label('Path Planning').classes('text-xl font-bold text-green-900 tracking-wide')
        ui.separator().classes('my-1')
        ui.label('Manage and execute path‑planning tasks.')\
            .classes('text-gray-600 mb-2')
        with ui.tabs().classes('mb-2') as tabs:
            tab_poses   = ui.tab('Saved Poses',    icon='list_alt')
            tab_actions = ui.tab('Program Actions', icon='play_circle')
        with ui.tab_panels(tabs, value=tab_poses):
            with ui.tab_panel(tab_poses):
                pose_container = ui.column().classes('w-full gap-y-2')
                __import__('utils.utils').utils.update_pose_table(planner, robot, pose_container)
                ui.label('Tip: Click the red × next to a pose to delete it.')\
                    .classes('text-xs text-gray-400 mt-1')
            with ui.tab_panel(tab_actions):
                ui.label('Program Actions').classes('text-lg font-semibold text-green-900 mb-2')
                with ui.row().classes('flex-wrap gap-3 mb-3'):
                    ui.button('Save Pose', icon='add_location_alt',
                        on_click=lambda: (
                            __import__('utils.utils').utils.save_pose(planner, robot),
                            __import__('utils.utils').utils.update_pose_table(planner, robot, pose_container)
                        ))\
                        .classes('bg-blue-700 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-900')
                    ui.button('Load Program', icon='folder_open',
                        on_click=lambda: __import__('utils.utils').utils.load_program(planner, pose_container, robot))\
                        .classes('bg-green-700 text-white px-4 py-2 rounded-lg shadow hover:bg-green-900')
                    ui.button('Save Program', icon='save',
                        on_click=lambda: __import__('utils.utils').utils.save_program(planner))\
                        .classes('bg-indigo-700 text-white px-4 py-2 rounded-lg shadow hover:bg-indigo-900')
                    ui.button('Execute Program', icon='play_arrow',
                        on_click=lambda: __import__('utils.utils').utils.execute_path(planner, robot, Arctos, settings_manager))\
                        .classes('bg-red-700 text-white px-4 py-2 rounded-lg shadow hover:bg-red-900')
                ui.label('Tip: Save your program before executing for best results.')\
                    .classes('text-xs text-gray-400 mt-1')
