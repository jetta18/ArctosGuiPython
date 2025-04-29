from nicegui import ui, app
import os

"""
menu.py

Provides the main navigation bar for the Arctos Robot Control application using NiceGUI.
This module defines a modern, intuitive, and visually appealing navigation header with logo,
page links, and a shutdown button. It is intended to be included at the top of every page.
"""

def create_menu():
    """Create a modern, intuitive navigation bar for the application.

    The navigation bar includes the application logo, title, navigation buttons for main sections,
    and a prominent shutdown button. The UI is styled for a modern look and responsive layout.

    Returns:
        None. The function builds the UI directly using NiceGUI components and injects CSS.

    Side Effects:
        - Registers static asset files for the logo and images.
        - Injects custom CSS for navigation button styles.
    """
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
