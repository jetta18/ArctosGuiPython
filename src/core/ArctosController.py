import math
import can
import time
import subprocess
from typing import List
import logging
from services.mks_servo_can import mks_servo
from services.mks_servo_can.mks_enums import Enable, Direction, EndStopLevel
import concurrent.futures
import platform


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

    def __init__(self, encoder_resolution: int = 16384, bitrate: int = 500000, settings_manager=None):
        """
        Initializes the CAN interface, servos, and gear ratio settings.
        
        :param encoder_resolution: Encoder resolution per revolution.
        :param bitrate: CAN bus bitrate (default 500000).
        """
        if hasattr(self, "initialized"):  # Prevent re-initialization
            return
        self.initialized = True  # Set initialization flag

        if platform.system() == "Windows":
            can_interface = "COM5"  # oder aus einer Config-Datei laden
        else:
            can_interface = "can0"

        self.can_interface = can_interface
        self.bitrate = bitrate
        self.encoder_resolution = encoder_resolution
        self.servos = []
        self.gear_ratios = [13.5, 150, 150, 48, (67.82 / 2), (67.82 / 2)]  # Gear ratios for each joint

        # ✅ Apply direction inversion if settings_manager is provided
        if settings_manager:
            directions = settings_manager.get("joint_directions") or {i: 1 for i in range(6)}
            self.gear_ratios = [gr * directions.get(i, 1) for i, gr in enumerate(self.gear_ratios)]

        # Initialize CAN Bus
        self.bus = self.initialize_can_bus()

        # Initialize Servos
        self.servos = self.initialize_servos()

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
        Initializes the servos connected to the CAN bus with detailed debug logging.

        :return: List of initialized servo objects.
        """
        logger.debug("🔧 Initializing servos...")
        start_time = time.time()

        try:
            notifier = can.Notifier(self.bus, [])
        except Exception as e:
            logger.debug(f"❌ Failed to create CAN notifier: {e}")
            raise

        servos = []
        for i in range(1, 7):
            try:
                logger.debug(f"🔹 Creating servo instance for ID {i}")
                servo = mks_servo.MksServo(self.bus, notifier, i)
                servos.append(servo)
                logger.debug(f"✅ Servo {i} initialized.")
            except Exception as e:
                logger.debug(f"❌ Failed to initialize servo ID {i}: {e}")
                raise

        # Enable limit ports on servos 3–6 (Index 2 and above)
        for index, servo in enumerate(servos[2:], start=3):
            try:
                logger.debug(f"🔸 Enabling limit port on Servo {index}")
                servo.set_limit_port_remap(Enable.Enable)
                time.sleep(0.1)
                logger.debug(f"✅ Limit port enabled on Servo {index}")
            except Exception as e:
                logger.debug(f"⚠️ Failed to enable limit port on Servo {index}: {e}")

        duration = time.time() - start_time
        logger.debug(f"✅ All servos initialized in {duration:.2f} seconds.")
        return servos

    def move_to_angles(self, angles_rad: list, speed: int = 500, acceleration: int = 150) -> None:
        """
        Moves all joints of the robot to the specified angles in parallel.
        
        :param angles_rad: List of angles (in radians) for each joint.
        :param speed: Motor speed (0-3000 RPM, default 750).
        :param acceleration: Acceleration (0-255, default 120).
        """

        # Berechne B- und C-Achse aus den Achsen 4 und 5
        b_axis = angles_rad[5] + angles_rad[4]
        c_axis = angles_rad[4] - angles_rad[5]

        # Erstelle die finale Winkel-Liste mit der gewünschten Vorzeichenlogik
        final_angles = [
            angles_rad[0],  # A0
            angles_rad[1],  # A1
            angles_rad[2],  # A2
            angles_rad[3],  # A3
            b_axis,         # B-Achse (kopplung)
            c_axis          # C-Achse (kopplung)
        ]

        def move_servo(i, angle_rad):
            """Helper function to move a single servo."""
            encoder_value = self.angle_to_encoder(angle_rad, i)
            logger.debug(f"Axis {i}: Angle {math.degrees(angle_rad):.2f}° -> Encoder value {encoder_value}")
            self.servos[i].run_motor_absolute_motion_by_axis(speed, acceleration, encoder_value)

        # Starte alle Achsenbewegungen gleichzeitig mit ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(move_servo, range(len(self.servos)), final_angles)

    def get_joint_angles(self) -> list[float]:
        """
        Reads the current joint angles from the encoder values and stores them.

        This function now runs all CAN requests in parallel using ThreadPoolExecutor,
        significantly reducing execution time.

        Returns:
            list[float]: A list containing the current joint angles in radians.
        """

        def read_encoder(i, servo):
            """Helper function to read encoder value with error handling."""
            try:
                encoder_value = servo.read_encoder_value_addition()
                if encoder_value is None:
                    logger.error(f"Failed to read encoder value for Axis {i}, setting to 0.")
                    return 0  # Set default value if no response
                return encoder_value
            except Exception as e:
                logger.error(f"Error reading encoder for Axis {i}: {e}")
                return 0  # Default value in case of an error

        # Parallelisiere das Einlesen der Encoder-Werte
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(read_encoder, range(len(self.servos)), self.servos))

        # Konvertiere Encoder-Werte in Gelenkwinkel
        current_joint_angle = []
        for i, encoder_value in enumerate(results):
            angle_rad = self.encoder_to_angle(encoder_value, i)
            current_joint_angle.append(angle_rad)
            logger.debug(f"Axis {i}: Encoder Value = {encoder_value}, Angle = {angle_rad:.6f} rad")

        return current_joint_angle

    def initialize_can_bus(self):
        """
        Initializes the CAN bus interface and ensures it is active.
        
        :return: Initialized CAN bus object.
        """
        if not self.is_can_interface_up():
            logger.error(f"CAN interface {self.can_interface} is not active. Please run 'setup_canable.sh' first.")
            raise RuntimeError("CAN interface is not available.")

        try:
            if platform.system() == "Windows":
                bus = can.interface.Bus(bustype="slcan", channel=self.can_interface, bitrate=self.bitrate)
            else:
                bus = can.interface.Bus(bustype="socketcan", channel=self.can_interface)

            logger.info(f"CAN bus successfully initialized on {self.can_interface} with bitrate {self.bitrate}.")
            return bus
        except Exception as e:
            logger.error(f"Error initializing CAN bus: {e}")
            raise RuntimeError("Error initializing CAN bus.")


    def is_can_interface_up(self) -> bool:
        """
        Checks whether the specified CAN interface is active.

        :return: True if the interface is active, False otherwise.
        """
        if platform.system() == "Windows":
            # On Windows, we assume the COM port is available if it appears in the port list
            import serial.tools.list_ports
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return self.can_interface in ports
        else:
            try:
                result = subprocess.run(["ip", "link", "show", self.can_interface], capture_output=True, text=True)
                return "UP" in result.stdout
            except Exception as e:
                logger.error(f"Error checking CAN interface: {e}")
            return False



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