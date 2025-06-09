from nicegui import ui

def live_joint_states(settings_manager):
    """Render the live joint states UI section if enabled in settings.

    Args:
        settings_manager: The settings manager object controlling feature toggles.

    Returns:
        list: List of NiceGUI label objects for each joint (or [None]*6 if disabled).
    """
    if not settings_manager.get("enable_live_joint_updates", True):
        return [None] * 6
        
    with ui.card().classes('fixed bottom-4 right-4 z-50 bg-gray-400/90 backdrop-blur-sm border border-gray-450/80 rounded-xl shadow-xl p-2 flex flex-col items-center justify-center').style('width: 530px; height: 100px; min-width: 530px; min-height: 100px; max-width: 530px; max-height: 100px; overflow: hidden;'):
        with ui.row().classes('items-center gap-3 w-full px-2').style('width: 100%; height: 100%;'):
            ui.icon('sensors', size='sm').classes('text-blue-600')
            joint_positions_encoder = []
            for i in range(6):
                with ui.column().classes('items-center').style('width: 64px; min-width: 64px; max-width: 64px;'):
                    ui.label(f'J{i+1}').classes('text-xs text-blue-800 -mb-1').style('width: 100%; text-align: center;')
                    joint_positions_encoder.append(
                        ui.label('--.--°').classes(
                            'text-sm font-mono text-blue-800 bg-gray-50/80 rounded px-2 py-1 min-w-[65px] max-w-[65px] text-center border border-gray-200 shadow-sm'
                        ).style('width: 70px; display: inline-block; text-align: center;')
                    )

    return joint_positions_encoder
