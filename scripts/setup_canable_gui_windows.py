
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox
import can

# Function to detect CANable-like devices (can be improved with VID/PID filters)
def find_canable_ports():
    ports = serial.tools.list_ports.comports()
    can_ports = []
    for port in ports:
        desc = f"{port.device} - {port.description}"
        if "canable" in port.description.lower() or "usb serial" in port.description.lower():
            can_ports.append((port.device, desc))
    return can_ports or [(p.device, f"{p.device} - {p.description}") for p in ports]

# Placeholder function to "start" the CAN interface via python-can
def start_can_interface(port, bitrate=500000):
    try:
        interface = "slcan"
        channel = port
        can_bus = can.interface.Bus(channel=channel, interface=interface, bitrate=bitrate)
        # Send a test frame (optional)
        msg = can.Message(arbitration_id=0x123, data=[0x11, 0x22], is_extended_id=False)
        can_bus.send(msg)
        return True, f"Interface started on {port} with bitrate {bitrate}"
    except Exception as e:
        return False, str(e)

# GUI Application
def run_gui():
    def on_connect():
        selected = combo.get()
        if not selected:
            messagebox.showwarning("Auswahl fehlt", "Bitte einen COM-Port auswählen.")
            return
        port = selected.split(" ")[0]
        success, msg = start_can_interface(port)
        if success:
            messagebox.showinfo("Erfolg", msg)
        else:
            messagebox.showerror("Fehler", f"Verbindung fehlgeschlagen:\n{msg}")

    window = tk.Tk()
    window.title("CANable Setup (Windows)")
    window.geometry("400x200")
    window.resizable(False, False)

    label = ttk.Label(window, text="Wähle dein CANable-Gerät (COM-Port):")
    label.pack(pady=10)

    ports = find_canable_ports()
    combo = ttk.Combobox(window, values=[desc for _, desc in ports], width=50)
    combo.pack(pady=5)

    connect_button = ttk.Button(window, text="Interface starten", command=on_connect)
    connect_button.pack(pady=20)

    window.mainloop()

if __name__ == "__main__":
    run_gui()
