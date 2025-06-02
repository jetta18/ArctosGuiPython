from nicegui import ui
from nicegui.elements.switch import Switch

def general_tab(settings_manager, settings):
    """
    Build the General tab UI for settings (theme and live joint updates).

    Args:
        settings_manager: The settings manager instance.
        settings: The current settings dictionary.

    Returns:
        None
    """
    with ui.row().classes("w-full"):
        with ui.card().classes("p-4 mb-4"):
            with ui.row().classes("items-center mb-2"):
                ui.label("Appearance").classes("text-xl font-semibold")
                with ui.icon("info").classes("text-blue-500 cursor-pointer ml-1"):
                    with ui.tooltip().classes("text-body2 text-left"):
                        ui.html(
                            """
                            <strong>Theme:</strong><br>
                            Switch between <b>Light</b> and <b>Dark</b> UI appearance.<br>
                            <ul style='margin:0 0 0 1em; padding:0; list-style: disc;'>
                                <li><b>Light:</b> Bright, daylight style for well-lit environments.</li>
                                <li><b>Dark:</b> Dimmed interface for low-light or night use.</li>
                            </ul>
                            <em>This setting affects the entire application interface.</em>
                            """
                        )
            ui.toggle(["Light", "Dark"],
                    value=settings.get("theme", "Light"),
                    on_change=lambda e: (
                        settings_manager.set("theme", e.value),
                        ui.dark_mode().enable() if e.value == "Dark" else ui.dark_mode().disable(),
                        ui.notify(f"Theme set to {e.value}")
                    )
                    )
        with ui.card().classes("p-4 mb-4"):
            with ui.row().classes("items-center mb-2"):
                ui.label("Live Joint Updates").classes("text-xl font-semibold")
                with ui.icon("info").classes("text-blue-500 cursor-pointer ml-1"):
                    with ui.tooltip().classes("text-body2 text-left"):
                        ui.html(
                            """
                            <strong>Live Joint Updates:</strong><br>
                            Enable or disable <b>real-time display</b> of joint encoder readings.<br>
                            <ul style='margin:0 0 0 1em; padding:0; list-style: disc;'>
                                <li>When enabled, the UI shows the actual joint angles as measured by the robot's encoders.</li>
                                <li>When disabled, only commanded or simulated values are shown.</li>
                            </ul>
                            <em>Recommended for monitoring the physical robot's state during operation.</em>
                            """
                        )
            live_switch: Switch = ui.switch(
                "Enable live joint angle updates",
                value=settings.get("enable_live_joint_updates", True)
            )
            live_switch.on_value_change(lambda e: (
                settings_manager.set("enable_live_joint_updates", e.value),
                ui.notify("Live updates enabled" if e.value else "Live updates disabled")
            ))

        with ui.card().classes("p-4 mb-4"):
            with ui.row().classes("items-center mb-2"):
                ui.label("Keyboard Control Target").classes("text-xl font-semibold")
                with ui.icon("info").classes("text-blue-500 cursor-pointer ml-1"):
                    with ui.tooltip().classes("text-body2 text-left"):
                        ui.html(
                            """
                            <strong>Keyboard Control Target:</strong><br>
                            <b>Send keyboard control commands to:</b>
                            <ul style='margin:0 0 0 1em; padding:0; list-style: disc;'>
                                <li><b>Enabled:</b> Keyboard controls move the <b>physical robot hardware</b> in real time.</li>
                                <li><b>Disabled:</b> Keyboard controls only affect the 3D simulation/visualization.</li>
                            </ul>
                            <em>Use caution: Enabling this will cause real robot movement in response to keyboard input.</em>
                            """
                        )
            send_to_robot_switch: Switch = ui.switch(
                "Send keyboard control to physical robot",
                value=settings.get("keyboard_send_to_robot", False)
            )
            send_to_robot_switch.on_value_change(lambda e: (
                settings_manager.set("keyboard_send_to_robot", e.value),
                ui.notify("Keyboard control will {}move the physical robot".format('' if e.value else 'not '))
            ))

        with ui.card().classes("p-4 mb-4"):
            with ui.row().classes("items-center mb-2 gap-1"):
                ui.label("Axis Control Mode").classes("text-xl font-semibold")
                with ui.icon("info").classes("text-blue-500 cursor-pointer ml-1"):
                    with ui.tooltip().classes("text-body2 text-left"):
                        ui.html(
                            """
                            <strong>Axis Control Mode:</strong><br>
                            <b>Choose how axes 5 (B) and 6 (C) are controlled:</b>
                            <ul style='margin:0 0 0 1em; padding:0; list-style: disc;'>
                                <li><b>Independent:</b> Axes 5 and 6 move independently (default).</li>
                                <li><b>Coupled B/C:</b> Axes 5 and 6 are coupled as B and C axes (legacy mode).</li>
                            </ul>
                            <em>Change this only if you have the standard robot version with coupled B/C axes.</em>
                            """
                        )
            coupled_switch = ui.switch(
                "Use coupled B/C axis mode (legacy)",
                value=settings.get("coupled_axis_mode", False)
            )
            def on_coupled_mode_change(e):
                settings_manager.set("coupled_axis_mode", e.value)
                ui.notify(f"Coupled B/C axis mode {'enabled' if e.value else 'disabled'}. Reloading settings...")
                ui.navigate.to('/settings')  # Reload the settings page
                
            coupled_switch.on_value_change(on_coupled_mode_change)
