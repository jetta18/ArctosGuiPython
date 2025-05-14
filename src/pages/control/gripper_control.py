from nicegui import ui
from utils.utils import open_gripper, close_gripper

def gripper_control(Arctos):
    """Create the gripper control expansion for the robot.

    Args:
        Arctos: The main robot control interface or object.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    expansion_common = (
        "w-full bg-white/90 backdrop-blur-md border border-blue-200 "
        "rounded-md shadow-xl p-0 transition-all duration-300 "
        "hover:shadow-2xl"
    )
    with ui.expansion('Gripper Control', icon='precision_manufacturing', value=False).classes(expansion_common).props('expand-icon="expand_more"'):
        ui.label("Control the gripper's movement.").classes('text-gray-600 mb-2')
        with ui.row().classes('justify-center gap-4'):
            ui.button("Open Gripper", on_click=lambda: open_gripper(Arctos)) \
                .tooltip("Send command to open the robot gripper") \
                .classes('bg-yellow-500 text-white px-4 py-2 rounded-lg shadow hover:bg-yellow-600')
            ui.button("Close Gripper", on_click=lambda: close_gripper(Arctos)) \
                .tooltip("Send command to close the robot gripper") \
                .classes('bg-orange-500 text-white px-4 py-2 rounded-lg shadow hover:bg-orange-600')
