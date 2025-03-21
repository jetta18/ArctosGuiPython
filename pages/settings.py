from nicegui import ui

def create():
    """
    Settings page for general configurations.
    """

    with ui.column().classes('p-4'):
        ui.label("⚙️ Settings").classes('text-3xl font-bold')

        # Dark Mode Toggle
        with ui.row():
            ui.label("🌗 Theme")
            ui.toggle(["Light", "Dark"], value="Light", on_change=lambda e: ui.dark_mode().enable() if e.value == "Dark" else ui.dark_mode().disable())

        # Language Selection
        with ui.row():
            ui.label("🌍 Language")
            ui.toggle(["English", "Deutsch"], value="English", on_change=lambda e: ui.notify(f"Language set to: {e.value}"))

        # UI Color Theme
        with ui.row():
            ui.label("🎨 UI Color Theme")
            ui.select(["Blue", "Green", "Red", "Gray"], value="Blue", on_change=lambda e: ui.notify(f"Color set to: {e.value}"))

        # FPS Slider
        with ui.row():
            ui.label("⚡ Performance Mode")
            ui.slider(min=1, max=60, value=30, step=1, on_change=lambda e: ui.notify(f"Max FPS set to: {e.value}"))

        # Auto-Update Saved Poses
        with ui.row():
            ui.label("🔄 Auto-Update Saved Poses")
            auto_update = ui.switch()
            auto_update.on_value_change(lambda e: ui.notify("Auto-Update Enabled" if e.value else "Auto-Update Disabled"))

        # Reset Button
        ui.button("🔄 Reset Settings", on_click=lambda: ui.notify("Settings have been reset!")).classes('bg-red-500 text-white px-4 py-2 rounded-lg')
