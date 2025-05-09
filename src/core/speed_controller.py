import time
import threading
import logging
from typing import Sequence, Optional, List

import numpy as np
import pinocchio as pin
from scipy.spatial.transform import Rotation as R

from services.mks_servo_can.mks_enums import Direction
from core.ArctosController import ArctosController  # type: ignore
from core.ArctosPinocchio import ArctosPinocchioRobot  # type: ignore


class CartesianSpeedController:
    """Closed‑loop Cartesian P‑Regler.

    • Unterstützt Teilbetrieb (`active_axes`).
    • Nutzt nur die Spalten des Jacobians der *wirklich aktiven* Achsen.
    • Leitet resultierende `q̇_active` zurück in einen 6‑Dim‑Vektor mit Nullen
      für inaktive Gelenke.
    """

    def __init__(
        self,
        robot: ArctosPinocchioRobot,
        arctos: ArctosController,
        loop_hz: float = 50.0,
        default_acc: int = 20,
        rpm_limit: int = 3000,
        kp_xyz: float = 2.0,
        kp_rpy: float = 2.0,
        active_axes: Optional[List[int]] = None,
    ) -> None:
        self.robot = robot
        self.arctos = arctos
        self.dt = 1.0 / loop_hz
        self.default_acc = int(np.clip(default_acc, 0, 255))
        self.rpm_limit = int(np.clip(rpm_limit, 0, 3000))
        self.kp_xyz = kp_xyz
        self.kp_rpy = kp_rpy
        self.active_axes: List[int] = sorted(active_axes) if active_axes else list(range(6))

        self._target_pose = np.zeros(6)
        self._lock = threading.Lock()
        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self._last_rpm: list[int] = [0] * 6
        self._last_dir: list[Direction] = [Direction.CCW] * 6

    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join()
        self._send_zero_velocity()

    # ------------------------------------------------------------------
    def set_target_pose(self, xyz: Sequence[float], rpy: Sequence[float]) -> None:
        with self._lock:
            self._target_pose[:3] = xyz
            self._target_pose[3:] = rpy

    # ------------------------------------------------------------------
    def _read_active_joint_angles(self) -> np.ndarray:
        q = np.zeros(6)
        for i in self.active_axes:
            enc = self.arctos._read_encoder_with_fallback(i, self.arctos.servos[i])  # type: ignore
            q[i] = self.arctos.encoder_to_angle(enc, i)  # type: ignore
        return q

    # ------------------------------------------------------------------
    def _loop(self) -> None:
        frame_id = self.robot.model.getFrameId(self.robot.ee_frame_name)
        while not self._stop_evt.is_set():
            t0 = time.perf_counter()

            # Sollpose
            with self._lock:
                x_des = self._target_pose.copy()

            # Ist‑gelenke (nur aktive)
            q_act = self._read_active_joint_angles()
            q_full = np.concatenate([q_act, np.zeros(2)])

            # FK Istpose
            pin.forwardKinematics(self.robot.model, self.robot.data, q_full)
            pin.updateFramePlacements(self.robot.model, self.robot.data)
            placement = self.robot.data.oMf[frame_id]
            p_curr = placement.translation
            rpy_curr = R.from_matrix(placement.rotation).as_euler('xyz')

            # Fehler & gewünschte EE‑Geschwindigkeit
            err_xyz = x_des[:3] - p_curr
            err_rpy = (x_des[3:] - rpy_curr + np.pi) % (2 * np.pi) - np.pi
            v_ee = np.concatenate([self.kp_xyz * err_xyz, self.kp_rpy * err_rpy])

            # Jacobian (voll)
            pin.computeJointJacobians(self.robot.model, self.robot.data, q_full)
            J6_full = pin.getFrameJacobian(
                self.robot.model,
                self.robot.data,
                frame_id,
                pin.ReferenceFrame.WORLD,
            )[:6, :6]

            # Sub‑Jacobian für aktive Achsen
            J6_act = J6_full[:, self.active_axes]  # 6×n_act

            # q̇ für aktive Achsen
            try:
                qdot_act = np.linalg.pinv(J6_act) @ v_ee  # n_act×1
            except np.linalg.LinAlgError:
                self.logger.warning("Jacobian (active) singular – skip")
                self._sleep_rest(t0)
                continue

            # Map zurück in 6‑dim Array
            qdot_full = np.zeros(6)
            for idx, joint_idx in enumerate(self.active_axes):
                qdot_full[joint_idx] = qdot_act[idx]

            # RPM & Senden nur für aktive
            for i, dq in zip(self.active_axes, qdot_act):
                rpm_f = dq / (2.0 * np.pi) * 60.0 * abs(self.arctos.gear_ratios[i])
                rpm_f = np.clip(rpm_f, -self.rpm_limit, self.rpm_limit)
                dir_cmd = Direction.CCW if rpm_f >= 0 else Direction.CW
                rpm_cmd = int(abs(rpm_f))
                if rpm_cmd == self._last_rpm[i] and dir_cmd == self._last_dir[i]:
                    continue
                try:
                    self.arctos.servos[i].run_motor_in_speed_mode(dir_cmd, rpm_cmd, self.default_acc)
                except Exception as exc:
                    self.logger.debug(f"Speed cmd axis {i} failed: {exc}")
                self._last_rpm[i] = rpm_cmd
                self._last_dir[i] = dir_cmd

            self._sleep_rest(t0)

    # ------------------------------------------------------------------
    def _sleep_rest(self, t0: float) -> None:
        dt = self.dt - (time.perf_counter() - t0)
        if dt > 0:
            time.sleep(dt)

    def _send_zero_velocity(self) -> None:
        for i in self.active_axes:
            if self._last_rpm[i] == 0:
                continue
            try:
                self.arctos.servos[i].run_motor_in_speed_mode(Direction.CCW, 0, self.default_acc)
            except Exception:
                pass
            self._last_rpm[i] = 0
