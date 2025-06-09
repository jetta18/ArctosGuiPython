"""
This module contains the ArctosController class, which manages communication with the robotic arm servos via CAN bus.

It provides functionalities for initializing the CAN bus, managing servo motors, converting between joint angles and
encoder values, and moving the robot's joints. This module also implements a Singleton pattern to ensure that only
one instance of ArctosController manages the servos at any given time.
"""
import math
import can
import time
from typing import List
import logging
from services.mks_servo_can import mks_servo
from services.mks_servo_can.mks_enums import Enable
import concurrent.futures
from .CanBusManager import CanBusManager

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

    def __init__(self, can_bus_manager: CanBusManager = None, settings_manager = None):
        """
        Initializes the CAN interface, servo motors, and gear ratio settings.

        This constructor initializes the CAN bus communication interface, sets up servo motors,
        and configures the gear ratios for each joint of the robotic arm. It also supports
        inversion of joint directions through a settings manager.

        Args:
            can_bus_manager (CanBusManager, optional): An instance of a CanBusManager. Defaults to None.
            settings_manager (Optional[Settings], optional): An instance of a settings manager
                that can provide joint direction settings. Defaults to None.

        Raises:
            RuntimeError: If the CAN interface is not available or if there is an error initializing the CAN bus.
        """
        if hasattr(self, "initialized"):  # Prevent re-initialization
            return
        self.initialized = True  # Set initialization flag            
        self.encoder_resolution = 16384
        default_ratios = [13.5, 150, 150, 48, 33.91, 33.91]

        if settings_manager:
            base_ratios = settings_manager.get("gear_ratios", default_ratios)
            directions = settings_manager.get("joint_directions", {i: 1 for i in range(6)})
            self.settings_manager = settings_manager  # Store reference to settings manager
        else:
            base_ratios = default_ratios
            directions = {i: 1 for i in range(6)}
            self.settings_manager = None

        # Apply sign for inverted axes
        self.gear_ratios = [gr * directions.get(i, 1) for i, gr in enumerate(base_ratios)]

        # Initialize CAN bus manager
        self.can_bus_manager = can_bus_manager
        try:
            self.bus = self.can_bus_manager.initialize()
        except Exception as e:
            logger.warning(f"CAN bus initialization failed: {e}")
            self.bus = None

        # Robust Servo initialization
        if self.bus is not None:
            try:
                self.servos = self.initialize_servos()
            except Exception as e:
                logger.warning(f"Servo initialization failed: {e}")
                self.servos = []
        else:
            self.servos = []
            
        # Create a persistent thread pool for motor commands
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=6)
        self.pending_futures = []

    def angle_to_encoder(self, angle_rad: float, axis_index: int) -> int:  
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
        logger.info("🔧 Initializing servos...")
        start_time = time.time()

        try:
            notifier = can.Notifier(self.bus, [])
        except Exception as e:
            logger.error(f"❌ Failed to create CAN notifier: {e}")
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
                logger.error(f"⚠️ Failed to enable limit port on Servo {index}: {e}")

        duration = time.time() - start_time
        logger.info(f"✅ All servos initialized in {duration:.2f} seconds.")
        return servos

    def move_to_angles(
        self,
        angles_rad: list[float],
        *,
        speeds: int | list[int] = 500,
        acceleration: int | list[int] = 150,
    ) -> None:
        """
        Move all robot joints to the specified target angles with optional per-joint speeds and accelerations.

        If coupled_axis_mode is enabled in settings, axes 4 and 5 will be treated as coupled B and C axes.
        B = axis4 + axis5
        C = axis4 - axis5

        Args:
            angles_rad (list[float]):
                Target joint angles in radians. Must be a list of exactly six values.
                When in coupled_axis_mode, angles_rad[4] and angles_rad[5] are treated as B and C axes.
            speeds (int | list[int], optional):
                Either a single global speed in RPM (applied to all joints),
                or a list of six individual speeds (one per joint).
                Each value is clamped to the valid servo range [0, 3000]. Defaults to 500.
            acceleration (int | list[int], optional):
                Either a single global acceleration value (applied to all joints),
                or a list of six individual acceleration values (one per joint).
                Each value is clamped to the firmware-supported range [0, 255]. Defaults to 150.

        Raises:
            ValueError: If `angles_rad` does not contain exactly 6 values.

        Returns:
            None
        """
        if len(angles_rad) != 6:
            raise ValueError("'angles_rad' must contain 6 joint values")

        # --- Normalize speeds --------------------------------------------------
        speed_scale = self.settings_manager.get("speed_scale", 1.0) if hasattr(self, 'settings_manager') else 1.0
        speed_list = [max(0, min(int(s * speed_scale), 3000)) for s in speeds]
        acc_list = [max(0, min(int(a), 255)) for a in acceleration]

        # Check if we should use coupled axis mode
        coupled_mode = False
        if hasattr(self, 'settings_manager'):
            coupled_mode = self.settings_manager.get("coupled_axis_mode", False)

        # Handle coupled axis mode if enabled
        if coupled_mode:
            # Calculate B and C axes from axes 4 and 5
            b_axis = angles_rad[4] + angles_rad[5]
            c_axis = angles_rad[4] - angles_rad[5]
            # Create a copy of the angles list and update axes 4 and 5
            angles_rad = list(angles_rad)
            angles_rad[4] = b_axis
            angles_rad[5] = c_axis

        # --- Cancel any pending futures to prevent queuing commands ------------
        if hasattr(self, 'pending_futures'):
            for future in self.pending_futures:
                if not future.done():
                    future.cancel()
            self.pending_futures = []

        # --- Move Helper -------------------------------------------------------
        def _move_servo(i: int, angle_rad: float) -> None:
            encoder_val = self.angle_to_encoder(angle_rad, i)
            logger.debug(
                f"Axis {i}: {math.degrees(angle_rad):.2f}° -> enc {encoder_val} @ {speed_list[i]} RPM / accel {acc_list[i]}"
            )
            
            # Send the new motion command
            self.servos[i].run_motor_absolute_motion_by_axis(
                speed_list[i], acc_list[i], encoder_val
            )

        # --- Execute in parallel -----------------------------------------------
        # Submit new tasks to the persistent thread pool
        futures = [
            self.thread_pool.submit(_move_servo, i, angle) 
            for i, angle in enumerate(angles_rad)
        ]
        
        # Add new futures to the pending list
        self.pending_futures = futures

    def _read_encoder_with_fallback(self, i: int, servo) -> int:
        """Reads encoder value for a single axis with fallback to 0 on failure."""
        try:
            encoder_value = servo.read_encoder_value_addition()  # type: ignore
            if encoder_value is None:
                logger.warning(f"Failed to read encoder value for Axis {i}, setting to 0.")
                return 0
            return encoder_value
        except Exception as e:
            logger.warning(f"Error reading encoder for Axis {i}: {e}")
            return 0

    def get_joint_angles(self) -> List[float]:
        """
        Retrieves the current joint angles of the robot.

        This method reads the current joint angles from the encoder values of each servo motor
        in a serial manner to reduce CAN bus contention and improve reliability.

        If reading fails, the corresponding joint angle is set to 0 and a warning is logged.

        Returns:
            list[float]: A list containing the current joint angles in radians.
        """
        current_joint_angle = []
        for i, servo in enumerate(self.servos):
            encoder_value = self._read_encoder_with_fallback(i, servo)
            angle_rad = self.encoder_to_angle(encoder_value, i)
            current_joint_angle.append(angle_rad)
            logger.debug(f"Axis {i}: Encoder = {encoder_value}, Angle = {angle_rad:.4f} rad")

        return current_joint_angle


    def send_can_message_gripper(self, bus: can.Bus, arbitration_id: int, data: List[int]) -> None:  
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
        
    def set_gear_ratios(self, ratios: list[float], directions: dict[int, int] | None = None) -> None:
        """
        Update gear ratios at runtime. Optionally apply direction signs again.
        """
        if directions is None:
            directions = {i: 1 for i in range(6)}
        self.gear_ratios = [gr * directions.get(i, 1) for i, gr in enumerate(ratios)]
        logger.debug(f"Gear ratios updated: {self.gear_ratios}")

    def emergency_stop(self) -> None:
        """
        Immediately stops all motors by sending the emergency stop command to each servo.

        This method should be called in case of emergency to halt all robot motion.
        Logs the result of each stop attempt.
        """
        if not hasattr(self, 'servos') or self.servos is None:
            logger.error("No servos initialized for emergency stop!")
            return
        for i, servo in enumerate(self.servos):
            try:
                result = servo.emergency_stop_motor()
                logger.debug(f"Emergency stop sent to servo {i}: {result}")
            except Exception as e:
                logger.error(f"Failed to send emergency stop to servo {i}: {e}")

    def safe_emergency_stop(self) -> None:
        """
        Performs a safe emergency stop:
        - If any motor is above 1000 RPM, decelerates all motors to zero using maximum acceleration.
        - Otherwise, performs a normal emergency stop.
        Logs actions and errors.
        """
        from services.mks_servo_can.can_motor import MAX_ACCELERATION
        from services.mks_servo_can.mks_enums import Direction
        high_rpm_detected = False
        rpm_list = []
        if not hasattr(self, 'servos') or self.servos is None:
            logger.error("No servos initialized for safe emergency stop!")
            return
        # Read all motor speeds
        for i, servo in enumerate(self.servos):
            try:
                rpm = servo.read_motor_speed()
                rpm_list.append(rpm)
                if rpm is not None and abs(rpm) > 1000:
                    high_rpm_detected = True
            except Exception as e:
                logger.error(f"Failed to read RPM from servo {i}: {e}")
                rpm_list.append(None)
        if high_rpm_detected:
            logger.warning("High RPM detected. Decelerating motors safely.")
            for i, (servo, rpm) in enumerate(zip(self.servos, rpm_list)):
                try:
                    if rpm is None:
                        logger.warning(f"Servo {i}: RPM unknown, skipping deceleration.")
                        continue
                    direction = Direction.CCW if rpm > 0 else Direction.CW
                    # Command motor to zero speed with max acceleration
                    result = servo.run_motor_in_speed_mode(direction, 0, MAX_ACCELERATION)
                    logger.debug(f"Servo {i}: Decelerate to 0 RPM with MAX_ACCELERATION. Result: {result}")
                except Exception as e:
                    logger.error(f"Servo {i}: Failed to decelerate safely: {e}")
        else:
            logger.debug("All motors below 1000 RPM. Performing normal emergency stop.")
            self.emergency_stop()

    def __del__(self):
        """Clean up resources when the object is destroyed."""
        if hasattr(self, "thread_pool"):
            self.thread_pool.shutdown(wait=True)
        # Clean up CAN bus manager if it exists
        if hasattr(self, "can_bus_manager"):
            self.can_bus_manager.shutdown()
