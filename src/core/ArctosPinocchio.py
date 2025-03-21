import os
import time
import pinocchio as pin
import numpy as np
import threading
import meshcat
import meshcat.servers
import logging
from pinocchio.visualize import MeshcatVisualizer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  


class ArctosPinocchioRobot:
    """
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
        """
        Initializes the robot, loads the URDF, and sets up the Meshcat viewer.

        :param urdf_path: Path to the URDF file of the robot.
        :param ee_frame_name: The name of the end-effector frame.
        """


        repo_path = os.path.dirname(os.path.abspath(__file__))
        urdf_path = os.path.join(repo_path, '..', 'models', 'urdf', 'arctos_urdf.urdf')
        self.urdf_path = urdf_path

        self.ee_frame_name = ee_frame_name  # Name of the end-effector frame

        # Load kinematic model
        self.model = pin.buildModelFromUrdf(urdf_path)
        self.data = self.model.createData()

        # Load geometric model (Visual representation)
        self.geom_model = pin.buildGeomFromUrdf(
            self.model, urdf_path, pin.GeometryType.VISUAL, None, [os.path.dirname(urdf_path)]
        )
        self.geom_data = self.geom_model.createData()

        # Retrieve joint limits from URDF
        self.lower_limits = self.model.lowerPositionLimit
        self.upper_limits = self.model.upperPositionLimit

        # Initialize Meshcat viewer automatically
        self.viz = self.initialize_viewer()

        # Initialize robot state (joint angles and Cartesian position)
        self.q = np.zeros(self.model.nq)  # Stores the current joint angles

        self.q_encoder = np.zeros(self.model.nq)
        self.ee_position = np.zeros(3)  # Stores the Cartesian position of the end-effector
        self.ee_orientation = np.zeros(3)
        # Compute initial Cartesian position
        self.update_end_effector_position()
        self.update_end_effector_orientation()

        # Display initial configuration
        self.display()


    def initialize_viewer(self, model_name: str = "arctos_robot") -> MeshcatVisualizer:
        """
        Initialisiert den Meshcat-Visualizer und speichert die tatsächlich verwendete URL.

        :param model_name: Der Name unter dem der Roboter in Meshcat gespeichert wird.
        :return: Eine Instanz von MeshcatVisualizer.
        """
        # Falls Meshcat noch nicht gestartet wurde, starte den Server
        if not hasattr(self, 'meshcat_server'):
            self.meshcat_server = meshcat.servers.zmqserver.start_zmq_server_as_subprocess()

        # Erstelle den Meshcat Visualizer und erhalte die tatsächliche URL
        viz = MeshcatVisualizer(self.model, self.geom_model, self.geom_model)
        visualizer_instance = meshcat.Visualizer()
        zmq_url = visualizer_instance.url()  # Holt die tatsächliche URL

        viz.initViewer(viewer=visualizer_instance)
        viz.loadViewerModel(model_name)

        # Konvertiere ZeroMQ URL in HTTP URL für die Anzeige in NiceGUI
        self.meshcat_url = zmq_url.replace("tcp://", "http://")

        return viz

    def update_end_effector_position(self) -> None:
        """
        Computes and updates the current Cartesian position of the end-effector.
        """
        frame_id = self.model.getFrameId(self.ee_frame_name)
        pin.forwardKinematics(self.model, self.data, self.q)
        pin.updateFramePlacements(self.model, self.data)
        self.ee_position = self.data.oMf[frame_id].translation

    def get_end_effector_position(self) -> np.ndarray:
        """
        Returns the current Cartesian position of the end-effector.

        :return: A numpy array [x, y, z] representing the end-effector position.
        """
        return self.ee_position.copy()

    def check_joint_limits(self, q: np.ndarray) -> bool:
        """
        Checks if the first 6 joint values are within the specified limits.

        :param q: A numpy array representing the joint configuration.
        :return: True if all first 6 joint values are within limits, False otherwise.
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
        Displays the robot in Meshcat using the given joint configuration.
        If no configuration is given, it uses the current state `self.q`.

        :param q: Optional. A numpy array representing the joint configuration.
        """
        if q is None:
            q = self.q  # Use stored joint state if none provided

        if not self.check_joint_limits(q):
            raise ValueError("❌ Cannot display! Joint limits exceeded.")
        
        if self.viz is not None:
            self.viz.display(q)
            self.q = q  # Store updated joint angles
            self.update_end_effector_position()  # Update Cartesian position
            self.update_end_effector_orientation() 
        else:
            logger.debug("Error: Visualizer not initialized.")

    def display(self, q: np.ndarray = None):
        if q is None:
            q = self.q
        if not self.check_joint_limits(q):
            raise ValueError("❌ Cannot display! Joint limits exceeded.")

        if self.viz is not None:
            self.viz.display(q)
            self.update_end_effector_position()
            self.update_end_effector_orientation() 
        else:
            logger.debug("Error: Visualizer not initialized.")
    
    def animate_display(self, q_target, duration=2.0, steps=50):
        q_start = self.q.copy()
        for t in range(steps + 1):
            alpha = t / steps
            q_interp = (1 - alpha) * q_start + alpha * q_target
            self.display(q_interp)
            time.sleep(duration / steps)
    
    def set_joint_angles_animated(self, q_target, duration=1.0, steps=50):
        threading.Thread(target=self.animate_display, args=(q_target, duration, steps)).start()
        self.q = q_target  # Gelenkwinkel direkt setzen, aber animiert in der Anzeige




    def inverse_kinematics(self, target_xyz: np.ndarray, target_rpy: np.ndarray = None, max_iters: int = 100, tol: float = 1e-4) -> np.ndarray:
        """
        Computes the inverse kinematics (IK) to determine joint angles that achieve a desired XYZ position
        and optionally a desired orientation (Roll, Pitch, Yaw).

        This function iteratively solves the IK problem using a Jacobian-based approach. It stops when the position 
        and orientation error is below a given tolerance or when the maximum number of iterations is reached.

        :param target_xyz: A numpy array [X, Y, Z] representing the desired position in Cartesian space.
        :param target_rpy: (Optional) A numpy array [roll, pitch, yaw] representing the desired orientation.
        :param max_iters: The maximum number of iterations allowed for convergence.
        :param tol: The error tolerance for convergence. The algorithm stops when the combined position and orientation 
                    error is below this threshold.
        :return: A numpy array containing the joint configuration that achieves the target position and orientation.

        :raises ValueError: If the IK solution does not converge within the specified iterations or if the computed
                            joint configuration exceeds joint limits.
        """
        frame_id = self.model.getFrameId(self.ee_frame_name)
        q = self.q.copy()  # Start from the current joint configuration

        for i in range(max_iters):
            # Perform forward kinematics to update the frame positions
            pin.forwardKinematics(self.model, self.data, q)
            pin.updateFramePlacements(self.model, self.data)

            # Compute the position error
            current_xyz = self.data.oMf[frame_id].translation
            position_error = target_xyz - current_xyz

            # Compute the orientation error if target_rpy is provided
            if target_rpy is not None:
                target_rpy = np.asarray(target_rpy, dtype=np.float64)

                # Retrieve the current rotation matrix of the end-effector
                current_rotation = self.data.oMf[frame_id].rotation
                current_rpy = pin.rpy.matrixToRpy(current_rotation)

                # Compute orientation error in RPY space
                orientation_error_rpy = target_rpy - current_rpy

                # Compute inverse RPY Jacobian for proper error transformation
                J_rpy_inv = pin.rpy.computeRpyJacobianInverse(current_rpy, pin.LOCAL_WORLD_ALIGNED)

                # Transform orientation error to a usable form
                orientation_error = J_rpy_inv @ orientation_error_rpy
            else:
                orientation_error = np.zeros(3)  # No orientation control if not specified

            # Combine position and orientation errors
            error = np.concatenate((position_error, orientation_error))

            # Check if the error is within the tolerance
            if np.linalg.norm(error) < tol:
                logger.debug(f"✅ IK converged in {i} iterations.")

                if not self.check_joint_limits(q):
                    raise ValueError("❌ IK solution exceeds joint limits!")

                self.update_end_effector_position()  # ✅ Update Cartesian position
                self.update_end_effector_orientation()
                return q

            # Compute the full Jacobian for position and orientation
            J = pin.computeFrameJacobian(self.model, self.data, q, frame_id, pin.LOCAL_WORLD_ALIGNED)

            # Solve the IK equation using the least squares method (pseudoinverse)
            dq = np.linalg.pinv(J) @ error
            q += dq  # Update joint angles

        logger.warning("⚠️ Warning: IK did not converge.")
        raise ValueError("❌ IK could not find a valid solution within joint limits.")


    def move_joint(self, joint_index: int, angle: float) -> None:
        """
        Moves a single joint to a specified angle while ensuring it stays within limits.

        :param joint_index: Index of the joint in the configuration vector.
        :param angle: Target angle in radians.
        """
        new_q = self.q.copy()
        new_q[joint_index] = angle

        if not self.check_joint_limits(new_q):
            raise ValueError(f"❌ Joint {joint_index} angle {angle} rad exceeds limits!")

        self.q = new_q  # ✅ Update stored joint state
        self.display()

    def get_current_joint_angles(self) -> np.ndarray:
        """
        Returns the current joint angles.

        :return: A numpy array containing the current joint angles.
        """
        return self.q[:6].copy()


    def update_end_effector_orientation(self) -> None:
        """
        Computes and updates the current Roll-Pitch-Yaw (RPY) orientation of the end-effector.
        Stores the result in `self.ee_orientation`.
        """
        frame_id = self.model.getFrameId(self.ee_frame_name)  # Frame-ID abrufen
        pin.forwardKinematics(self.model, self.data, self.q)  # Kinematik aktualisieren
        pin.updateFramePlacements(self.model, self.data)  # Frame-Positionen aktualisieren

        current_rotation = self.data.oMf[frame_id].rotation  # 3x3 Rotationsmatrix holen
        self.ee_orientation = pin.rpy.matrixToRpy(current_rotation)  # RPY berechnen & speichern

    def get_end_effector_orientation(self) -> np.ndarray:
        """
        Returns the last computed Roll-Pitch-Yaw (RPY) orientation of the end-effector.

        :return: A numpy array [roll, pitch, yaw] representing the end-effector orientation in radians.
        """
        return self.ee_orientation.copy()  # Gibt gespeicherte Orientierung zurück
