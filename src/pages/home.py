from nicegui import ui, app
import os


def create():
    """
    Create the home page of the Arctos Robot Control GUI.

    This function generates the main landing page for the Arctos Robot Control application.
    It features a dynamic, visually appealing layout with:
        - Animated gradient background
        - Glassy cards with smooth transitions
        - Interactive buttons for navigation
        - GitHub footer link

    The page provides an overview and quick access to the robot control, servo configuration, and settings pages.
    """
    # Set dark mode for the UI
    ui.dark_mode()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'assets'))
    app.add_static_files('/assets', assets_path)

    # Main container for the home page layout
    # The animated gradient is applied here to create a dynamic background
    with ui.column().classes(
        'items-center justify-center min-h-screen w-full '
        'bg-gradient-to-br from-slate-800 via-blue-900 to-white-950 animate-gradient-x'):

        # Arctos Robot Logo
        # The logo is displayed at the top of the page with interactive hover effect
        ui.image('/assets/icon.png').classes(
            'w-40 h-40 mt-6 drop-shadow-xl hover:scale-105 transition-transform duration-300')

        # Main Headings
        # Main heading and sub-heading for the page, designed for high visual impact
        ui.label("Welcome to Arctos Robot Control").classes(
            'text-5xl font-extrabold tracking-wide text-white mt-4 drop-shadow-lg '
            'transition-all hover:scale-105 duration-300')
        ui.label("Control your robot, monitor system data, and configure everything with just a few clicks.").classes(
            'text-lg text-gray-300 mt-2')

        # Responsive dashboard grid
        with ui.grid().classes(
            'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 w-full max-w-screen-2xl mt-10 px-8'):
            
            # Control Card
            # Navigation card for accessing the robot control page
            with ui.card().classes(
                'p-6 bg-white/10 backdrop-blur-xl border border-white/10 rounded-xl '
                'shadow-lg text-center transition-transform transform hover:scale-105 hover:shadow-2xl duration-300'):
                ui.label("⚙️ Control").classes('text-2xl font-bold text-white')
                ui.label("Manual control & automation modes").classes("text-gray-300 text-sm mb-4")
                ui.button("🔧 Open", on_click=lambda: ui.navigate.to('/control')).classes(
                    'bg-blue-600 text-white px-6 py-3 rounded-lg '
                    'transition-all hover:bg-blue-700 hover:scale-105 shadow-[0_0_10px_#3b82f6]')
            
            # MKS Servo Configuration Card
            # Navigation card for accessing the MKS servo configuration page
            with ui.card().classes(
                'p-6 bg-white/10 backdrop-blur-xl border border-white/10 rounded-xl '
                'shadow-lg text-center transition-transform transform hover:scale-105 hover:shadow-2xl duration-300'):
                ui.label("🔩 MKS Servo Configuration").classes('text-2xl font-bold text-white')
                ui.label("Motor control & calibration").classes("text-gray-300 text-sm mb-4")
                ui.button("🛠️ Open", on_click=lambda: ui.navigate.to('/mks')).classes(
                    'bg-yellow-500 text-white px-6 py-3 rounded-lg '
                    'transition-all hover:bg-yellow-600 hover:scale-105 shadow-[0_0_10px_#eab308]')
            
            # Settings Card
            # Navigation card for accessing the system settings page
            with ui.card().classes(
                'p-6 bg-white/10 backdrop-blur-xl border border-white/10 rounded-xl '
                'shadow-lg text-center transition-transform transform hover:scale-105 hover:shadow-2xl duration-300'):
                ui.label("🛠️ Settings").classes('text-2xl font-bold text-white')
                ui.label("Network, sensors & system options").classes("text-gray-300 text-sm mb-4")
                ui.button("⚙️ Open", on_click=lambda: ui.navigate.to('/settings')).classes(
                    'bg-gray-600 text-white px-6 py-3 rounded-lg '
                    'transition-all hover:bg-gray-700 hover:scale-105 shadow-[0_0_10px_#6b7280]')
        
        # Separator Line
        # A visual separator to divide the main content area from the footer
        ui.separator().classes("my-20 border-gray-500 w-2/3")

        # Footer
        with ui.row().classes("mt-6 mb-6 text-sm text-gray-400 items-center justify-center gap-2"):
            ui.label("Arctos Robot Control v0.1 - Beta")
            ui.label("|")
            ui.link("GitHub", "https://github.com/jetta18/ArctosGuiPython", new_tab=True).classes(
                "underline hover:text-white")
