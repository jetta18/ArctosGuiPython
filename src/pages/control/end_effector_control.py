from nicegui import ui

def end_effector_control(robot):
    """Create the end-effector control expansion for the robot.

    Args:
        robot: The robot instance whose end-effector is being controlled.

    Returns:
        tuple: Tuple of (position_labels, orientation_labels) as NiceGUI label objects.
    """
    with ui.expansion('End-Effector Control', icon='open_with', value=False).classes('w-full bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
        with ui.row().classes('items-center mb-2'):
            ui.icon('open_with').classes('text-2xl text-purple-700 mr-2')
            ui.label('End-Effector Control').classes('text-2xl font-bold text-purple-900 tracking-wide')
        ui.separator().classes('my-2')
        with ui.row().classes('gap-2 mb-4 flex-wrap items-center justify-center'):
            ee_position_labels = {}
            for axis in ["X", "Y", "Z"]:
                ee_position_labels[axis] = ui.label(f"{axis}: 0.00 m").classes('px-2 py-1 rounded bg-blue-100 text-blue-900 font-mono')
            ui.label('|').classes('mx-2 text-gray-400')
            ee_orientation_labels = {}
            for axis in ["Roll", "Pitch", "Yaw"]:
                ee_orientation_labels[axis] = ui.label(f"{axis}: 0.00°").classes('px-2 py-1 rounded bg-purple-100 text-purple-900 font-mono')
    return ee_position_labels, ee_orientation_labels
