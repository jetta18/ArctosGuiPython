from nicegui import ui, app

def create_menu():
    """Creates the navigation menu for the application.
    
    This function builds a responsive navigation header with a dropdown menu, allowing
    users to navigate between different sections of the application. The menu
    includes options for the home page, robot control, settings, MKS configuration,
    and an exit option to shut down the application.
    """
    # Create a header container for the navigation menu
    with ui.header().classes('bg-gray-800 text-white p-2'):
        # Add a label for the application name, styled as a header
        ui.label("🤖 Arctos Robot Control").classes('text-2xl font-bold ml-4')

        # Create a menu button (hamburger icon) that triggers the dropdown menu
        with ui.button(icon='menu').classes('ml-auto'):

            # Define the dropdown menu
            with ui.menu():

                # Menu items with navigation links
                # Navigate to the home page
                ui.menu_item('🏠 Home', lambda: ui.navigate.to('/'))
                # Navigate to the control page
                ui.menu_item('🦾 Control', lambda: ui.navigate.to('/control'))
                # Navigate to the settings page
                ui.menu_item('⚙️ Settings', lambda: ui.navigate.to('/settings'))
                # Navigate to the mks config page
                ui.menu_item('🔧 MKS Configuration', lambda: ui.navigate.to('/mks'))

                # Add a separator for visual clarity
                ui.separator()
                # Add an exit option that shuts down the application
                ui.menu_item('❌ Stop Application', on_click=app.shutdown)
