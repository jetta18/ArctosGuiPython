from nicegui import ui, app

def create_menu():
    """
    Creates the navigation menu for the application.
    
    This function builds a responsive navigation header with a dropdown menu. 
    Users can navigate between different sections, including the home page, 
    robot control, settings, and MKS configuration. An exit option is also included.
    """
    with ui.header().classes('bg-gray-800 text-white p-2'):
        ui.label("🤖 Arctos Robot Control").classes('text-2xl font-bold ml-4')
        with ui.button(icon='menu').classes('ml-auto'):
            with ui.menu():
                ui.menu_item('🏠 Home', lambda: ui.navigate.to('/'))
                ui.menu_item('🦾 Control', lambda: ui.navigate.to('/control'))
                ui.menu_item('⚙️ Settings', lambda: ui.navigate.to('/settings'))
                ui.menu_item('🔧 MKS Configuration', lambda: ui.navigate.to('/mks'))
                ui.separator()
                ui.menu_item('❌ Exit', on_click=app.shutdown)
