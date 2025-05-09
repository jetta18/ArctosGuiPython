from core.ArctosController import ArctosController
from core.ArctosPinocchio import ArctosPinocchioRobot
from core.speed_controller import CartesianSpeedController
import time
import numpy as np

# Init
arctos = ArctosController()
robot = ArctosPinocchioRobot()


controller = CartesianSpeedController(robot, arctos,
                                      loop_hz=50,
                                      active_axes=[0, 1])
controller.start()
controller.set_target_pose([-0.4, 0, 0.5], [0, 0, 0])

# Beobachtungszeit
print("✳️ Fahre Zielpose an...")
time.sleep(10)  # 10 Sekunden beobachten

# Stopp
controller.stop()
print("🛑 Regler gestoppt")