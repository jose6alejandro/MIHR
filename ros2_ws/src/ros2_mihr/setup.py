from setuptools import setup
import os
import sys
from glob import glob

package_name = 'ros2_mihr'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jose6alejandro',
    maintainer_email='joseacastrorosales@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'supervisor = ros2_mihr.supervisor:main', 
            'perception_img = ros2_mihr.perception_img:main',
            'perception = ros2_mihr.perception:main',
            'recognition = ros2_mihr.recognition:main',
            'recognition_img = ros2_mihr.recognition_img:main',
            'normative = ros2_mihr.normative:main', 
            'verbal = ros2_mihr.verbal:main',
            'automatic = ros2_mihr.automatic:main',
            'deliberative = ros2_mihr.deliberative:main',   
            'adaptative = ros2_mihr.adaptative:main',  
            'action = ros2_mihr.action:main',  
            'action_mov = ros2_mihr.action_mov:main', 
            'affective = ros2_mihr.affective:main',
            'no_verbal = ros2_mihr.no_verbal:main',   
            'paraverbal = ros2_mihr.paraverbal:main',                        
            'record = ros2_mihr.record:main', 
            'spur = ros2_mihr.spur:main',           
        ],
    },
)
