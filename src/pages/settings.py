"""
Enhanced Settings page with vertical tabs inside a splitter and responsive
layout.  *Homing* tab now leverages a responsive **CSS Grid** so that the offsets
 table and the calibration wizard are shown **side‑by‑side on medium and larger
 screens** while automatically stacking on mobiles. All behaviour (callbacks,
 settings persistence) remains unchanged.
"""
from typing import Any, Dict

from nicegui import ui
from nicegui.elements.switch import Switch

from utils.settings_manager import SettingsManager
from core.homing import HOMING_SEQUENCE


def create(settings_manager: SettingsManager, arctos: Any) -> None:
    """Build the Settings page with vertical tabs and responsive scaling."""
    settings: Dict[str, Any] = settings_manager.all()

    # Apply theme immediately
    (ui.dark_mode().enable() if settings.get("theme") == "Dark" else ui.dark_mode().disable())

    # Page header
    ui.label("⚙️ Settings").classes("text-4xl font-bold text-center my-4")

    # ───────────── Splitter with vertical tabs ──────────────
    with ui.splitter(value=20).classes("w-full h-[calc(100vh-8rem)]") as splitter:
        # -------- Tabs (left side) --------
        with splitter.before:
            with ui.tabs().props("vertical").classes("w-full") as tabs:
                tab_general = ui.tab("General", icon="tune")
                tab_joints = ui.tab("Joints", icon="developer_board")
                tab_homing = ui.tab("Homing", icon="home")

        # -------- Panels (right side) --------
        with splitter.after:
            with ui.tab_panels(tabs, value=tab_general).props("vertical").classes("w-full h-full overflow-y-auto"):

                # ==================== General Tab ====================
                with ui.tab_panel(tab_general):
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

                # ==================== Joints Tab ====================
                with ui.tab_panel(tab_joints):

                    # Helper – each widget uses the same handler factory so we don't repeat lambdas
                    def make_handler(k: str, idx: int, default: Dict[int, int], title: str):
                        """Returns a handler that stores the new value and shows a toast."""
                        def _handler(e):
                            raw_val = -1 if k == "joint_directions" and e.value == "Inverted" else int(e.value)
                            settings_manager.set(k, {**settings_manager.get(k, default), idx: raw_val})
                            ui.notify(f"{title.split()[1]} {idx + 1} set to {e.value}")
                        return _handler

                    with ui.row().classes("flex-wrap gap-4"):

                        # ───── Cards 1-3: Direction, Speed, Acceleration ─────
                        for title, key, default, label_fmt, tooltip in [
                            ("Joint Directions", "joint_directions",
                             {i: 1 for i in range(6)}, "Joint {}", "Invert or normal rotation direction."),
                            ("Joint Speeds (RPM)", "joint_speeds",
                             {i: 500 for i in range(6)}, "J{}", "Set max speed in RPM."),
                            ("Joint Accelerations", "joint_accelerations",
                             {i: 150 for i in range(6)}, "J{}", "Set acceleration (0-255).")
                        ]:
                            with ui.card().classes("p-4 grow md:max-w-[30%]"):
                                ui.label(title).classes("text-xl font-semibold mb-2")
                                vals: Dict[int, int] = settings.get(key, default)
                                with ui.row().classes("flex-wrap gap-2"):
                                    for i in range(6):
                                        widget = ui.select if title == "Joint Directions" else ui.number
                                        val_i = vals.get(i)
                                        init_val = (
                                            "Inverted"
                                            if title == "Joint Directions" and val_i == -1
                                            else (val_i if title != "Joint Directions" else "Normal")
                                        )
                                        params: Dict[str, Any] = {"label": label_fmt.format(i + 1), "value": init_val}
                                        if widget is ui.select:
                                            params["options"] = ["Normal", "Inverted"]
                                        else:
                                            params.update({
                                                "min": 0,
                                                "max": 3000 if key == "joint_speeds" else 255,
                                                "step": 10 if key == "joint_speeds" else 5
                                            })
                                        widget(**params,
                                               on_change=make_handler(key, i, default, title))\
                                            .classes("w-24 sm:w-28 md:w-32")\
                                            .tooltip(tooltip)

                        # ───── Card 4: Gear Ratios ─────
                        with ui.card().classes("p-4 grow md:max-w-[30%]"):
                            ui.label("Gear Ratios").classes("text-xl font-semibold mb-2")

                            # Load current or default ratios
                            ratios: list[float] = settings_manager.get(
                                "gear_ratios",
                                [13.5, 150, 150, 48, 67.82 / 2, 67.82 / 2]
                            )

                            def make_ratio_handler(idx: int):
                                def _handler(e):
                                    updated = list(settings_manager.get("gear_ratios", ratios))
                                    updated[idx] = float(e.value or 0)
                                    settings_manager.set("gear_ratios", updated)
                                    # 👉 live-update the controller
                                    arctos.set_gear_ratios(
                                        updated,
                                        settings_manager.get("joint_directions", {i: 1 for i in range(6)})
                                    )
                                    ui.notify(f"Gear ratio J{idx + 1} set to {e.value}")
                                return _handler


                            # Input fields J1–J6
                            with ui.row().classes("flex-wrap gap-2"):
                                for i in range(6):
                                    ui.number(
                                        label=f"J{i + 1}",
                                        value=ratios[i],
                                        min=1, step=0.1,
                                        on_change=make_ratio_handler(i)
                                    ).classes("w-24 sm:w-28 md:w-32")\
                                     .tooltip("Set gear reduction ratio")


                # ==================== Homing Tab ====================
                with ui.tab_panel(tab_homing):
                    # -------- Grid container (table + wizard) --------
                    with ui.element('div').classes("w-full grid grid-cols-1 md:grid-cols-2 gap-4 items-start"):
                        # ---- Offsets table ----
                        with ui.card().classes("p-4 overflow-x-auto"):
                            ui.label("Homing Offsets").classes("text-xl font-semibold mb-2")
                            offsets: Dict[int, int] = settings_manager.get("homing_offsets", {i: 0 for i in range(6)})
                            rows = [{"Axis": f"J{axis}", "Offset": offsets.get(axis - 1, 0)} for axis in HOMING_SEQUENCE]
                            ui.table(
                                columns=[{"name": "Axis", "label": "Axis"}, {"name": "Offset", "label": "Offset"}],
                                rows=rows
                            ).classes("min-w-full").tooltip("Current zero offsets for each joint.")

                        # ---- Calibration Wizard ----
                        with ui.card().classes("p-4") as wizard_card:
                            ui.label("Calibration Wizard").classes("text-xl font-semibold mb-2")
                            # First line: axis selection + buttons
                            with ui.row().classes("gap-2 flex-wrap mb-2"):
                                axis_sel = ui.select([f"Axis {i}" for i in HOMING_SEQUENCE], label="Axis", value=f"Axis {HOMING_SEQUENCE[0]}").classes("w-32")
                                axis_sel.tooltip("Select the joint to calibrate.")
                                home_btn = ui.button("🏠 Home").tooltip("Drive joint to limit switch (zero encoder).")
                                save_btn = ui.button("💾 Save").tooltip("Save current encoder value as zero offset.")
                            # Second line: step value + move buttons
                            with ui.row().classes("gap-2 flex-wrap mb-2 items-center"):
                                ui.label("Step:").classes("w-12")
                                step_in = ui.number(label=None, value=100, min=1, step=1).classes("w-20")
                                step_in.tooltip("Incremental step size for manual adjustment.")
                                dec_btn = ui.button("◀").tooltip("Move joint negative by step.")
                                inc_btn = ui.button("▶").tooltip("Move joint positive by step.")
                            # Position read‑out
                            pos_lbl = ui.label("Position: --").classes("mt-2 font-mono")

                            # ---------- Handlers ----------
                            def on_home():
                                idx = int(axis_sel.value.split()[-1]) - 1
                                arctos.servos[idx].b_go_home()
                                pos_lbl.text = "Position: 0"

                            def on_move(dir_: int):
                                idx = int(axis_sel.value.split()[-1]) - 1
                                raw = int(step_in.value or 0) * dir_
                                sp = settings_manager.get("joint_speeds", {}).get(idx, 500)
                                ac = settings_manager.get("joint_accelerations", {}).get(idx, 150)
                                arctos.servos[idx].run_motor_relative_motion_by_axis(sp, ac, raw)
                                val = arctos.servos[idx].read_encoder_value_addition() or 0
                                pos_lbl.text = f"Position: {val}"

                            def on_save():
                                idx = int(axis_sel.value.split()[-1]) - 1
                                val = arctos.servos[idx].read_encoder_value_addition() or 0
                                d = settings_manager.get("homing_offsets", {})
                                d[idx] = val
                                settings_manager.set("homing_offsets", d)
                                ui.notify(f"Saved offset J{idx + 1}: {val}")

                            # Bind handlers after definition
                            home_btn.on('click', lambda _: on_home())
                            dec_btn.on('click', lambda _: on_move(-1))
                            inc_btn.on('click', lambda _: on_move(1))
                            save_btn.on('click', lambda _: on_save())

            # ───────────── End of panels ─────────────

    # ═══════════ Global actions outside splitter ═══════════
    with ui.dialog() as dlg, ui.card().classes("p-4"):
        ui.label("Confirm Reset").classes("text-xl font-semibold mb-2")
        ui.label("Are you sure you want to reset all settings? This cannot be undone.")
        with ui.row().classes("justify-end mt-4 gap-2"):
            # Cancel → red
            ui.button("Cancel", on_click=dlg.close) \
                .props('color=negative') \
                .classes('text-white')

            # Confirm → green
            ui.button("Confirm") \
                .props('color=positive') \
                .classes('text-white') \
                .on('click', lambda: (
                    [settings_manager.set(k, v) for k, v in {
                    "theme": "Light",  # Default UI theme
                    "joint_speeds": {i: 500 for i in range(6)},
                    'joint_acceleration': {i: 150 for i in range(6)},
                    "joint_directions": {i: 1 for i in range(6)},  # Default direction for each joint (1 or -1)
                    "speed_scale": 1.0, 
                    "enable_live_joint_updates": False,  # Enable live encoder updates in U
                    "homing_offsets": {i: 0 for i in range(6)},  # Homing offset for each joint
                    "gear_ratios": [13.5, 150, 150, 48, 33.91, 33.91],
                    }.items()],
                    ui.notify("Settings reset to defaults."), dlg.close()
                ))

    # Reset-All-Button → red
    ui.button("Reset All", on_click=lambda: dlg.open()) \
        .props('color=negative') \
        .classes('text-white mt-4')
