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
        ui.label("Appearance").classes("text-xl font-semibold mb-2")
        ui.toggle(["Light", "Dark"],
                  value=settings.get("theme", "Light"),
                  on_change=lambda e: (
                      settings_manager.set("theme", e.value),
                      ui.dark_mode().enable() if e.value == "Dark" else ui.dark_mode().disable(),
                      ui.notify(f"Theme set to {e.value}")
                  )
                  ).tooltip("Choose between light and dark UI themes.")
    with ui.card().classes("p-4"):
        ui.label("Live Joint Updates").classes("text-xl font-semibold mb-2")
        live_switch: Switch = ui.switch(
            "Enable live joint angle updates",
            value=settings.get("enable_live_joint_updates", True)
        )
        live_switch.on_value_change(lambda e: (
            settings_manager.set("enable_live_joint_updates", e.value),
            ui.notify("Live updates enabled" if e.value else "Live updates disabled")
        ))
        live_switch.tooltip("Toggle real-time display of joint encoder readings.")

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
            ("Joint Directions", "joint_directions", {i: 1 for i in range(6)}, "Joint {}", "Invert or normal rotation direction."),
            ("Joint Speeds (RPM)", "joint_speeds", {i: 500 for i in range(6)}, "J{}", "Set max speed in RPM."),
            ("Joint Accelerations", "joint_accelerations", {i: 150 for i in range(6)}, "J{}", "Set acceleration (0-255).")
        ]:
            with ui.card().classes("p-4 grow md:max-w-[30%]"):
                with ui.row().classes("items-center gap-1 mb-2"):
                    ui.label(title).classes("text-xl font-semibold")
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
            ui.label("Gear Ratios").classes("text-xl font-semibold mb-2")
            ratios = settings_manager.get("gear_ratios", [13.5, 150, 150, 48, 67.82 / 2, 67.82 / 2])
            with ui.row().classes("flex-wrap gap-2"):
                for i in range(6):
                    ui.number(
                        label=f"J{i + 1}",
                        value=ratios[i],
                        min=1, step=0.1,
                        on_change=make_ratio_handler(settings_manager, arctos, i)
                    ).classes("w-24 sm:w-28 md:w-32")\
                     .tooltip("Set gear reduction ratio")
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
    with ui.element('div').classes("w-full grid grid-cols-1 md:grid-cols-2 gap-4 items-start"):
        # Offsets Table
        with ui.card().classes("p-4 overflow-x-auto"):
            ui.label("Homing Offsets").classes("text-xl font-semibold mb-2")
            offsets = settings_manager.get("homing_offsets", {i: 0 for i in range(6)})
            rows = [{"Axis": f"J{axis}", "Offset": offsets.get(axis - 1, 0)} for axis in HOMING_SEQUENCE]
            ui.table(
                columns=[{"name": "Axis", "label": "Axis"}, {"name": "Offset", "label": "Offset"}],
                rows=rows
            ).classes("min-w-full").tooltip("Current zero offsets for each joint.")
        # Calibration Wizard
        with ui.card().classes("p-4") as wizard_card:
            with ui.row().classes("items-center mb-2 gap-1"):
                ui.label("Calibration Wizard").classes("text-xl font-semibold")
                with ui.icon("info").classes("text-blue-500 cursor-pointer"):
                    with ui.tooltip().classes("text-body2 text-left"):
                        ui.html(
                            """
                            1. 🏠 <strong>Home</strong> – drive the joint to its limit switch (encoder = 0)<br>
                            2. ◀ / ▶ – jog the joint by the selected <em>Step</em> until the zero-mark aligns<br>
                            3. 💾 <strong>Save</strong> – write the current encoder count as the homing offset
                            """
                        )
            with ui.row().classes("gap-2 flex-wrap mb-2"):
                axis_sel = ui.select([f"Axis {i}" for i in HOMING_SEQUENCE], label="Axis", value=f"Axis {HOMING_SEQUENCE[0]}").classes("w-32")
                axis_sel.tooltip("Select the joint to calibrate.")
                home_btn = ui.button("🏠 Home").tooltip("Drive joint to limit switch (zero encoder).")
                save_btn = ui.button("💾 Save").tooltip("Save current encoder value as zero offset.")
            with ui.row().classes("gap-2 flex-wrap mb-2 items-center"):
                ui.label("Step:").classes("w-12")
                step_in = ui.number(label=None, value=100, min=1, step=1).classes("w-20")
                step_in.tooltip("Incremental step size for manual adjustment.")
                dec_btn = ui.button("◀").tooltip("Move joint negative by step.")
                inc_btn = ui.button("▶").tooltip("Move joint positive by step.")
            pos_lbl = ui.label("Position: --").classes("mt-2 font-mono")
            on_home, on_move, on_save = make_homing_handlers(settings_manager, arctos, axis_sel, step_in, pos_lbl)
            home_btn.on('click', lambda _: on_home())
            dec_btn.on('click', lambda _: on_move(-1))
            inc_btn.on('click', lambda _: on_move(1))
            save_btn.on('click', lambda _: on_save())
