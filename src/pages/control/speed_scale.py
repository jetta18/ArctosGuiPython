from nicegui import ui

def speed_scale(settings_manager, apply_speed):
    """Create the speed scale UI section for adjusting robot speed.

    Args:
        settings_manager: The settings manager for user preferences and state.
        apply_speed (Callable): Function to apply the new speed value.

    Returns:
        None. The function builds the UI directly using NiceGUI components.
    """
    expansion_common = 'w-full bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-2xl shadow-lg p-3 hover:shadow-xl transition-all duration-300'
    with ui.expansion('Speed Scale', icon='speed', value=False).classes(expansion_common).props('expand-icon="expand_more" id=speed-scale-section'):
        speed_val = settings_manager.get('speed_scale', 1.0)
        with ui.row().classes('items-center gap-3'):
            speed_slider = ui.slider(
                min=0.1, max=2.0, value=speed_val, step=0.01
            ).props('dense label-always color=primary').classes('w-52 hover:scale-105 transition-transform')
            speed_display = ui.label(f"{int(speed_val*100)} %") \
                .classes('font-mono text-lg text-blue-800 ml-2')
            speed_input = ui.number(
                value=speed_val, min=0.1, max=2.0, step=0.01, format='%.2f'
            ).classes('w-16 ml-2 border-blue-300 rounded')
            ui.button('Apply', on_click=lambda: apply_speed(speed_slider.value)) \
                .props('color=primary dense').classes('ml-3 px-4 py-1 rounded-lg text-white font-semibold shadow hover:bg-blue-700 transition-colors')
            with ui.icon('info').classes('text-blue-500 cursor-pointer'):
                with ui.tooltip().classes('text-body2 text-left'):
                    ui.html(
                        """
                        <strong>Speed Scale:</strong><br>
                        Scales the overall robot movement speed.<br>
                        <ul style='margin:0 0 0 1em; padding:0; list-style: disc;'>
                            <li>1.0 = 100 % (default speed)</li>
                            <li>Lower: slower, safer motion</li>
                            <li>Higher: faster, less precise</li>
                        </ul>
                        Use the slider or enter a value.
                        """
                    )
        def safe_percent(val):
            try:
                num = float(val)
                return f"{int(round(num * 100))} %"
            except Exception:
                return "-- %"
        speed_slider.on('update:model-value', lambda e: [
            speed_input.set_value(e.args),
            speed_display.set_text(safe_percent(e.args))
        ])
        speed_input.on('update:model-value', lambda e: [
            speed_slider.set_value(e.args),
            speed_display.set_text(safe_percent(e.args))
        ])
