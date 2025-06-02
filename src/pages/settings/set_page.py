"""
set_page.py

Main entry point for the Arctos Settings page UI.
Provides the create() function to build the settings page with all tabs and dialogs.
"""

from typing import Any, Dict
from nicegui import ui
from utils.settings_manager import SettingsManager
from pages.settings.dialog_helpers import create_gear_ratio_wizard, create_reset_dialog
from pages.settings.tabs.general_tab import general_tab
from pages.settings.tabs.joints_tab import joints_tab
from pages.settings.tabs.homing_tab import homing_tab


def create(settings_manager: SettingsManager, arctos: Any) -> None:
    """
    Build the Settings page with vertical tabs and responsive scaling.

    Args:
        settings_manager (SettingsManager): The persistent settings manager.
        arctos (Any): The main robot controller instance.

    Returns:
        None

    This function constructs the settings page UI, including tabs for General, Joints, and Homing,
    and provides dialogs for gear-ratio calibration and resetting all settings. It applies the current
    theme, builds the tabbed layout, and injects all required event handlers.
    """
    settings: Dict[str, Any] = settings_manager.all()

    # Apply theme immediately
    (ui.dark_mode().enable() if settings.get("theme") == "Dark" else ui.dark_mode().disable())

    # Gear-Ratio Wizard dialog (helper returns open function)
    def _current_ratio(axis_idx: int) -> float:
        return settings_manager.get("gear_ratios", [13.5, 150, 150, 48, 67.82/2, 67.82/2])[axis_idx]
    open_ratio_wizard = create_gear_ratio_wizard(settings_manager, arctos, _current_ratio)

    # Reset dialog
    open_reset_dialog = create_reset_dialog(settings_manager)

    # Page header
    ui.label("⚙️ Settings").classes("text-4xl font-bold text-center my-4")

    # Splitter with vertical tabs
    with ui.splitter(value=20).classes("w-full h-[calc(100vh-8rem)]") as splitter:
        with splitter.before:
            with ui.tabs().props("vertical").classes("w-full") as tabs:
                tab_general = ui.tab("General", icon="tune")
                tab_joints = ui.tab("Joints", icon="developer_board")
                tab_homing = ui.tab("Homing", icon="home")
        with splitter.after:
            with ui.tab_panels(tabs, value=tab_general).props("vertical").classes("w-full h-full overflow-y-auto"):
                with ui.tab_panel(tab_general):
                    general_tab(settings_manager, settings)
                with ui.tab_panel(tab_joints):
                    joints_tab(settings_manager, arctos, settings, open_ratio_wizard)
                with ui.tab_panel(tab_homing):
                    homing_tab(settings_manager, arctos)

    # Reset-All Button
    ui.button("Reset All", on_click=lambda: open_reset_dialog()) \
        .props('color=negative') \
        .classes('text-white mt-4')
