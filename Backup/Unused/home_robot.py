import os
import time
import can
import serial.tools.list_ports

# Konfiguration
BAUDRATE = 500000
MOTOR_IDS = [3, 2 ,1]  # IDs der Motoren
TARGET_FILE = "target_positions.txt"  # Datei mit gespeicherten Positionen

# Gear Ratios aus roscan.py
GEAR_RATIOS = [6.75, 75, 75, 24, 33.91, 33.91]  # Getriebeübersetzungen für jede Achse

def calculate_crc(data):
    """Berechnet die CRC-Prüfsumme für eine CAN-Nachricht."""
    return sum(data) & 0xFF  # 8-bit CRC Checksum


def find_can_port():
    """Findet die CAN-Schnittstelle automatisch."""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "CAN" in port.description or "USB2CAN" in port.description:
            return port.device
    return None

def read_target_positions(file_path):
    """Liest gespeicherte Positionen aus einer Datei."""
    if not os.path.exists(file_path):
        print(f"Fehler: Datei {file_path} nicht gefunden!")
        return {motor_id: 0 for motor_id in MOTOR_IDS}  # Standardwert 0

    positions = {}
    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split("=")
            if len(parts) == 2:
                motor_id, position = int(parts[0]), float(parts[1])
                positions[motor_id] = position  # Werte in Radians speichern
    return positions

def send_can_message(bus, motor_id, command, data):
    """Sendet eine CAN-Nachricht an einen Motor mit korrekt berechnetem CRC."""
    message_data = [command] + data  # Befehl + Daten
    time.sleep(0.1)
    crc = calculate_crc([motor_id] + message_data)  # CRC berechnen
    time.sleep(0.1)
    full_message = message_data + [crc]  # CRC ans Ende anhängen

    message = can.Message(arbitration_id=motor_id, data=full_message, is_extended_id=False)
    time.sleep(0.1)
    bus.send(message)

    print(f"Gesendet: Motor {motor_id} | Befehl: {command:02X} | Daten: {full_message}")
    time.sleep(0.2)  # Wartezeit für Verarbeitung

def home_motor(bus, motor_id):
    """Sendet eine korrekt formatierte Home-Nachricht (`0x91`) an den Motor mit CRC."""
    print(f"Motor {motor_id} fährt auf Home-Position...")

    home_command = [0x91]  # Home-Befehl
    send_can_message(bus, motor_id, home_command[0], home_command[1:])  # `0x91` mit CRC senden

    time.sleep(10)  # Wartezeit für das Homen
    print(f"Motor {motor_id} ist in der Home-Position.")

def move_to_position(bus, motor_id, radians):
    """
    Bewegt den Motor auf eine gespeicherte Position mit Befehl `F5`
    und setzt danach die aktuelle Position auf Null (`0x92`).
    """
    gear_ratio = GEAR_RATIOS[motor_id - 1]  # Gear Ratio für die Achse
    abs_position = int(radians * gear_ratio * 100)  # Berechnung aus convert_to_can_message()

    print(f"Motor {motor_id} fährt auf gespeicherte Position: {abs_position} (Encoder-Pulses basierend auf Gear Ratio)")

    speed = 500  # RPM
    acceleration = 2  # Beispielwert

    speed_bytes = speed.to_bytes(2, byteorder="big", signed=False)
    position_bytes = abs_position.to_bytes(3, byteorder="big", signed=True)

    # CAN-Nachricht im `F5`-Format: [Befehl] [Speed] [Mode] [Position] [CRC]
    can_data = [0xF5] + list(speed_bytes) + [0x02] + list(position_bytes)
    send_can_message(bus, motor_id, can_data[0], can_data[1:])  # `F5` Befehl mit CRC senden
    send_can_message(bus, motor_id, can_data[0], can_data[1:])  # `F5` Befehl mit CRC senden

    time.sleep(10)  # Wartezeit, damit sich der Motor bewegt

    # Position auf Null setzen mit `0x92`
    print(f"Setze Motor {motor_id} auf Null-Position...")
    send_can_message(bus, motor_id, 0x92, [])  # `0x92` Befehl senden
    time.sleep(1)  # Kurze Wartezeit für die Nullsetzung


def move_to_zero_pose():
    """Hauptprogramm zum Homen und Positionieren der Motoren."""
    print("Starte Homen der Motoren...")

    # CAN-Port finden
    can_port = find_can_port()
    if can_port is None:
        print("Keine CAN-Schnittstelle gefunden. Bitte Verbindung prüfen!")
        return

    print(f"Verwende CAN-Schnittstelle: {can_port}")
    bus = can.interface.Bus(bustype="slcan", channel=can_port, bitrate=BAUDRATE)

    # Zielpositionen laden (in Radians)
    target_positions = read_target_positions(TARGET_FILE)

    # Jeder Motor fährt einzeln auf Home und dann auf Zielposition
    for motor_id in MOTOR_IDS:
        home_motor(bus, motor_id)  # Home-Prozess mit verbessertem Format
        target_pos = target_positions.get(motor_id, 0)  # Falls nicht vorhanden, nehme 0 Radians
        move_to_position(bus, motor_id, target_pos)

    print("Alle Motoren haben ihre Zielposition erreicht.")

def move_to_sleep_pose():
    """Hauptprogramm zum Homen und Positionieren der Motoren."""
    print("Starte Homen der Motoren...")

    # CAN-Port finden
    can_port = find_can_port()
    if can_port is None:
        print("Keine CAN-Schnittstelle gefunden. Bitte Verbindung prüfen!")
        return

    print(f"Verwende CAN-Schnittstelle: {can_port}")
    bus = can.interface.Bus(bustype="slcan", channel=can_port, bitrate=BAUDRATE)

    # Zielpositionen laden (in Radians)
    target_positions = read_target_positions(TARGET_FILE)

    # Jeder Motor fährt einzeln auf Home und dann auf Zielposition
    for motor_id in MOTOR_IDS:
        home_motor(bus, motor_id)  # Home-Prozess mit verbessertem Format
        target_pos = target_positions.get(motor_id, 0)  # Falls nicht vorhanden, nehme 0 Radians
        move_to_position(bus, motor_id, target_pos)

    home_motor(bus, 2)
    time.sleep(1)
    home_motor(bus, 3)


    print("Alle Motoren haben ihre Zielposition erreicht.")

