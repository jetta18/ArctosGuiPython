"""
ui_panels.py

UI panel builders for the Arctos settings page.
Defines functions to construct General, Joints, and Homing tab contents.
"""
from nicegui import ui
from nicegui.elements.switch import Switch
from core.homing import HOMING_SEQUENCE
from pages.settings.handler_factories import make_joint_handler, make_ratio_handler, make_homing_handlers

def general_tab(settings_manager, settings):
    """
    Build the General tab UI for settings (theme and live joint updates).

    Args:
        settings_manager: The settings manager instance.
        settings: The current settings dictionary.

    Returns:
        None
    """
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
    with ui.card().classes("p-4"):
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

    with ui.card().classes("p-4 mt-4"):
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

    with ui.card().classes("p-4 mt-4"):
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

def joints_tab(settings_manager, arctos, settings, open_ratio_wizard):
    """
    Build the Joints tab UI for settings (directions, speeds, accelerations, gear ratios).

    Args:
        settings_manager: The settings manager instance.
        arctos: The robot controller instance.
        settings: The current settings dictionary.
        open_ratio_wizard (Callable): Function to open the gear-ratio wizard dialog.

    Returns:
        None
    """
    from typing import Any, Dict
    with ui.row().classes("flex-wrap gap-4"):
        for title, key, default, label_fmt, tooltip in [
            ("Joint Directions", "joint_directions", {i: 1 for i in range(6)}, "Joint {}", "Set joint direction (Normal/Inverted)"),
            ("Joint Speeds", "joint_speeds", {i: 500 for i in range(6)}, "J{}", "Set max speed in RPM"),
            ("Joint Accelerations", "joint_accelerations", {i: 150 for i in range(6)}, "J{}", "Set max acceleration")
        ]:
            with ui.card().classes("p-4 grow md:max-w-[30%]"):
                with ui.row().classes("items-center mb-2 gap-1"):
                    ui.label(title).classes("text-xl font-semibold")
                    if title == "Joint Directions":
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            with ui.tooltip().classes("text-body2 text-left"):
                                ui.html(
                                    """
                                    <strong>Joint Directions:</strong> <br>
                                    Set each joint's rotation direction:<br>
                                    <ul style='margin: 0 0 0 1em; padding: 0; list-style: disc;'>
                                      <li><b>Normal</b>: Default direction (matches positive command).</li>
                                      <li><b>Inverted</b>: Reverses joint movement (use if robot moves opposite to command).</li>
                                    </ul>
                                    <em>Change only if your robot's wiring or mechanics require it.</em>
                                    """
                                )
                    elif title == "Joint Speeds":
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            with ui.tooltip().classes("text-body2 text-left"):
                                ui.html(
                                    """
                                    <strong>Joint Speeds:</strong> <br>
                                    Set the rotation speed for each joint (in RPM).<br>
                                    <ul style='margin: 0 0 0 1em; padding: 0; list-style: disc;'>
                                      <li>Higher values = faster motion, but may reduce precision or safety.</li>
                                      <li>Lower values = slower, safer, more precise movement.</li>
                                      <li>Adjust only if needed for your application or hardware limits.</li>
                                    </ul>
                                    <em>Default is 500 RPM for all joints.</em>
                                    """
                                )
                    elif title == "Joint Accelerations":
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            with ui.tooltip().classes("text-body2 text-left"):
                                ui.html(
                                    """
                                    <strong>Joint Acceleration:</strong> <br>
                                    Set the acceleration for each joint (in encoder units/s²).<br>
                                    <ul style='margin: 0 0 0 1em; padding: 0; list-style: disc;'>
                                      <li>Higher values = joints reach speed faster, but may cause jerky motion.</li>
                                      <li>Lower values = smoother, more controlled starts and stops.</li>
                                      <li>Adjust for your robot's mass and application needs.</li>
                                    </ul>
                                    <em>Default is 150 for all joints.</em>
                                    """
                                )
                    else:
                        with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                            ui.tooltip(tooltip)
                vals: Dict[int, int] = settings.get(key, default)
                with ui.row().classes("flex-wrap gap-2"):
                    for i in range(6):
                        widget = ui.select if title == "Joint Directions" else ui.number
                        val_i = vals.get(i)
                        init_val = (
                            "Inverted" if title == "Joint Directions" and val_i == -1 else (val_i if title != "Joint Directions" else "Normal")
                        )
                        params = {"label": label_fmt.format(i + 1), "value": init_val}
                        if widget is ui.select:
                            params["options"] = ["Normal", "Inverted"]
                        else:
                            params.update({
                                "min": 0,
                                "max": 3000 if key == "joint_speeds" else 255,
                                "step": 10 if key == "joint_speeds" else 5
                            })
                        widget(**params,
                               on_change=make_joint_handler(settings_manager, key, i, default, title))\
                            .classes("w-24 sm:w-28 md:w-32")
        # Gear Ratios Card
        with ui.card().classes("p-4 grow md:max-w-[30%]"):
            with ui.row().classes("items-center mb-2 gap-1"):
                ui.label("Gear Ratios").classes("text-xl font-semibold")
                with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                    with ui.tooltip().classes("text-body2 text-left"):
                        ui.html(
                            """
                            <strong>Gear Ratios:</strong> <br>
                            Each value defines the gear reduction for a joint (motor turns : output turns).<br>
                            <ul style='margin: 0 0 0 1em; padding: 0; list-style: disc;'>
                              <li>Adjust only if you have physically changed the robot or calibrated with the wizard.</li>
                              <li>Use the <b>Gear-Ratio Wizard</b> for assisted calibration.</li>
                              <li>Typical values: J1 (13.5), J2/J3 (150), J4 (48), J5/J6 (~34).</li>
                            </ul>
                            <em>Incorrect values may cause inaccurate movement.</em>
                            """
                        )
            ratios = settings_manager.get("gear_ratios", [13.5, 150, 150, 48, 67.82 / 2, 67.82 / 2])
            with ui.row().classes("flex-wrap gap-2"):
                for i in range(6):
                    ui.number(
                        label=f"J{i + 1}",
                        value=ratios[i],
                        min=1, step=0.1,
                        on_change=make_ratio_handler(settings_manager, arctos, i)
                    ).classes("w-24 sm:w-28 md:w-32")
                ui.button("⚙️ Gear-Ratio Wizard", on_click=open_ratio_wizard).props("color=secondary").classes("mt-2")

