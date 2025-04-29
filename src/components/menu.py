from nicegui import ui, app
import os

def create_menu():
    """Creates a modern, intuitive navigation bar for the application."""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    assets_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'assets'))
    app.add_static_files('/assets', assets_path)

    # Modern horizontal navigation bar
    with ui.header().classes('bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700 shadow-lg px-6 py-2'):
        with ui.row().classes('items-center w-full justify-between'):
            # Left: Logo and App Title
            with ui.row().classes('items-center gap-3'):
                ui.image('/assets/icon.png').classes('w-10 h-10 rounded shadow-lg')
                ui.label("Arctos Robot Control").classes('text-2xl font-extrabold tracking-wide text-white drop-shadow')
            # Center: Navigation Buttons
            with ui.row().classes('gap-2 ml-8'):
                ui.button('🏠 Home', on_click=lambda: ui.navigate.to('/')).props('flat').classes('nav-btn')
                ui.button('🦾 Control', on_click=lambda: ui.navigate.to('/control')).props('flat').classes('nav-btn')
                ui.button('⚙️ Settings', on_click=lambda: ui.navigate.to('/settings')).props('flat').classes('nav-btn')
                ui.button('🔧 MKS Config', on_click=lambda: ui.navigate.to('/mks')).props('flat').classes('nav-btn')
            # Right: Profile/Settings and Shutdown
            with ui.row().classes('gap-3 ml-auto items-center'):
                ui.button('❌ Stop Application', on_click=app.shutdown).props('flat').classes('bg-red-600 text-white font-bold rounded px-4 py-2 hover:bg-red-800 shadow-lg transition-all')
    # Add some custom CSS for nav-btn hover/active
    ui.add_head_html('''
    <style>
    .nav-btn {
        background: transparent;
        color: #fff;
        font-weight: 500;
        border-radius: 0.6rem;
        padding: 0.5rem 1.2rem;
        transition: background 0.2s, color 0.2s, box-shadow 0.2s;
        box-shadow: none;
        outline: none;
    }
    .nav-btn:hover, .nav-btn:focus {
        background: rgba(255,255,255,0.10);
        color: #38bdf8;
        box-shadow: 0 2px 8px rgba(56,189,248,0.08);
    }
    </style>
    ''')
