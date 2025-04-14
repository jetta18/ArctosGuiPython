"""
This module contains the ArctosController class, which manages communication with the robotic arm servos via CAN bus.

It provides functionalities for initializing the CAN bus, managing servo motors, converting between joint angles and
encoder values, and moving the robot's joints. This module also implements a Singleton pattern to ensure that only
one instance of ArctosController manages the servos at any given time.
"""
import math
import can
import time
import subprocess
from typing import List, Optional
import logging
from services.mks_servo_can import mks_servo
from services.mks_servo_can.mks_enums import Enable, Direction, EndStopLevel
import concurrent.futures
import platform
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.config.settings import Settings


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ArctosController:
    """
    Manages communication with the robotic arm servos via the CAN bus.

    The `ArctosController` class handles the low-level control of the robotic arm, including
    initialization of the CAN bus interface, servo motor management, and conversion between
    encoder values and joint angles. It provides methods for moving the robot's joints and
    interacting with the gripper. This class follows the Singleton design pattern to ensure
    that only one instance manages the servos.
    """
    _instance = None  #: Stores the Singleton instance.

    def __new__(cls, *args, **kwargs):
        """
        Ensures that only a single instance of `ArctosController` is created (Singleton pattern).

        If an instance already exists, it returns the existing instance. Otherwise, it creates a new instance.

        Returns:
            ArctosController: The Singleton instance of ArctosController.
        """
        if cls._instance is None:
            cls._instance = super(ArctosController, cls).__new__(cls)
        return cls._instance

    def __init__(self, encoder_resolution: int = 16384, bitrate: int = 500000, settings_manager: Optional["Settings"] = None):
        """
        Initializes the CAN interface, servo motors, and gear ratio settings.

        This constructor initializes the CAN bus communication interface, sets up servo motors,
        and configures the gear ratios for each joint of the robotic arm. It also supports
        inversion of joint directions through a settings manager.

        Args:
            encoder_resolution (int, optional): Encoder resolution per revolution. Defaults to 16384.
            bitrate (int, optional): CAN bus bitrate. Defaults to 500000.
            settings_manager (Optional[Settings], optional): An instance of a settings manager
                that can provide joint direction settings. Defaults to None.

        Raises:
            RuntimeError: If the CAN interface is not available or if there is an error initializing the CAN bus.
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
        #self.bus = self.initialize_can_bus()

        # Initialize Servos
        #self.servos = self.initialize_servos()

    def angle_to_encoder(self, angle_rad: float, axis_index: int) -> int:  # Correct the return type here
        """
        Converts a joint angle from radians to an encoder value for a given axis.

        This method calculates the corresponding encoder value for a given joint angle.
        The calculation takes into account the gear ratio and encoder resolution.

        Args:
            angle_rad (float): The joint angle in radians.
            axis_index (int): The index of the axis (joint) for which to convert the angle.

        Returns:
            int: The calculated encoder value for the given joint angle.
        """
        gear_ratio = self.gear_ratios[axis_index]
        encoder_value = int((angle_rad / (2 * math.pi)) * self.encoder_resolution * gear_ratio)
        return encoder_value

    def encoder_to_angle(self, encoder_value: int, axis_index: int) -> float:
        """
        Converts an encoder value to a joint angle in radians for a given axis.

        This method calculates the corresponding joint angle in radians for a given encoder value.
        The calculation accounts for the gear ratio and encoder resolution.
        
        :param encoder_value: Encoder reading.
        :param axis_index: Index of the axis.
        :return: Angle in radians.
        """
        gear_ratio = self.gear_ratios[axis_index]
        angle_rad = (encoder_value / (self.encoder_resolution * gear_ratio)) * (2 * math.pi)
        return angle_rad

    def initialize_servos(self):
        """
        Initializes the servo motors connected to the CAN bus.

        This method initializes each servo motor connected to the CAN bus. It configures
        the limit port on servos 3 through 6.
        
        Returns:
            List[mks_servo.MksServo]: A list of initialized servo motor objects.
        Raises:
            Exception: If there is an error during the initialization of a servo motor.
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
        Moves the robot's joints to the specified angles.

        This method moves each joint of the robotic arm to the target angles, specified in radians.
        It handles the coupling of the B and C axes (servos 4 and 5) to generate the correct target angle.
        The movement is performed in parallel for all axes to minimize the total execution time.

        Args:
            angles_rad (list): A list of angles in radians for each joint.
            speed (int, optional): The speed of the motor movement. Ranges from 0 to 3000 RPM.
                Defaults to 500.
            acceleration (int, optional): The acceleration of the motor movement. Ranges from 0 to 255.
                Defaults to 150.
        """

        def move_servo(i, angle_rad):
            """
            Helper function to move a single servo to the target angle.
            """
            encoder_value = self.angle_to_encoder(angle_rad, i)
            logger.debug(f"Axis {i}: Angle {math.degrees(angle_rad):.2f}° -> Encoder value {encoder_value}")
            self.servos[i].run_motor_absolute_motion_by_axis(speed, acceleration, encoder_value)

        # Calculate the target angles for the B and C axes, which are coupled to axes 4 and 5
        # B-axis and C-axis coupling calculation
        # B-axis (servo 6) = angles_rad[5] + angles_rad[4]
        # C-axis (servo 5) = angles_rad[4] - angles_rad[5]
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

        # Move all axes simultaneously using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(move_servo, range(len(self.servos)), final_angles)

    def get_joint_angles(self) -> List[float]:
        """
        Retrieves the current joint angles of the robot.

        This method reads the current joint angles from the encoder values of each servo motor.
        It utilizes parallel execution with `ThreadPoolExecutor` to send all CAN requests
        concurrently, thus reducing the overall execution time.

        The method handles potential errors during encoder reading by logging an error message
        and setting the corresponding joint angle to a default value of 0.

        Raises:
            Exception: If there is an error during encoder reading for a joint.

        Returns:
            list[float]: A list containing the current joint angles in radians.
        """

        def read_encoder(i, servo):
            """Helper function to read encoder value with error handling."""
            try:
                encoder_value = servo.read_encoder_value_addition()  # type: ignore
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
        Initializes the CAN bus interface.

        This method initializes the CAN bus interface, sets the bitrate, and ensures that the
        CAN interface is active. If the CAN interface is not active, it logs an error and raises
        a `RuntimeError`.

        Returns:
            can.Bus: The initialized CAN bus object.
        Raises:
            RuntimeError: If the CAN interface is not active or if there is an error initializing the CAN bus.
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
        Checks if the specified CAN interface is active.

        This method checks the status of the CAN interface. On Windows, it checks if the COM port
        is available in the list of serial ports. On Linux, it uses the `ip link show` command to
        check if the interface is up.

        Returns:
            bool: True if the interface is active, False otherwise.
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


    def send_can_message_gripper(self, bus: can.Bus, arbitration_id: int, data: List[int]) -> None:  # Add type hint for 'bus'
        """
        Sends a CAN message to control the gripper.

        This method sends a CAN message with the specified arbitration ID and data to control
        the gripper. It handles the message sending process and logs the sent message details.
        It includes a delay of 500 ms after sending the message to allow for processing.

        Args:
            bus (can.Bus): The CAN bus object to send the message on.
            arbitration_id (int): The arbitration ID of the CAN message.
            data (List[int]): A list of integers representing the data payload of the CAN message.

        Raises:
            can.CanError: If there is an issue sending the CAN message.
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
        Opens the gripper.

        Sends a CAN command to open the robot's gripper.

        Raises:
            Exception: If there is an issue sending the open gripper command.

        """
        try:
            self.send_can_message_gripper(self.bus, 0x07, [0xFF])
            logger.debug("Gripper opened.")
        except Exception as e:
            logger.debug(f"Error sending open gripper command: {e}")

    def close_gripper(self) -> None:
        """
        Closes the gripper.

        Sends a CAN command to close the robot's gripper.

        Raises:
            Exception: If there is an issue sending the close gripper command.

        """
        try:
            self.send_can_message_gripper(self.bus, 0x07, [0x00])
            logger.debug("Gripper closed.")
        except Exception as e:
            logger.debug(f"Error sending close gripper command: {e}")

    def wait_for_motors_to_stop(self) -> None:
        """
        Waits until all motors have stopped moving.

        This method continuously checks the state of each servo motor to see if it is still running.
        It waits until all motors have stopped moving before returning. This is useful to ensure that
        all motions have completed before proceeding to the next operation.

        """
        while any(servo.is_motor_running() for servo in self.servos):
            logger.debug("Motors are still running. Waiting...")
            time.sleep(0.5)  # Wait before checking again

    def is_motor_running(self) -> bool:
        """
        Check if any motor is still running.

        Returns:
            True if any motor is running. False if no motor is running.
        """
        if any(servo.is_motor_running() for servo in self.servos):
            return True
        else:
            return False