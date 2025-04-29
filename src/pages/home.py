from nicegui import ui, app
import os

def create():
    ui.dark_mode()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'assets'))
    app.add_static_files('/assets', assets_path)

    with ui.column().classes(
        'items-center justify-center min-h-screen w-full bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 animate-gradient-x'):

        # Hero Section
        with ui.column().classes('items-center mt-10 mb-8'):
            ui.image('/assets/icon.png').classes('w-44 h-44 drop-shadow-2xl hover:scale-105 transition-transform duration-300')
            ui.label("Arctos Robot Control").classes('text-6xl font-extrabold tracking-tight text-white mt-6 drop-shadow-xl')
            ui.label("Seamless, powerful, and intuitive robot management for professionals and makers.").classes('text-xl text-gray-300 mt-3 mb-2')
            ui.button('🚀 Get Started', on_click=lambda: ui.navigate.to('/control')).classes(
                'bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-4 rounded-full text-xl font-semibold mt-4 mb-2 shadow-lg hover:scale-105 hover:from-blue-700 hover:to-indigo-700 transition-all')

        # Feature Highlights (polished, always visible)
        with ui.grid().classes('grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 w-full max-w-5xl mt-2 mb-10 justify-center'):
            for color, icon, title, desc, link in [
                ('text-blue-400', 'bolt', 'Real-Time Control', 'Instant feedback and live robot response', None),
                ('text-green-400', 'shield-check', 'Safety First', 'Built-in safety checks and emergency stop', None),
                ('text-yellow-400', 'cogs', 'Modular Config', 'Flexible settings for every use case', None),
                ('text-purple-400', 'book-open', 'Documentation', None, 'https://github.com/jetta18/ArctosGuiPython'),
            ]:
                with ui.card().classes('w-full min-h-[160px] bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-lg flex flex-col items-center p-5 transition-transform hover:scale-105 hover:shadow-2xl duration-200'):
                    ui.icon(icon).classes(f'{color} text-3xl mb-2')
                    ui.label(title).classes('text-lg font-bold text-white mb-1')
                    if desc:
                        ui.label(desc).classes('text-gray-300 text-sm text-center')
                    if link:
                        ui.link('Read the Docs', link, new_tab=True).classes('text-blue-300 underline hover:text-white text-sm mt-1')

        # Navigation Dashboard
        with ui.grid().classes('grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-5xl mt-6 px-8'):
            with ui.card().classes('p-8 bg-white/10 backdrop-blur-xl border border-white/10 rounded-2xl shadow-xl text-center hover:scale-105 hover:shadow-2xl transition-transform duration-300'):
                ui.icon('gamepad').classes('text-4xl text-blue-400 mb-3')
                ui.label('Robot Control').classes('text-2xl font-bold text-white')
                ui.label('Manual & automated robot operation').classes('text-gray-300 text-base mb-4')
                ui.button('Go to Control', on_click=lambda: ui.navigate.to('/control')).classes('bg-blue-600 text-white px-6 py-3 rounded-lg mt-2 hover:bg-blue-700 hover:scale-105')
            with ui.card().classes('p-8 bg-white/10 backdrop-blur-xl border border-white/10 rounded-2xl shadow-xl text-center hover:scale-105 hover:shadow-2xl transition-transform duration-300'):
                ui.icon('settings').classes('text-4xl text-yellow-400 mb-3')
                ui.label('Servo Config').classes('text-2xl font-bold text-white')
                ui.label('Motor calibration & diagnostics').classes('text-gray-300 text-base mb-4')
                ui.button('Go to Servo Config', on_click=lambda: ui.navigate.to('/mks')).classes('bg-yellow-500 text-white px-6 py-3 rounded-lg mt-2 hover:bg-yellow-600 hover:scale-105')
            with ui.card().classes('p-8 bg-white/10 backdrop-blur-xl border border-white/10 rounded-2xl shadow-xl text-center hover:scale-105 hover:shadow-2xl transition-transform duration-300'):
                ui.icon('tune').classes('text-4xl text-green-400 mb-3')
                ui.label('Settings').classes('text-2xl font-bold text-white')
                ui.label('Networking, sensors, and system options').classes('text-gray-300 text-base mb-4')
                ui.button('Go to Settings', on_click=lambda: ui.navigate.to('/settings')).classes('bg-green-600 text-white px-6 py-3 rounded-lg mt-2 hover:bg-green-700 hover:scale-105')

        ui.separator().classes('my-16 border-gray-600 w-2/3')

        # Footer
        with ui.row().classes('mt-8 mb-6 text-base text-gray-400 items-center justify-center gap-2'):
            ui.label('© 2025 jetta18 |')
            ui.link('GitHub', 'https://github.com/jetta18/ArctosGuiPython', new_tab=True).classes('underline hover:text-white')
            ui.label('| v0.1 Beta')
