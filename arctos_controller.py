import math
import can
import os
import time
import glob
from typing import List
import logging
from mks_servo_can import mks_servo
from mks_servo_can.mks_enums import Enable, Direction, EndStopLevel


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  

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
        self.gear_ratios = [13.5, -150, -150, 48, -(67.82 / 2.1), (67.82 / 2.1)]  # Gear ratios for each joint

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

        logger.debug("Servos successfully initialized.")
        return servos

    def move_to_angles(self, angles_rad: list, speed: int = 750, acceleration: int = 120) -> None:
        """
        Moves all joints of the robot to the specified angles.
        
        :param angles_rad: List of angles (in radians) for each joint.
        :param speed: Motor speed (0-3000 RPM, default 400).
        :param acceleration: Acceleration (0-255, default 100).
        """
        # Berechne B- und C-Achse aus den Achsen 4 und 5
        b_axis = angles_rad[5] + angles_rad[4]
        c_axis = angles_rad[4] - angles_rad[5]
        
        # Erstelle die finale Winkel-Liste mit der gewünschten Vorzeichenlogik
        final_angles = [
            angles_rad[0],         # A0
            angles_rad[1],        # A1
            angles_rad[2],        # A2
            angles_rad[3],         # A3
            b_axis,               # B-Achse (kopplung)
            c_axis                 # C-Achse (kopplung)
        ]
        
        # Fahre alle Achsen anhand der finalen Winkel an
        for i, angle_rad in enumerate(final_angles):
            encoder_value = self.angle_to_encoder(angle_rad, i)
            logger.debug(f"Axis {i}: Angle {math.degrees(angle_rad):.2f}° -> Encoder value {encoder_value}")
            self.servos[i].run_motor_absolute_motion_by_axis(speed, acceleration, encoder_value)

    def get_joint_angles(self) -> list[float]:
        """
        Reads the current joint angles from the encoder values and stores them.

        This function iterates over all servos, reads their encoder values, 
        converts these values into radians, and stores the resulting angles 
        in a list. Additionally, it logs each axis's encoder value and the 
        corresponding angle in degrees.

        Returns:
            list[float]: A list containing the current joint angles in radians.
        """
        current_joint_angle = []  # Initialize an empty list to store angles

        for i, servo in enumerate(self.servos):
            encoder_value = servo.read_encoder_value_addition()  # Read encoder value
            time.sleep(0.2)
            angle_rad = self.encoder_to_angle(encoder_value, i)  # Convert to radians
            current_joint_angle.append(angle_rad)  # Store joint angle

            logger.debug(f"Axis {i}: Encoder Value = {encoder_value}, Angle = {math.degrees(angle_rad):.2f}°")

        return current_joint_angle

    def initialize_can_bus(self):
        """
        Initializes the CAN bus interface and ensures it is active.
        
        :return: Initialized CAN bus object.
        """
        if not self.is_can_interface_up():
            logger.debug(f"CAN interface {self.can_interface} not active. Starting it...")
            self.setup_can_interface()

        try:
            bus = can.interface.Bus(bustype="socketcan", channel=self.can_interface)
            logger.debug(f"CAN bus successfully initialized on {self.can_interface} with {self.bitrate} baud rate.")
            return bus
        except Exception as e:
            logger.debug(f"Error initializing CAN bus: {e}")
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
        Configures and initializes the CAN interface (`slcan`) dynamically by detecting available `ttyACM*` ports.
        
        This method scans for connected `ttyACM*` devices, which represent USB-to-CAN adapters (e.g., CANable devices). 
        It then attempts to configure and activate the CAN interface on each detected device.
        
        The following steps are executed:
        1. Identify all available `ttyACM*` devices.
        2. Iterate over the detected devices and try to configure each one.
        3. Ensure that any previously running `slcand` process is stopped before initializing a new one.
        4. Load the necessary kernel modules for CAN communication.
        5. Start `slcand` with the detected `ttyACM*` port and set up the CAN interface.
        6. Verify if the `slcan0` interface is successfully created and activated.
        7. If a working interface is found, exit the function; otherwise, log an error.

        If no `ttyACM*` device is detected, or if all initialization attempts fail, an error message is logged.

        Note: This function requires root privileges to execute system commands like `modprobe` and `ip link set`.
        """
        # Search for all available ttyACM* devices
        tty_ports = glob.glob("/dev/ttyACM*")

        if not tty_ports:
            logger.error("No ttyACM* device found! Make sure your CANable device is properly connected.")
            return

        # Try to configure each detected device
        for tty_port in tty_ports:
            logger.debug(f"Attempting to set up CAN interface on: {tty_port}")

            # Ensure any existing slcan0 interface is disabled before reconfiguring
            os.system("sudo ip link set slcan0 down")
            os.system("sudo killall slcand")
            time.sleep(1)

            # Load necessary kernel modules
            os.system("sudo modprobe can")
            os.system("sudo modprobe can_raw")
            os.system("sudo modprobe slcan")

            # Start slcand for the detected device
            os.system(f"sudo slcand -o -c -s6 {tty_port} slcan0")
            os.system("sudo ip link set slcan0 up")
            time.sleep(1)

            # Check if the interface is successfully created
            result = os.system("ip link show slcan0 > /dev/null 2>&1")
            if result == 0:
                logger.debug(f"CAN interface successfully set up on {tty_port}.")
                return  # Exit function once a working interface is found

        logger.error("Failed to initialize a functional CAN interface. Please check your device connection and permissions.")


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
            logger.debug(f"Sent CAN message: ID=0x{msg.arbitration_id:X}, Data=[{data_bytes}]")
            time.sleep(0.5)  # Delay of 500 ms to allow for processing
        except can.CanError as e:
            logger.debug(f"Error sending CAN message: {e}")

    def open_gripper(self) -> None:
        """
        Sends a command to open the gripper.
        
        :raises Exception: If there is an issue sending the command.
        """
        try:
            self.send_can_message_gripper(self.bus, 0x07, [0xFF])
            logger.debug("Gripper opened.")
        except Exception as e:
            logger.debug(f"Error sending open gripper command: {e}")

    def close_gripper(self) -> None:
        """
        Sends a command to close the gripper.
        
        :raises Exception: If there is an issue sending the command.
        """
        try:
            self.send_can_message_gripper(self.bus, 0x07, [0x00])
            logger.debug("Gripper closed.")
        except Exception as e:
            logger.debug(f"Error sending close gripper command: {e}")

    def wait_for_motors_to_stop(self) -> None:
        """
        Waits until all motors stop moving before proceeding.
        
        This function continuously checks if any motor is still running and waits until all motors have stopped before returning.
        
        :param Arctos: Instance of the robot controller containing servo objects.
        """
        while any(servo.is_motor_running() for servo in self.servos):
            logger.debug("Motors are still running. Waiting...")
            time.sleep(0.5)  # Wait before checking again
    
    def is_motor_running(self) -> bool:
        if any(servo.is_motor_running() for servo in self.servos):
            return True
        else:
            return False