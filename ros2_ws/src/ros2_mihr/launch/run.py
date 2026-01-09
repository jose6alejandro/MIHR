from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
import os
def generate_launch_description():

    initial_nodes = [
        Node(
            package='ros2_mihr',
            executable='record',
            name='Record',
        ),
        Node(
            package='ros2_mihr',
            executable='deliberative',
            name='Deliberative',
        ),     
        Node(
            package='ros2_mihr',
            executable='paraverbal',
            name='Paraverbal',
        )       
    ]

    delayed_group_actions = []

    display_menu()
    choice = input("Seleccione una opción: ")

    if choice == '1':
        save_ablation_settings('config1')
        initial_nodes = [            
            Node(
                package='ros2_mihr',
                executable='adaptative',
                name='Adaptative',
            ),            
            Node(
                package='ros2_mihr',
                executable='no_verbal',
                name='No_verbal',
            )] + initial_nodes
        
        delayed_group_actions = delayed_group_actions + [
            Node(
                package='ros2_mihr',
                executable='affective',
                name='Affective',
            ),
            Node(
                package='ros2_mihr',
                executable='automatic',
                name='Automatic',
            ),            
            Node(
                package='ros2_mihr',
                executable='normative',
                name='Normative',
            )            
        ]

    elif choice == '2':
        save_ablation_settings('config2')
        delayed_group_actions = delayed_group_actions + [
            Node(
                package='ros2_mihr',
                executable='affective',
                name='Affective',
            ),
            Node(
                package='ros2_mihr',
                executable='no_verbal',
                name='No_verbal',
            ), 
            Node(
                package='ros2_mihr',
                executable='automatic',
                name='Automatic',
            ),              
            Node(
                package='ros2_mihr',
                executable='normative',
                name='Normative',
            )            
        ]

    elif choice == '3':
        save_ablation_settings('config3')
        initial_nodes = [            
            Node(
                package='ros2_mihr',
                executable='adaptative',
                name='Adaptative',
            ),            
            Node(
                package='ros2_mihr',
                executable='no_verbal',
                name='No_verbal',
            )] + initial_nodes
        delayed_group_actions = delayed_group_actions + [
            Node(
                package='ros2_mihr',
                executable='affective',
                name='Affective',
            ),
            Node(
                package='ros2_mihr',
                executable='automatic',
                name='Automatic',
            )                 
        ]
    elif choice == '4':
        save_ablation_settings('config4')
        initial_nodes = [            
            Node(
                package='ros2_mihr',
                executable='adaptative',
                name='Adaptative',
            )] + initial_nodes
        delayed_group_actions = delayed_group_actions + [
            Node(
                package='ros2_mihr',
                executable='normative',
                name='Normative',
            )     
        ]
    else:
        initial_nodes = [            
            Node(
                package='ros2_mihr',
                executable='recognition',
                #name='Recognition',
            ),  
            Node(
                package='ros2_mihr',
                executable='perception',
                #name='Perception',
            ),
            Node(
                package='ros2_mihr',
                executable='action',
                #name='Action', 
            )            

        ]
        delayed_group_actions = [] 
  
    os.system('clear')
            

    delayed_group = TimerAction( period=40.0, actions=delayed_group_actions)
    launch_actions = initial_nodes + [delayed_group]

    return LaunchDescription(launch_actions)

def display_menu():
    os.system('clear')
    print("\n==============================")
    print("      Modo de configuración      ")
    print("==============================")
    print("1) Configuración base (con todos los nodos)")
    print("2) Ablación Config  (sin Adaptativo)")
    print("3) Ablación Config  (sin Normativo)")
    print("4) Ablación Config  (sin Afectivo)")
    print("*) Raspberry Config (con nodos esenciales)")
    print("==============================")


def save_ablation_settings(text):

    try:
      with open('../config.txt', 'w') as archivo:    
        archivo.write(f"{text}")

    except IOError:
        print("Ocurrió un error al intentar escribir el archivo.")




