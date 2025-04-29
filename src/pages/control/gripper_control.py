from nicegui import ui

def gripper_control(Arctos):
    """Create the gripper control expansion for the robot.

    Args:
        Arctos: The main robot control interface or object.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    with ui.expansion('Gripper Control', icon='precision_manufacturing', value=False).classes('w-full bg-gradient-to-br from-yellow-50 to-orange-100 border border-yellow-200 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
        ui.label("Control the gripper's movement.").classes('text-gray-600 mb-2')
        with ui.row().classes('justify-center gap-4'):
            ui.button("Open Gripper", on_click=lambda: __import__('utils.utils').utils.open_gripper(Arctos)) \
                .tooltip("Send command to open the robot gripper") \
                .classes('bg-yellow-500 text-white px-4 py-2 rounded-lg shadow hover:bg-yellow-600')
            ui.button("Close Gripper", on_click=lambda: __import__('utils.utils').utils.close_gripper(Arctos)) \
                .tooltip("Send command to close the robot gripper") \
                .classes('bg-orange-500 text-white px-4 py-2 rounded-lg shadow hover:bg-orange-600')
