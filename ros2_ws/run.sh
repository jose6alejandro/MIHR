#!/bin/bash

ROS_PATH="src/ros2_mihr/ros2_mihr"
PROJECT_PATH=$(pwd)

if [ "$1" == "1" ]; then
    colcon build --symlink-install
    source install/setup.bash
    sudo chmod -R 777 /dev  
elif [ "$1" == "2" ]; then
    source install/setup.bash  
elif [ "$1" == "3" ]; then
#    echo "source ~/$pwd/install/setup.bash" >> ~/.bashrc
    source ~/.bashrc
elif [ "$1" == "4" ]; then
    rm -rf build install log
elif [ "$1" == "5" ]; then
    sudo chmod -R 777 /dev 
elif [ "$1" ]; then
    cd $ROS_PATH
    ros2 run ros2_mihr $1
    cd ../../../    
else 
    cd $ROS_PATH
    ros2 launch ros2_mihr run.py 
    cd ../../../
fi
