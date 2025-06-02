from nicegui import ui
from pages.settings.handler_factories import make_homing_handlers

def homing_tab(settings_manager, arctos):
    """
    Build the Homing tab UI for settings (homing offsets and calibration wizard).

    Args:
        settings_manager: The settings manager instance.
        arctos: The robot controller instance.

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