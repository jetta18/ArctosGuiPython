import os
import time
import pinocchio as pin
import numpy as np
import threading
import logging
from pink.tasks import FrameTask
from pink.limits.configuration_limit import ConfigurationLimit
from pink.limits.velocity_limit import VelocityLimit
from pink import solve_ik, Configuration
from scipy.spatial.transform import Rotation as R
import qpsolvers
from robomeshcat import Scene, Robot



logger = logging.getLogger(__name__) # Setup Logger
logger.setLevel(logging.INFO)


class ArctosPinocchioRobot:
    """ArctosPinocchioRobot Class:

    This class is a wrapper around the Pinocchio library, providing an interface for working with robotic models,
    specifically designed for the Arctos robot. It leverages Pinocchio's kinematic and dynamic functionalities to
    simulate and control the robot's movements, compute inverse kinematics, and manage the robot's state.

    The class also integrates with RoboMeshCat for visualization and provides methods for checking joint limits,
    updating the end-effector's position and orientation, and retrieving current joint angles.
    

    A class to manage a robotic model using Pinocchio.
    
    Features:
    - Stores the current joint angles (`self.q`).
    - Stores the Cartesian position of the end-effector (`self.ee_position`).
    - Computes inverse kinematics (IK) while ensuring joint limits are met.
    - Provides motion visualization (digital twin).
    - Allows control of individual joints with limit enforcement.
    - Exports joint angles for external motor control.
    """

    def __init__(self, ee_frame_name="gripper"):
        """Initializes the ArctosPinocchioRobot instance.

        This constructor initializes the robot model by loading the URDF file, setting up the geometric and
        collision models, configuring joint limits, and initializing the RoboMeshCat visualizer. It also sets
        up the initial robot state, including joint angles, end-effector position, and orientation.

        The constructor performs the following main operations:
        1. Loads the robot's URDF model using Pinocchio.
        2. Creates the geometric (visual) and collision models for the robot.
        3. Initializes the joint limits based on the URDF.
        4. Sets up the RoboMeshCat scene for robot visualization.
        5. Initializes the robot's state, including setting joint angles to zero, calculating the initial
           end-effector position and orientation, and displaying the initial state in MeshCat.

        Args:
            ee_frame_name (str, optional): Name of the end-effector frame in the URDF model. Defaults to "gripper".

        Raises:
            FileNotFoundError: If the URDF file is not found.
        """


        repo_path = os.path.dirname(os.path.abspath(__file__))
        urdf_path = os.path.join(repo_path, '..', 'models', 'urdf', 'arctos_urdf.urdf')
        self.urdf_path = urdf_path
        self.ee_frame_name = ee_frame_name

        # Load kinematic model
        self.model = pin.buildModelFromUrdf(urdf_path)
        self.data = self.model.createData()

        # Load geometric model (Visual)
        self.geom_model = pin.buildGeomFromUrdf(
            self.model, urdf_path, pin.GeometryType.VISUAL, None, [os.path.dirname(urdf_path)]
        )
        self.geom_data = self.geom_model.createData()

        # Load collision model (optional)
        self.collision_model = pin.buildGeomFromUrdf(
            self.model, urdf_path, pin.GeometryType.COLLISION, None, [os.path.dirname(urdf_path)]
        )
        self.collision_data = self.collision_model.createData()

        # Joint limits
        self.lower_limits = self.model.lowerPositionLimit
        self.upper_limits = self.model.upperPositionLimit

        # RoboMeshCat setup
        self.scene = Scene(open=False, wait_for_open=False)
        self.robot = Robot(
            pinocchio_model=self.model,
            pinocchio_data=self.data,
            pinocchio_geometry_model=self.geom_model,
            pinocchio_geometry_data=self.geom_data,
            name="arctos"
        )
        self.scene.add_robot(self.robot)
        self.meshcat_url = self.scene.vis.url().replace("tcp://", "http://")

        # Robot state
        self.q = np.zeros(self.model.nq)
        self.q_encoder = np.zeros(self.model.nq)
        self.ee_position = np.zeros(3)
        self.ee_orientation = np.zeros(3)
        self.update_end_effector_position()
        self.update_end_effector_orientation()
        self.display()


    def check_joint_limits(self, q: np.ndarray) -> bool:
        """Checks if the given joint configuration is within the specified limits.

        This method checks if the first 6 joint values in the provided joint configuration `q` are within
        the lower and upper position limits defined for the robot. It logs a warning for each joint that
        violates its limits, specifying whether it is below or above the respective limit.

        Note:
        - The method considers only the first 6 joint values for the limit check.
        - It logs detailed information about each joint limit violation, including the joint number and the
          extent to which the limit is violated.


        Args:
            q (np.ndarray): A numpy array representing the joint configuration.

        Returns:
            bool: True if all first 6 joint values are within limits, False otherwise.

        Raises:
        """
        q_limited = q[:6]  # Consider only first 6 joints
        below_limits = q_limited < self.lower_limits[:6]
        above_limits = q_limited > self.upper_limits[:6]

        if any(below_limits) or any(above_limits):
            logger.warning("⚠️ Joint Limit Violations Detected:")
            for i in range(6):
                if below_limits[i]:
                    logger.warning(f"Joint {i+1} BELOW limit: {q_limited[i]:.2f} rad < {self.lower_limits[i]:.2f} rad")
                if above_limits[i]:
                    logger.warning(f"Joint {i+1} ABOVE limit: {q_limited[i]:.2f} rad > {self.upper_limits[i]:.2f} rad")
            return False

        return True

    def instant_display_state(self, q: np.ndarray = None) -> None:
        """
        Updates and displays the robot's state in RoboMeshCat based on the provided or current joint configuration.
        
        Args:
            q (np.ndarray, optional): Joint configuration to display. If None, uses the current state `self.q`.
        
        Raises:
            TypeError: If the provided joint configuration is not a NumPy array.
            ValueError: If joint limits are exceeded.
        """
        if q is None:
            q = self.q

        if not isinstance(q, np.ndarray):
            raise TypeError("❌ Joint configuration must be a NumPy array.")

        if not self.check_joint_limits(q):
            raise ValueError("❌ Cannot display! Joint limits exceeded.")

        self.robot[:] = q
        self.scene.render()

        self.q = q  # Update internal state
        self.update_end_effector_position()
        self.update_end_effector_orientation()
        logger.debug("✅ Robot state updated and displayed.")


    def display(self, q: np.ndarray = None):
        """Displays the robot in the RoboMeshCat scene with a given joint configuration.

        This method updates the robot's joint positions in the RoboMeshCat visualization to match the
        provided joint configuration `q`. If no configuration is provided, it uses the current state `self.q`.

        Args:
            q (np.ndarray, optional): The joint configuration to display. If None, uses the current state `self.q`. Defaults to None.

        Raises:
            ValueError: If the provided joint configuration exceeds the joint limits.
        """
        if q is None:
            q = self.q
        if not self.check_joint_limits(q):
            raise ValueError("❌ Cannot display! Joint limits exceeded.")
        self.q = q
        self.robot[:] = q
        self.scene.render()
        self.update_end_effector_position()
        self.update_end_effector_orientation()
    
    
    
    
    def animate_display(self, q_target: np.ndarray, duration: float = 2.0, steps: int = 50) -> None:
        """
        Animates the robot's motion using RoboMeshCat's built-in animation system.

        Args:
            q_target (np.ndarray): Target joint configuration for the animation.
            duration (float, optional): Duration of the animation in seconds. Defaults to 2.0.
            steps (int, optional): Number of steps in the animation. Defaults to 50.
        """
        q_start = self.q.copy()
        trajectory = [(1 - t / steps) * q_start + (t / steps) * q_target for t in range(steps + 1)]
        
        fps = steps / duration if duration > 0 else 30

        with self.scene.animation(fps=int(fps)):
            for q in trajectory:
                self.robot[:] = q
                self.q = q
                self.scene.render()

        self.update_end_effector_position()
        self.update_end_effector_orientation()

    
    def set_joint_angles_animated(self, q_target, duration=1.5, steps=15):
        """Sets the joint angles to a target configuration with animation.

        This method animates the robot's movement to the target joint configuration over a specified duration.

        Args:
            q_target (np.ndarray): The target joint configuration.
            duration (float, optional): The duration of the animation in seconds. Defaults to 1.0.
            steps (int, optional): The number of steps in the animation. Defaults to 50.
        """

        #start the animation in a new thread
        self.animate_display(q_target, duration, steps)
        # Set the angles direct
        self.q = q_target  # Set joint angles directly, but animate in display


    def update_end_effector_orientation(self) -> None:
        """Updates the end-effector's Roll-Pitch-Yaw (RPY) orientation.

        This method computes the current Roll-Pitch-Yaw (RPY) orientation of the end-effector frame
        based on the robot's current joint configuration. It updates the internal `self.ee_orientation`
        attribute with the calculated RPY values.

        Raises:
        """
        frame_id = self.model.getFrameId(self.ee_frame_name)  # Frame-ID abrufen
        pin.forwardKinematics(self.model, self.data, self.q)  # Kinematik aktualisieren
        pin.updateFramePlacements(self.model, self.data)  # Frame-Positionen aktualisieren

        current_rotation = self.data.oMf[frame_id].rotation  # 3x3 Rotationsmatrix holen
        self.ee_orientation = pin.rpy.matrixToRpy(current_rotation)  # RPY berechnen & speichern

    def update_end_effector_position(self) -> None:
        """Updates the Cartesian position of the end-effector.

        This method calculates the current Cartesian position (x, y, z) of the end-effector frame
        based on the robot's current joint configuration and updates the `self.ee_position` attribute.

        Raises:
        """
        frame_id = self.model.getFrameId(self.ee_frame_name)
        pin.forwardKinematics(self.model, self.data, self.q)
        pin.updateFramePlacements(self.model, self.data)
        self.ee_position = self.data.oMf[frame_id].translation


    def get_end_effector_orientation(self) -> np.ndarray:
        """Retrieves the end-effector's current Roll-Pitch-Yaw (RPY) orientation.

        This method returns the last computed Roll-Pitch-Yaw (RPY) orientation of the end-effector,
        which is stored in the `self.ee_orientation` attribute.

        Returns:
            np.ndarray: A numpy array [roll, pitch, yaw] representing the end-effector orientation in radians.
        """
        return self.ee_orientation.copy()  # Returns stored orientation

    def get_end_effector_position(self) -> np.ndarray:
        """Retrieves the end-effector's current Cartesian position.

        This method returns the last computed Cartesian position (x, y, z) of the end-effector,
        stored in the `self.ee_position` attribute.

        Returns:
            np.ndarray: A numpy array [x, y, z] representing the end-effector position.
        """
        return self.ee_position.copy()

    def get_current_joint_angles(self) -> np.ndarray:
        """Retrieves the current joint angles of the robot.

        This method returns a copy of the current joint angles for the first 6 joints of the robot,
        which are stored in the `self.q` attribute.

        Returns:
            np.ndarray: A numpy array containing the current joint angles.
        """
        return self.q[:6].copy()

    def inverse_kinematics_pink(self, target_xyz: np.ndarray, target_rpy: np.ndarray = None) -> np.ndarray:
        """
        Computes the inverse kinematics for a target position or pose using the PINK library.

        This method calculates the joint configuration required for the robot to reach a specified target
        position or pose. It utilizes the PINK (Pinocchio Inverse Kinematics) library to solve the inverse
        kinematics problem. The method supports solving for position only or for both position and orientation,
        depending on whether `target_rpy` is provided.

        Args:
            target_xyz (np.ndarray): The target Cartesian position [x, y, z].
            target_rpy (np.ndarray, optional): The target Roll-Pitch-Yaw orientation [roll, pitch, yaw].
                                            If None, only position IK is performed.

        Returns:
            np.ndarray: The joint configuration (joint angles) that achieves the target position or pose.

        Raises:
            ValueError: If the IK solution violates joint limits.
            RuntimeError: If the IK solver fails to converge.
        """
        # Compute target rotation
        if target_rpy is not None:
            target_rot = R.from_euler('xyz', target_rpy).as_matrix()
        else:
            frame_id = self.model.getFrameId(self.ee_frame_name)
            pin.forwardKinematics(self.model, self.data, self.q)
            pin.updateFramePlacements(self.model, self.data)
            target_rot = self.data.oMf[frame_id].rotation

        target_SE3 = pin.SE3(target_rot, target_xyz)

        # Initial robot configuration
        configuration = Configuration(self.model, self.data, self.q.copy())

        # Task setup
        task = FrameTask(
            frame=self.ee_frame_name,
            position_cost=2.0,
            orientation_cost=0.5 if target_rpy is not None else 0.0,
            lm_damping=1e-3
        )
        task.set_target(target_SE3)

        # Preferred solver
        preferred_solvers = ["proxqp", "osqp", "quadprog"]
        solver = next((s for s in preferred_solvers if s in qpsolvers.available_solvers), None)
        if solver is None:
            raise RuntimeError("No suitable QP solver available.")

        # Define limits (position and velocity limits)
        limits = [
            ConfigurationLimit(self.model),
            VelocityLimit(self.model)
        ]

        # IK parameters
        dt = 0.05
        tol = 1e-4
        max_iter = 150

        # Iterative solve
        for i in range(max_iter):
            velocity = solve_ik(
                configuration,
                tasks=[task],
                dt=dt,
                solver=solver,
                limits=limits
            )
            configuration.integrate_inplace(velocity, dt)
            error_norm = np.linalg.norm(task.compute_error(configuration))
            if error_norm < tol:
                break
        else:
            raise RuntimeError(f"IK did not converge within {max_iter} iterations (final error: {error_norm:.3g})")

        q_solution = configuration.q.copy()

        if not self.check_joint_limits(q_solution):
            raise ValueError("❌ IK solution violates joint limits!")

        return q_solution

