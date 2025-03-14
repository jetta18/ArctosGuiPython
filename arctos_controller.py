import math
import can
import os
import time
from typing import List
from mks_servo_can import mks_servo
from mks_servo_can.mks_enums import Enable, Direction, EndStopLevel

class ArctosController:
    """
    ArctosController manages the communication with the robotic arm servos via CAN bus.
    It provides functions for initialization, movement, and conversion between encoder values and joint angles.
    
    This class follows a Singleton pattern to ensure only one instance controls the servos.
    """
    _instance = None  # Stores the Singleton instance

    def __new__(cls, *args, **kwargs):
        """
        Ensures a single instance of ArctosController is created (Singleton pattern).
        """
        if cls._instance is None:
            cls._instance = super(ArctosController, cls).__new__(cls)
        return cls._instance

    def __init__(self, encoder_resolution: int = 16384, can_interface: str = "slcan0", bitrate: int = 500000):
        """
        Initializes the CAN interface, servos, and gear ratio settings.
        
        :param encoder_resolution: Encoder resolution per revolution.
        :param can_interface: Name of the CAN interface (default "slcan0").
        :param bitrate: CAN bus bitrate (default 500000).
        """
        if hasattr(self, "initialized"):  # Prevent re-initialization
            return
        self.initialized = True  # Set initialization flag

        self.can_interface = can_interface
        self.bitrate = bitrate
        self.encoder_resolution = encoder_resolution
        self.servos = []
        self.gear_ratios = [13.5, 150, 150, 48, (67.82 / 2.1), (67.82 / 2.1)]  # Gear ratios for each joint

        # Initialize CAN Bus
        self.bus = self.initialize_can_bus()

        # Initialize Servos
        self.servos = self.initialize_servos()

        self.current_joint_angle = [0, 0, 0, 0, 0, 0]  # Store current joint angles

    def angle_to_encoder(self, angle_rad: float, axis_index: int) -> int:
        """
        Converts a joint angle (radians) to an encoder value for a given axis.
        
        :param angle_rad: Angle in radians.
        :param axis_index: Index of the axis.
        :return: Corresponding encoder value.
        """
        gear_ratio = self.gear_ratios[axis_index]
        encoder_value = int((angle_rad / (2 * math.pi)) * self.encoder_resolution * gear_ratio)
        return encoder_value
    
    def encoder_to_angle(self, encoder_value: int, axis_index: int) -> float:
        """
        Converts an encoder value to a joint angle (radians) for a given axis.
        
        :param encoder_value: Encoder reading.
        :param axis_index: Index of the axis.
        :return: Angle in radians.
        """
        gear_ratio = self.gear_ratios[axis_index]
        angle_rad = (encoder_value / (self.encoder_resolution * gear_ratio)) * (2 * math.pi)
        return angle_rad

    def initialize_servos(self):
        """
        Initializes the servos connected to the CAN bus.
        
        :return: List of initialized servo objects.
        """
        notifier = can.Notifier(self.bus, [])  # CAN bus notifier (could add filters)

        servos = [
            mks_servo.MksServo(self.bus, notifier, i) for i in range(1, 7)
        ]

        # Enable limit ports from Servo 3 (Index 2) onwards
        for servo in servos[2:]:
            servo.set_limit_port_remap(Enable.Enable)
            time.sleep(0.1)

        #servos[3].set_working_current(2800)
        #servos[3].set_home(EndStopLevel.Low, Direction.CCW, homeSpeed=140, endLimit=Enable.Enable)

        # servos[4].set_motor_shaft_locked_rotor_protection(Enable.Disable)
        # servos[5].set_motor_shaft_locked_rotor_protection(Enable.Disable)
        # servos[4].set_working_current(2000)
        # servos[5].set_working_current(2000)
        print("Servos successfully initialized.")
        return servos

    def move_to_angles(self, angles_rad: list, speed: int = 400, acceleration: int = 100) -> None:
        """
        Moves all joints of the robot to the specified angles.
        
        :param angles_rad: List of angles (in radians) for each joint.
        :param speed: Motor speed (0-3000 RPM, default 400).
        :param acceleration: Acceleration (0-255, default 100).
        """
        for i, angle_rad in enumerate(angles_rad):
            encoder_value = self.angle_to_encoder(angle_rad, i)
            print(f"Axis {i}: Angle {math.degrees(angle_rad)}° -> Encoder value {encoder_value}")
            self.servos[i].run_motor_absolute_motion_by_axis(speed, acceleration, encoder_value)

    def set_joint_angles(self) -> None:
        """
        Reads the current joint angles from the encoder values and stores them.
        """
        for i, servo in enumerate(self.servos):
            encoder_value = servo.read_encoder_value_addition()  # Read encoder value
            angle_rad = self.encoder_to_angle(encoder_value, i)  # Convert to radians
            self.current_joint_angle[i] = angle_rad  # Store joint angle
            print(f"Axis {i}: Encoder Value = {encoder_value}, Angle = {math.degrees(angle_rad):.2f}°")

    def initialize_can_bus(self):
        """
        Initializes the CAN bus interface and ensures it is active.
        
        :return: Initialized CAN bus object.
        """
        if not self.is_can_interface_up():
            print(f"CAN interface {self.can_interface} not active. Starting it...")
            self.setup_can_interface()

        try:
            bus = can.interface.Bus(bustype="socketcan", channel=self.can_interface)
            print(f"CAN bus successfully initialized on {self.can_interface} with {self.bitrate} baud rate.")
            return bus
        except Exception as e:
            print(f"Error initializing CAN bus: {e}")
            raise RuntimeError("Error initializing CAN bus.")

    def is_can_interface_up(self) -> bool:
        """
        Checks whether the specified CAN interface is active.
        
        :return: True if the interface is active, False otherwise.
        """
        result = os.system(f"ip link show {self.can_interface} > /dev/null 2>&1")
        return result == 0  # 0 means the interface exists

    def setup_can_interface(self) -> None:
        """
        Configures and starts the CAN interface (`slcan`) on `ttyACM0`.
        """
        print("Starting slcan for ttyACM0...")
        os.system("sudo modprobe can")
        os.system("sudo modprobe can_raw")
        os.system("sudo modprobe slcan")
        os.system("sudo slcand -o -c -s6 /dev/ttyACM0 slcan0") 
        os.system("sudo ip link set slcan0 up")
        time.sleep(1)  # Wait to ensure stability



    def send_can_message_gripper(self, bus: can.Bus, arbitration_id: int, data: List[int]) -> None:
        """
        Sends a CAN message with the given arbitration ID and data.
        
        :param bus: The CAN bus to send the message on.
        :param arbitration_id: The identifier of the CAN message.
        :param data: A list of integers representing the message payload.
        :raises can.CanError: If there is an issue sending the CAN message.
        """
        try:
            msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
            bus.send(msg)
            data_bytes = ', '.join([f'0x{byte:02X}' for byte in msg.data])
            print(f"Sent CAN message: ID=0x{msg.arbitration_id:X}, Data=[{data_bytes}]")
            time.sleep(0.5)  # Delay of 500 ms to allow for processing
        except can.CanError as e:
            print(f"Error sending CAN message: {e}")

    def open_gripper(self) -> None:
        """
        Sends a command to open the gripper.
        
        :raises Exception: If there is an issue sending the command.
        """
        try:
            self.send_can_message_gripper(self.bus, 0x07, [0xFF])
            print("Gripper opened.")
        except Exception as e:
            print(f"Error sending open gripper command: {e}")

    def close_gripper(self) -> None:
        """
        Sends a command to close the gripper.
        
        :raises Exception: If there is an issue sending the command.
        """
        try:
            self.send_can_message_gripper(self.bus, 0x07, [0x00])
            print("Gripper closed.")
        except Exception as e:
            print(f"Error sending close gripper command: {e}")