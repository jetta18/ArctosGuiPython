from nicegui import ui

def on_key(event):
    print(f"Key: {event.key.name} / Action: {event.action}, Repeated: {event.action.repeat}")

# Create a keyboard listener with no ignored elements
ui.keyboard(
    on_key=on_key,
    active=True,
    repeating=True,
    ignore=[]  # capture keys even in input fields
)

ui.run()
