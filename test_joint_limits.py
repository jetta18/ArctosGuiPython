from ArctosController import ArctosController
from mks_servo_can.mks_enums import Enable, Direction, EndStopLevel
import homing

Arctos = ArctosController()

homing.move_to_zero_pose(Arctos)
#Arctos.servos[0].run_motor_in_speed_mode(direction=Direction.CCW, speed=50, acceleration=20)

Arctos.get_joint_angles()