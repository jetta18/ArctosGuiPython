#!/bin/bash

# ROS-Umgebung laden
source /opt/ros/melodic/setup.bash
source /home/michael/ROS/devel/setup.bash

# Open new tab and launch the ROS demo
gnome-terminal --tab -- bash -c "source /opt/ros/melodic/setup.bash && source /home/michael/ROS/devel/setup.bash && roslaunch arctos_config demo.launch; exec bash"

# Open new tab and run the Moveo MoveIt interface
gnome-terminal --tab -- bash -c "source /opt/ros/melodic/setup.bash && source /home/michael/ROS/devel/setup.bash && rosrun moveo_moveit interface.py; exec bash"

# Open new tab and run the Moveo MoveIt transform
gnome-terminal --tab -- bash -c "source /opt/ros/melodic/setup.bash && source /home/michael/ROS/devel/setup.bash && rosrun moveo_moveit transform.py; exec bash"

# Open new tab and run the UI script
gnome-terminal --tab -- bash -c "source /opt/ros/melodic/setup.bash && source /home/michael/ROS/devel/setup.bash && python3 ui.py; exec bash"