def homing_tab(settings_manager, arctos, settings):
    """
    Build the Homing tab UI for settings (homing offsets and calibration wizard).

    Args:
        settings_manager: The settings manager instance.
        arctos: The robot controller instance.
        settings: The current settings dictionary.

    Returns:
        None
    """
    # Get coupled mode status
    coupled_mode = settings_manager.get("coupled_axis_mode", False)
    
    # Define homing sequence based on coupled mode (1-based indexing)
    HOMING_SEQUENCE = [1, 2, 3, 4, 5, 6]  # Default to all axes (1-6)
    if coupled_mode:
        HOMING_SEQUENCE = [1, 2, 3, 4]  # Only axes 1-4 in coupled mode
        
    with ui.element('div').classes("w-full grid grid-cols-1 md:grid-cols-2 gap-4 items-start"):
        # Modern Offsets Table
        with ui.card().classes("p-4"):
            # Title row: black, bold, info icon with HTML tooltip
            with ui.row().classes("items-center mb-4"):
                ui.label("Homing Offsets").classes("text-2xl font-bold text-black dark:text-white mr-2")
                with ui.icon("info").classes("text-blue-500 cursor-pointer text-base"):
                    with ui.tooltip().classes("text-body2 text-left"):
                        tooltip_text = """
                        <strong>Homing Offsets:</strong> <br>
                        These offsets define the encoder value for each joint when homed and then moved to zero position.<br>
                        <ul style='margin:0 0 0 1em; padding:0; list-style: disc;'>
                          <li>Adjust these if your robot's zero position needs fine-tuning.</li>
                          <li>Click a value to edit and press Enter or click away to save.</li>
                        """
                        if coupled_mode:
                            tooltip_text += "<li><b>Note:</b> Axes 5 and 6 are not shown in coupled B/C axis mode.</li>"
                        tooltip_text += "</ul><em>Changes are saved immediately.</em>"
                        ui.html(tooltip_text)
            
            if coupled_mode:
                with ui.row().classes("mb-4 p-2 bg-yellow-50 dark:bg-yellow-900 rounded"):
                    ui.icon("warning").classes("text-yellow-600 dark:text-yellow-300")
                    ui.label("Coupled B/C axis mode is enabled. Only axes 1-4 are shown.").classes("text-yellow-700 dark:text-yellow-200")
            
            # Get offsets and convert from 0-based to 1-based if needed
            raw_offsets = settings_manager.get("homing_offsets", {})
            # Initialize with 0 for all axes in the current sequence
            offsets = {axis: raw_offsets.get(axis - 1, 0) for axis in HOMING_SEQUENCE}
            
            def make_offset_handler(axis):
                def handler(e):
                    # Store the value in the offsets dict with 1-based key for display
                    offsets[axis] = e.value
                    # Convert to 0-based for saving to config
                    save_offsets = {k-1: v for k, v in offsets.items() if k in HOMING_SEQUENCE}
                    settings_manager.set("homing_offsets", save_offsets)
                    ui.notify(f"Set offset for J{axis} to {e.value}")
                return handler
                
            with ui.element('table').classes("w-full border-separate border-spacing-y-2"):
                with ui.element('thead').classes("bg-blue-100 dark:bg-gray-800"):
                    with ui.element('tr'):
                        with ui.element('th').classes("px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider"):
                            ui.label("Axis").classes("text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider")
                        with ui.element('th').classes("px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider"):
                            ui.label("Offset").classes("text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider")
                with ui.element('tbody'):
                    for idx, axis in enumerate(HOMING_SEQUENCE):
                        row_classes = "hover:bg-blue-50 dark:hover:bg-gray-800 transition-colors "
                        row_classes += "bg-white dark:bg-gray-900" if idx % 2 == 0 else "bg-gray-50 dark:bg-gray-800"
                        with ui.element('tr').classes(row_classes):
                            with ui.element('td').classes("px-6 py-4 whitespace-nowrap text-base text-gray-800 dark:text-gray-100 font-mono"):
                                ui.label(f"J{axis}").classes("text-base text-gray-800 dark:text-gray-100 font-mono")
                            with ui.element('td').classes("px-6 py-4 whitespace-nowrap text-base text-blue-700 dark:text-blue-300 font-semibold font-mono"):
                                ui.number(
                                    value=offsets[axis],
                                    min=-10000000, max=10000000, step=100,
                                    on_change=make_offset_handler(axis)
                                ).props("dense")
            
            if coupled_mode:
                ui.label("Note: Only axes 1-4 are shown in coupled B/C axis mode.").classes("text-xs text-yellow-600 dark:text-yellow-400 mt-2")
            else:
                ui.label("Current zero offsets for each joint.").classes("text-xs text-gray-500 mt-2 dark:text-gray-400")
        # Calibration Wizard
        with ui.card().classes("p-4") as wizard_card:
            with ui.row().classes("items-center mb-2 gap-1"):
                ui.label("Calibration Wizard").classes("text-xl font-semibold")
                with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                    with ui.tooltip().classes("text-body2 text-left"):
                        tooltip_text = """
                        1. 🏠 <strong>Home</strong> – drive the joint to its limit switch (encoder = 0)<br>
                        2. ◀ / ▶ – jog the joint by the selected <em>Step</em> until the zero-mark aligns<br>
                        3. 💾 <strong>Save</strong> – write the current encoder count as the homing offset
                        """
                        if coupled_mode:
                            tooltip_text += "<br><br><b>Note:</b> In coupled B/C axis mode, only axes 1-4 can be calibrated."
                        ui.html(tooltip_text)
            
            if coupled_mode:
                with ui.row().classes("mb-2 p-2 bg-yellow-50 dark:bg-yellow-900 rounded w-full"):
                    ui.icon("warning").classes("text-yellow-600 dark:text-yellow-300")
                    ui.label("Coupled B/C axis mode is enabled. Only axes 1-4 are shown.").classes("text-yellow-700 dark:text-yellow-200")
            
            with ui.row().classes("gap-2 flex-wrap mb-2"):
                axis_options = [f"Axis {i}" for i in HOMING_SEQUENCE]
                axis_sel = ui.select(
                    axis_options, 
                    label="Axis", 
                    value=f"Axis {HOMING_SEQUENCE[0]}"
                ).classes("w-32")
                axis_sel.tooltip("Select the joint to calibrate.")
                
                home_btn = ui.button("🏠 Home").tooltip("Drive joint to limit switch (zero encoder).")
                save_btn = ui.button("💾 Save").tooltip("Save current encoder value as zero offset.")
                
                # No need to disable in coupled mode, just showing axes 1-4
            
            with ui.row().classes("gap-2 flex-wrap mb-2 items-center"):
                ui.label("Step:").classes("w-12")
                step_in = ui.number(label=None, value=100, min=1, step=1).classes("w-20")
                step_in.tooltip("Incremental step size for manual adjustment.")
                
                dec_btn = ui.button("◀").tooltip("Move joint negative by step.")
                inc_btn = ui.button("▶").tooltip("Move joint positive by step.")
                
                # No need to disable in coupled mode, just showing axes 1-4
            
            pos_lbl = ui.label("Position: --").classes("mt-2 font-mono")
            
            # Always enable handlers, but only show axes 1-4 in coupled mode
            on_home, on_move, on_save = make_homing_handlers(settings_manager, arctos, axis_sel, step_in, pos_lbl)
            home_btn.on('click', lambda _: on_home())
            dec_btn.on('click', lambda _: on_move(-1))
            inc_btn.on('click', lambda _: on_move(1))
            save_btn.on('click', lambda _: on_save())
