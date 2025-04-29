from nicegui import ui

def live_joint_states(settings_manager):
    """Render the live joint states UI section if enabled in settings.

    Args:
        settings_manager: The settings manager object controlling feature toggles.

    Returns:
        list: List of NiceGUI label objects for each joint (or [None]*6 if disabled).
    """
    if not settings_manager.get("enable_live_joint_updates", True):
        return [None]*6
    with ui.card().classes('w-full bg-gradient-to-br from-blue-50 to-cyan-100 border border-blue-300 rounded-2xl shadow-lg p-3 mb-3'):
        with ui.row().classes('items-center mb-2'):
            ui.icon('sensors').classes('text-2xl text-blue-700 mr-2')
            ui.label("Live Joint-States").classes('text-2xl font-bold text-blue-900 tracking-wide')
        with ui.grid(columns=6).classes('w-full'):
            joint_positions_encoder = [
                ui.label(f"J{i+1}: --.--°")
                .classes(
                    'text-base text-center font-mono text-blue-900 bg-white rounded-lg px-3 py-2 border border-blue-200 shadow-sm'
                )
                for i in range(6)
            ]
    return joint_positions_encoder
