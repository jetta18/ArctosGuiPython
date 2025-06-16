import numpy as np
import time
import logging
import threading
from typing import List, Union, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TrajectoryPlanner:
    """
    A class for planning and executing smooth trajectories for the Arctos robot.
    
    This class provides functionality to plan and execute smooth joint space trajectories
    with configurable speed and acceleration profiles, while respecting joint limits.
    """
    
    # Class constants
    MIN_STEPS_LINEAR = 10  # Minimum steps for any linear Cartesian move
    STEP_DISTANCE_RESOLUTION_M = 0.01  # 1 step per cm of movement
    JOINT_JUMP_THRESHOLD_RAD = np.deg2rad(45)  # Max allowed joint jump (45 degrees)
    MIN_TIME_STEP = 0.04  # 25Hz update rate for smooth motion
    MAX_JOINT_SPEED = 3000  # Maximum allowed joint speed
    MAX_JOINT_ACCELERATION = 255  # Maximum allowed joint acceleration
    TARGET_ANGULAR_RESOLUTION_RAD = np.deg2rad(1.0)  # Desired ~1.0 deg change per step
    MIN_TRAJ_STEPS = 10  # Min steps for any trajectory
    MAX_TRAJ_STEPS = 75  # Max steps to cap trajectory duration
    
    def __init__(self, robot: Any, controller: Any) -> None:
        """
        Initialize the TrajectoryPlanner.
        
        Args:
            robot: An instance of ArctosPinocchioRobot for kinematics calculations
            controller: An instance of ArctosController for sending commands to the robot
        """
        self.robot = robot
        self.controller = controller
        
    def _validate_joint_angles(self, current_angles: np.ndarray, target_angles: np.ndarray) -> bool:
        """Validate joint angles before planning trajectory."""
        if len(target_angles) != len(current_angles):
            logger.error(
                f"Mismatch in length between current ({len(current_angles)}) "
                f"and target ({len(target_angles)}) joint angles."
            )
            return False
            
        if not self.robot.check_joint_limits(target_angles):
            logger.error(f"Target joint configuration {np.rad2deg(target_angles)} violates joint limits.")
            return False
            
        return True
    
    def _calculate_speed_factors(self, joint_deltas: np.ndarray) -> np.ndarray:
        """Calculate speed factors based on joint deltas for smooth motion."""
        max_delta = np.max(joint_deltas) if np.max(joint_deltas) > 1e-6 else 1.0
        normalized_deltas = joint_deltas / max_delta
        return np.maximum(np.power(normalized_deltas, 0.8), 0.5)  # power=0.8, min_speed=0.5
    
    def _calculate_speeds(self, 
                         speed_factors: np.ndarray, 
                         base_speed: Union[int, float, List[float], np.ndarray],
                         speed_boost: float = 1.5) -> List[int]:
        """Calculate individual joint speeds based on base speed and factors."""
        if isinstance(base_speed, (int, float)):
            base_speed_scalar = base_speed * speed_boost
            return [min(self.MAX_JOINT_SPEED, int(base_speed_scalar * factor)) 
                   for factor in speed_factors]
                    
        if isinstance(base_speed, (list, np.ndarray)) and len(base_speed) == len(speed_factors):
            return [min(self.MAX_JOINT_SPEED, int(float(s) * speed_boost * speed_factors[i])) 
                   for i, s in enumerate(base_speed)]
                   
        logger.warning("Invalid joint_speed format. Using default scaled base speed for all joints.")
        return [min(self.MAX_JOINT_SPEED, int(500 * speed_boost * factor)) 
               for factor in speed_factors]
    
    def _calculate_accelerations(self, 
                               speed_factors: np.ndarray, 
                               base_accel: Union[int, float, List[float], np.ndarray],
                               accel_boost: float = 1.3) -> List[int]:
        """Calculate individual joint accelerations based on base acceleration and factors."""
        if isinstance(base_accel, (int, float)):
            base_accel_scalar = min(self.MAX_JOINT_ACCELERATION, int(base_accel * accel_boost))
            return [min(self.MAX_JOINT_ACCELERATION, int(base_accel_scalar * factor)) 
                   for factor in speed_factors]
                    
        if isinstance(base_accel, (list, np.ndarray)) and len(base_accel) == len(speed_factors):
            return [min(self.MAX_JOINT_ACCELERATION, int(float(a) * accel_boost * speed_factors[i])) 
                   for i, a in enumerate(base_accel)]
                   
        logger.warning("Invalid joint_acceleration format. Using default scaled base acceleration.")
        return [min(self.MAX_JOINT_ACCELERATION, int(150 * accel_boost * factor)) 
               for factor in speed_factors]
    
    def _generate_smooth_trajectory(self, 
                                  start_angles: np.ndarray, 
                                  target_angles: np.ndarray) -> List[np.ndarray]:
        """Generate smooth trajectory using cosine interpolation with adaptive step count."""
        max_joint_delta = np.max(np.abs(target_angles - start_angles))
        
        if max_joint_delta < 1e-6: # Very small or no movement
            return [start_angles.copy(), target_angles.copy()]

        num_interpolated_steps = int(np.ceil(max_joint_delta / self.TARGET_ANGULAR_RESOLUTION_RAD))
        
        # Clamp steps between min and max
        actual_steps = max(self.MIN_TRAJ_STEPS, min(num_interpolated_steps, self.MAX_TRAJ_STEPS))
        
        # Ensure at least 2 steps for interpolation if actual_steps was calculated to be less
        # This typically applies if MIN_TRAJ_STEPS is very low or max_joint_delta is tiny.
        actual_steps = max(actual_steps, 2)

        trajectory = []
        for i in range(actual_steps):
            t_raw = i / (actual_steps - 1) # t_raw goes from 0 to 1
            # Apply cosine interpolation for smooth start and stop (ease-in, ease-out)
            t = 0.5 - 0.5 * np.cos(t_raw * np.pi)
            interpolated_joints = start_angles * (1 - t) + target_angles * t
            trajectory.append(interpolated_joints)
            
        return trajectory
    
    def _execute_joint_movement(self, 
                              joint_configs: List[np.ndarray],
                              speeds: List[int],
                              accelerations: List[int],
                              joint_deltas: np.ndarray) -> bool:
        """Execute the planned joint movement through the controller."""
        servos = self.controller.servos
        
        for i, joint_config in enumerate(joint_configs):
            # Log progress periodically
            if i % 10 == 0: 
                logger.debug(f"Moving to waypoint {i+1}/{len(joint_configs)}: "
                           f"{np.rad2deg(joint_config)}")
            
            # Check joint limits at each waypoint before commanding
            if not self.robot.check_joint_limits(joint_config):
                logger.error(f"Joint limits violated at trajectory point {i} for "
                           f"config {np.rad2deg(joint_config)}. Aborting.")
                return False
            
            # Convert joint angles to encoder values
            angles_rad = joint_config.tolist()[:6]
            encoder_values = [
                self.controller.angle_to_encoder(angle, j_idx) 
                for j_idx, angle in enumerate(angles_rad)
            ]
            
            # Move each joint in a separate thread
            self._move_joints_concurrently(
                encoder_values, 
                speeds, 
                accelerations, 
                joint_deltas, 
                servos
            )
            
            # Add small delay between waypoints (except the last one)
            if i < len(joint_configs) - 1:
                time.sleep(self.MIN_TIME_STEP)
        
        return True
    
    def _move_joints_concurrently(self, 
                                encoder_values: List[float],
                                speeds: List[int],
                                accelerations: List[int],
                                joint_deltas: np.ndarray,
                                servos: list) -> None:
        """Start commands to move all joints concurrently using threads. Does not wait for completion."""
        threads = []
        for j_idx, (enc_val, spd, acc) in enumerate(zip(encoder_values, speeds, accelerations)):
            # Only move joints that need significant movement and have valid servo
            if j_idx < len(servos) and joint_deltas[j_idx] > 1e-4:
                thread = threading.Thread(
                    target=servos[j_idx].run_motor_absolute_motion_by_axis,
                    args=(spd, acc, enc_val)
                )
                threads.append(thread)
                thread.start()
                
        # Wait for all threads to complete
        # Threads are intentionally not joined here.
        # The time.sleep in _execute_joint_movement provides pacing.
        # wait_for_motors_to_stop() at the end of the main public method
        # ensures overall motion completion.
    
    def move_linear_joints_smooth(self, 
                                target_joint_angles: np.ndarray, 
                                num_steps: int = 20, 
                                joint_speed: Union[int, List[int], np.ndarray] = 500, 
                                joint_acceleration: Union[int, List[int], np.ndarray] = 150) -> bool:
        """
        Move the robot in a linear joint space path with smooth motion.
        
        This method plans and executes a smooth trajectory in joint space from the current
        joint configuration to the target configuration, respecting speed and acceleration
        limits while ensuring smooth motion.
        
        Args:
            target_joint_angles: Target joint angles in radians (typically for first 6 joints).
            num_steps: Number of intermediate steps for interpolation. More steps result
                     in smoother but slower motion.
            joint_speed: Base speed for joint movements (controller-specific units, 0-3000).
                       Can be a scalar or a list for individual joint speeds.
            joint_acceleration: Base acceleration for joint movements (0-255).
                              Can be a scalar or a list for individual joint accelerations.
            
        Returns:
            bool: True if movement was successful, False otherwise.
        """
        try:
            current_joint_angles = self.robot.q_encoder[:6]  # Assuming first 6 are controllable
            
            # Validate inputs
            if not self._validate_joint_angles(current_joint_angles, target_joint_angles):
                return False
                
            logger.info(f"Starting smooth linear joint movement from {np.rad2deg(current_joint_angles)} "
                      f"to {np.rad2deg(target_joint_angles)}")
            
            # Calculate joint deltas and speed factors
            joint_deltas = np.abs(target_joint_angles - current_joint_angles)
            speed_factors = self._calculate_speed_factors(joint_deltas)
            
            # Calculate individual joint speeds and accelerations
            speeds = self._calculate_speeds(speed_factors, joint_speed, speed_boost=1.5)
            accelerations = self._calculate_accelerations(speed_factors, joint_acceleration, accel_boost=1.3)
            
            # Generate smooth trajectory (num_steps is no longer used here)
            joint_configs = self._generate_smooth_trajectory(
                current_joint_angles, 
                target_joint_angles
            )
            
            # Execute the movement
            success = self._execute_joint_movement(
                joint_configs,
                speeds,
                accelerations,
                joint_deltas
            )
            
            # Wait for all motors to stop
            self.controller.wait_for_motors_to_stop()
            
            if success:
                logger.info("Smooth linear joint movement completed successfully.")
            else:
                logger.warning("Smooth linear joint movement completed with issues.")
                
            return success
            
        except Exception as e:
            logger.error(f"Error during smooth linear joint movement: {e}", exc_info=True)
            return False
