import os
import time
import pinocchio as pin
import numpy as np
import threading
import meshcat
import meshcat.servers
import logging
from pinocchio.visualize import MeshcatVisualizer
from pink.tasks import FrameTask
from pink import solve_ik, Configuration
from scipy.spatial.transform import Rotation as R
import qpsolvers

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
        """Initializes the robot model, loads the URDF, sets up the Meshcat viewer, and initializes robot state.

        Args:
            ee_frame_name (str, optional): The name of the end-effector frame in the URDF model. Defaults to "gripper".

        Raises:
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

                # Load collision model (for future collision detection)
        self.collision_model = pin.buildGeomFromUrdf(
            self.model, urdf_path, pin.GeometryType.COLLISION, None, [os.path.dirname(urdf_path)]
        )
        self.collision_data = self.collision_model.createData()

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
        """Initializes the Meshcat viewer and stores the actual used URL.

        Args:
            model_name (str, optional): The name under which the robot is stored in Meshcat. Defaults to "arctos_robot".

        Returns:
            MeshcatVisualizer: An instance of MeshcatVisualizer.

        Raises:

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

    def check_joint_limits(self, q: np.ndarray) -> bool:
        """Checks if the first 6 joint values are within the specified limits.

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
        """Displays the robot in Meshcat using the given joint configuration.
        If no configuration is given, it uses the current state `self.q`.

        Args:
            q (np.ndarray, optional): A numpy array representing the joint configuration. If None, uses the current state `self.q`. Defaults to None.

        Raises:
            ValueError: If joint limits are exceeded.
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
        """Displays the robot in Meshcat using the given joint configuration.
        If no configuration is given, it uses the current state `self.q`.

        Args:
            q (np.ndarray, optional): A numpy array representing the joint configuration. If None, uses the current state `self.q`. Defaults to None.

        Raises:
            ValueError: If joint limits are exceeded.

        """
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
        """Animates the robot's movement from its current configuration to a target configuration over a given duration.

        Args:
            q_target (np.ndarray): The target joint configuration.
            duration (float, optional): The duration of the animation in seconds. Defaults to 2.0.
            steps (int, optional): The number of steps in the animation. Defaults to 50.
        """
        #copy the current joint angles
        q_start = self.q.copy()
        #loop over the steps
        for t in range(steps + 1):
            alpha = t / steps
            q_interp = (1 - alpha) * q_start + alpha * q_target
            self.display(q_interp)
            time.sleep(duration / steps)
    
    def set_joint_angles_animated(self, q_target, duration=1.0, steps=50):
        """Sets the joint angles to a target configuration with animation.

        Args:
            q_target (np.ndarray): The target joint configuration.
            duration (float, optional): The duration of the animation in seconds. Defaults to 1.0.
            steps (int, optional): The number of steps in the animation. Defaults to 50.
        """
        #start the animation in a new thread
        threading.Thread(target=self.animate_display, args=(q_target, duration, steps)).start()
        # Set the angles direct
        self.q = q_target  # Gelenkwinkel direkt setzen, aber animiert in der Anzeige


    def update_end_effector_orientation(self) -> None:
        """
        Computes and updates the current Roll-Pitch-Yaw (RPY) orientation of the end-effector.
        Stores the result in `self.ee_orientation`.

        Raises:

        """
        frame_id = self.model.getFrameId(self.ee_frame_name)  # Frame-ID abrufen
        pin.forwardKinematics(self.model, self.data, self.q)  # Kinematik aktualisieren
        pin.updateFramePlacements(self.model, self.data)  # Frame-Positionen aktualisieren

        current_rotation = self.data.oMf[frame_id].rotation  # 3x3 Rotationsmatrix holen
        self.ee_orientation = pin.rpy.matrixToRpy(current_rotation)  # RPY berechnen & speichern

    def update_end_effector_position(self) -> None:
        """
        Computes and updates the current Cartesian position of the end-effector.

        Raises:


        """
        frame_id = self.model.getFrameId(self.ee_frame_name)
        pin.forwardKinematics(self.model, self.data, self.q)
        pin.updateFramePlacements(self.model, self.data)
        self.ee_position = self.data.oMf[frame_id].translation


    def get_end_effector_orientation(self) -> np.ndarray:
        """
        Returns the last computed Roll-Pitch-Yaw (RPY) orientation of the end-effector.


        Raises:

        :return: A numpy array [roll, pitch, yaw] representing the end-effector orientation in radians.
        """
        return self.ee_orientation.copy()  # Gibt gespeicherte Orientierung zurück

    def get_end_effector_position(self) -> np.ndarray:
        """
        Returns the current Cartesian position of the end-effector.


        Raises:

        :return: A numpy array [x, y, z] representing the end-effector position.
        """
        return self.ee_position.copy()

    def get_current_joint_angles(self) -> np.ndarray:
        """
        Returns the current joint angles.


        Raises:

        :return: A numpy array containing the current joint angles.
        """
        return self.q[:6].copy()

    def inverse_kinematics_pink(self, target_xyz: np.ndarray, target_rpy: np.ndarray = None) -> np.ndarray:
        """Computes the inverse kinematics for a target position or pose using the PINK library.

        Args:
            target_xyz (np.ndarray): The target Cartesian position [x, y, z].
            target_rpy (np.ndarray, optional): The target Roll-Pitch-Yaw orientation [roll, pitch, yaw]. If None, only position IK is performed. Defaults to None.

        Returns:
            np.ndarray: The joint configuration (joint angles) that achieve the target position or pose.

        Raises:
            ValueError: If the IK solution violates joint limits.
        """

        # Zielrotation berechnen
        if target_rpy is not None:
            target_rot = R.from_euler('xyz', target_rpy).as_matrix()
        else:
            frame_id = self.model.getFrameId(self.ee_frame_name)
            pin.forwardKinematics(self.model, self.data, self.q)
            pin.updateFramePlacements(self.model, self.data)
            target_rot = self.data.oMf[frame_id].rotation

        target_SE3 = pin.SE3(target_rot, target_xyz)

        # Konfiguration
        configuration = Configuration(self.model, self.data, self.q.copy())

        # IK-Task definieren (ohne target im Konstruktor!)
        task = FrameTask(
            frame=self.ee_frame_name,
            position_cost=2.0,
            orientation_cost=0.5 if target_rpy is not None else 0.0,
            lm_damping=1e-3
        )
        task.set_target(target_SE3)

        # Solver
        solver = "quadprog" if "quadprog" in qpsolvers.available_solvers else qpsolvers.available_solvers[0]

        # solve_ik
        dt = 0.05
        for _ in range(300):  # 3 Iterationen für mehr Genauigkeit
            velocity = solve_ik(configuration, tasks=[task], dt=dt, solver=solver)
            configuration.integrate_inplace(velocity, dt)

        q_solution = configuration.q.copy()

        if not self.check_joint_limits(q_solution):
            raise ValueError("❌ IK-Lösung mit PINK verletzt Gelenkgrenzen!")

        return q_solution

