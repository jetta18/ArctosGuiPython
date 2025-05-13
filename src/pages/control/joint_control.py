from nicegui import ui

def joint_control(robot):
    """Create the joint control UI expansion for the robot.

    Args:
        robot: The robot instance whose joints are being controlled.

    Returns:
        list: List of NiceGUI label objects for each joint.
    """
    with ui.expansion('Joint Control', icon='360', value=False).classes('w-full bg-gradient-to-br from-blue-50 to-cyan-100 border border-blue-300 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300 mb-3').props('expand-icon="expand_more"'):
        ui.label("View and set the joint angles.").classes('text-gray-600 mb-4')
        with ui.grid(columns=3).classes('gap-4 w-full mb-2'):
            joint_positions = [
                ui.label(f"Joint {i+1}: 0.0°").classes('text-sm w-full text-center bg-white border border-blue-200 rounded-lg py-2 shadow-sm font-mono text-blue-900') for i in range(6)
            ]
        with ui.grid(columns=3).classes('gap-4 w-full mb-2'):
            new_joint_inputs = [ui.number(label=f"Joint {i+1} (°)").classes('w-full border-blue-200 rounded-lg') for i in range(6)]
        ui.button("Set Joint Angles", on_click=lambda: __import__('utils.utils').utils.set_joint_angles_from_gui(robot, new_joint_inputs)) \
            .tooltip("Send entered joint angles to the robot using forward kinematics") \
            .classes('bg-blue-600 text-white w-full mt-2 py-2 rounded-lg shadow hover:bg-blue-800')
    return joint_positions
