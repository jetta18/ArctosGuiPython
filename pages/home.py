from nicegui import ui

def create():
    """
    Creates a modern, fullscreen dashboard page for Arctos Robot Control.
    
    This function constructs a responsive and visually appealing user interface using the NiceGUI framework.
    It includes sections for robot control, settings, servo configuration, system status, sensor values, 
    and placeholders for future features.
    """

    # Main container with a full-screen layout and gradient background
    with ui.column().classes('items-center justify-center min-h-screen w-full bg-gradient-to-br from-gray-900 to-gray-700'):

        # Centered logo at the top
        ui.image('./assets/icon.png').classes('w-40 h-40 mt-6 drop-shadow-lg')

        # Main heading
        ui.label("Welcome to Arctos Robot Control").classes(
            'text-5xl font-extrabold tracking-wide text-white mt-4 drop-shadow-lg'
        )
        ui.label("Control your robot, monitor system data, and configure everything with just a few clicks.").classes(
            'text-lg text-gray-300 mt-2'
        )

        # **Dashboard section with full width**
        with ui.grid(columns=3).classes('w-full max-w-screen-2xl gap-6 mt-8 px-8'):

            # Control Card
            with ui.card().classes('p-6 bg-white bg-opacity-90 backdrop-blur-md rounded-xl shadow-xl text-center'):
                ui.label("⚙️ Control").classes('text-2xl font-bold text-black')
                ui.label("Manual control & automation modes").classes("text-gray-700 text-sm mb-4")
                ui.button("🔧 Open", on_click=lambda: ui.navigate.to('/control')).classes(
                    'bg-blue-500 text-white px-6 py-3 rounded-lg transition-all hover:bg-blue-600 hover:scale-105 shadow-md')

            # Settings Card
            with ui.card().classes('p-6 bg-white bg-opacity-90 backdrop-blur-md rounded-xl shadow-xl text-center'):
                ui.label("🛠️ Settings").classes('text-2xl font-bold text-black')
                ui.label("Network, sensors & system options").classes("text-gray-700 text-sm mb-4")
                ui.button("⚙️ Open", on_click=lambda: ui.navigate.to('/settings')).classes(
                    'bg-gray-500 text-white px-6 py-3 rounded-lg transition-all hover:bg-gray-600 hover:scale-105 shadow-md')

            # Servo Configuration Card
            with ui.card().classes('p-6 bg-white bg-opacity-90 backdrop-blur-md rounded-xl shadow-xl text-center'):
                ui.label("🔩 Servo Configuration").classes('text-2xl font-bold text-black')
                ui.label("Motor control & calibration").classes("text-gray-700 text-sm mb-4")
                ui.button("🛠️ Open", on_click=lambda: ui.navigate.to('/mks')).classes(
                    'bg-yellow-500 text-white px-6 py-3 rounded-lg transition-all hover:bg-yellow-600 hover:scale-105 shadow-md')

        # **Live Status Section - Now Full Width**
        with ui.grid(columns=2).classes('w-full max-w-screen-2xl gap-6 mt-8 px-8'):

            # System Status
            with ui.card().classes('p-6 bg-white bg-opacity-90 backdrop-blur-md rounded-xl shadow-xl text-center'):
                ui.label("📡 System Status").classes('text-2xl font-bold text-black')
                ui.label("Real-time monitoring of the robot").classes("text-gray-700 text-sm mb-4")
                ui.label("🟢 System OK").classes('text-green-500 text-lg font-bold')

            # Sensor Data
            with ui.card().classes('p-6 bg-white bg-opacity-90 backdrop-blur-md rounded-xl shadow-xl text-center'):
                ui.label("📊 Sensor Data").classes('text-2xl font-bold text-black')
                ui.label("Current sensor readings of the robot").classes("text-gray-700 text-sm mb-4")
                ui.label("🔵 Temperature: 36°C | 🔴 Battery: 89%").classes('text-blue-500 text-lg font-bold')

        # **Placeholder for Future Features (Expandable)**
        with ui.grid(columns=3).classes('w-full max-w-screen-2xl gap-6 mt-8 px-8'):

            # Debug Console
            with ui.card().classes('p-6 bg-white bg-opacity-90 backdrop-blur-md rounded-xl shadow-xl text-center'):
                ui.label("🖥️ Debug Console").classes('text-2xl font-bold text-black')
                ui.label("This section could display debugging logs or system data.").classes("text-gray-700 text-sm")

            # Future Features Cards
            with ui.card().classes('p-6 bg-white bg-opacity-90 backdrop-blur-md rounded-xl shadow-xl text-center'):
                ui.label("🚀 Autonomous Functions").classes('text-2xl font-bold text-black')
                ui.label("Upcoming features for autonomous control").classes("text-gray-700 text-sm")

            with ui.card().classes('p-6 bg-white bg-opacity-90 backdrop-blur-md rounded-xl shadow-xl text-center'):
                ui.label("📍 Live Map Data").classes('text-2xl font-bold text-black')
                ui.label("Interface for real-time visualization").classes("text-gray-700 text-sm")

        # **Separator for Better Structure**
        ui.separator().classes("my-6 border-gray-500 w-2/3")

        # **Footer**
        ui.label("🚀 Arctos Robot Control v1.0 - Designed for Maximum Efficiency").classes(
            "text-gray-400 text-sm mb-6"
        )
