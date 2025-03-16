import os
import time
import pinocchio as pin
import numpy as np
import threading
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

    def __init__(self, urdf_path: str = "/home/michael/GIT/ArctosGuiPython/arctos_urdf.urdf", ee_frame_name="gripper"):
        """
        Initializes the robot, loads the URDF, and sets up the Meshcat viewer.

        :param urdf_path: Path to the URDF file of the robot.
        :param ee_frame_name: The name of the end-effector frame.
        """
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
        self.ee_position = np.zeros(3)  # Stores the Cartesian position of the end-effector

        # Compute initial Cartesian position
        self.update_end_effector_position()

        # Display initial configuration
        self.display()


    def initialize_viewer(self, model_name: str = "arctos_robot") -> MeshcatVisualizer:
        """
        Initializes the Meshcat visualizer and loads the robot model.

        :param model_name: The name under which the robot is stored in Meshcat.
        :return: An instance of MeshcatVisualizer.
        """
        viz = MeshcatVisualizer(self.model, self.geom_model, self.geom_model)
        viz.initViewer()
        viz.loadViewerModel(model_name)
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
        :return: True if the first 6 joint values are within limits, False otherwise.
        """
        q_limited = q[:6]  # Take only first 6 joints for comparison

        if np.any(q_limited < self.lower_limits[:6]) or np.any(q_limited > self.upper_limits[:6]):
            logger.warning(f"⚠️ Error: Joint angles exceed limits! {q_limited}")
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
        Berechnet die inverse Kinematik (IK), um Gelenkwinkel zu finden, die die gewünschte XYZ-Position
        und optional eine gewünschte Orientierung (Roll, Pitch, Yaw) erreichen.

        :param target_xyz: Ein numpy-Array [X, Y, Z] mit der Zielposition.
        :param target_rpy: (Optional) Ein numpy-Array [roll, pitch, yaw] für die gewünschte Orientierung.
        :param max_iters: Maximale Anzahl der Iterationen für die Konvergenz.
        :param tol: Toleranz für das Abbruchkriterium.
        :return: Ein numpy-Array mit der Gelenkkonfiguration, die das Ziel erreicht.
        """
        frame_id = self.model.getFrameId(self.ee_frame_name)
        q = self.q.copy()  # Starte von der aktuellen Gelenkkonfiguration

        for i in range(max_iters):
            pin.forwardKinematics(self.model, self.data, q)
            pin.updateFramePlacements(self.model, self.data)

            # Positionsfehler berechnen
            current_xyz = self.data.oMf[frame_id].translation
            position_error = target_xyz - current_xyz

            # Orientierungsfehler berechnen (falls target_rpy vorhanden ist)
            if target_rpy is not None:
                target_rpy = np.asarray(target_rpy, dtype=np.float64)

                # Aktuelle Orientierung als Rotationsmatrix
                current_rotation = self.data.oMf[frame_id].rotation
                current_rpy = pin.rpy.matrixToRpy(current_rotation)

                # Fehler in RPY-Raum berechnen
                orientation_error_rpy = target_rpy - current_rpy

                # Inverse RPY-Jacobian berechnen
                J_rpy_inv = pin.rpy.computeRpyJacobianInverse(current_rpy, pin.LOCAL_WORLD_ALIGNED)

                # Orientierungskorrektur umwandeln
                orientation_error = J_rpy_inv @ orientation_error_rpy
            else:
                orientation_error = np.zeros(3)  # Keine Orientierungskontrolle

            # Fehler kombinieren
            error = np.concatenate((position_error, orientation_error))

            if np.linalg.norm(error) < tol:
                logger.debug(f"✅ IK konvergierte in {i} Iterationen.")

                if not self.check_joint_limits(q):
                    raise ValueError("❌ IK-Lösung überschreitet Gelenkgrenzen!")

                self.update_end_effector_position()  # ✅ Aktualisiere die kartesische Position
                return q

            # Gesamtes Jacobian für Position & Orientierung berechnen
            J = pin.computeFrameJacobian(self.model, self.data, q, frame_id, pin.LOCAL_WORLD_ALIGNED)

            # IK-Gleichung lösen (Least Squares Methode)
            dq = np.linalg.pinv(J) @ error
            q += dq  # Gelenkwinkel-Update

        logger.warning("⚠️ Warnung: IK hat nicht konvergiert.")
        raise ValueError("❌ IK konnte keine gültige Lösung innerhalb der Gelenkgrenzen finden.")




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

