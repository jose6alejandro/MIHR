import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import os
import time
import textwrap

BOLD = '\33[1m'
END = '\33[0m'


class Supervisor(Node):
    def __init__(self):
        super().__init__('supervisor')
        
        self.subscription = self.create_subscription(
            String,
            'monitoreo',
            self.response_callback,
            15
        )
        
        self.subscription_2 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
            10
        )  

        self.subscription_3 = self.create_subscription(
            String,
            'estado_actual',
            self.current_state_callback,
            10
        ) 
        self.subscription_4 = self.create_subscription(
            String,
            'mensaje',
            self.user_message_callback,
            10
        )     

        self.subscription_5 = self.create_subscription(
            String,
            'respuesta_verbal',
            self.robot_message_callback,
            10
        ) 

        self.subscription_6 = self.create_subscription(
            String,
            'respuesta_robot',
            self.flag_callback,
            10
        ) 

        self.state_name = 'Saludo' 
        self.user_message = ''
        self.robot_message = ''
        self.temp_message = ''
        self.current_shift = 'Robot'
        
        os.system('clear') 
        print('Cargando nodos de la arquitectura MIHR...')
        self.nodes = {
        'Percepción':['',''], 
        'Percepción_Img':['',''], 
        'Reconocimiento':['',''], 
        'Reconocimiento_Img':['',''], 
        'Deliberativo':['',''], 
        'Adaptativo':['',''], 
        'Normativo':['',''], 
        'Automático':['',''],
        'Afectivo':['',''],
        'Verbal':['',''],
        'Paraverbal':['',''],
        'No_verbal':['',''],
        'Actuador':['',''],
        'Actuador_Mov':['',''] 
        } 

    def current_state_callback(self, msg):
        self.state_name = msg.data.split(':')[0]        

    def user_message_callback(self, msg):
        self.user_message = msg.data
        self.current_shift = 'Robot'

    def robot_message_callback(self, msg):
        self.robot_message = msg.data
        
    def flag_callback(self, msg):
        #self.robot_message = self.temp_message
        self.current_shift = 'Estudiante'


    def response_callback(self, msg):
            os.system('clear')
            
            try:
                name_node, current_state, number_of_calls = msg.data.split(':')
                if name_node in self.nodes:
                    self.nodes[name_node] = [current_state, number_of_calls]
                else:
                    return
            except ValueError:
                self.get_logger().error(f"Mensaje de monitoreo mal formado recibido: '{msg.data}'")
                return

            col_nodo_width = 50
            col_estado_width = 40
            col_llamado_width = 10
            total_width = col_nodo_width + col_estado_width + col_llamado_width
            
            title = f"Funcionamiento del MIHR"
            header = (f"{BOLD}{'Nodo':<{col_nodo_width}}"
                    f"{'Estado':<{col_estado_width}}"
                    f"{'Llamadas':>{col_llamado_width}}{END}")
            
            separator = '-' * total_width

            print(separator)
            print(title)            
            print(separator)
            print(header)
            print(separator)
        
            for n_node, info in self.nodes.items():
                state = info[0]
                calls = info[1]
                print(f"{n_node:<{col_nodo_width}}"
                    f"{state:<{col_estado_width}}"
                    f"{calls:>{col_llamado_width}}")
            
            print(separator)
            print(f'{BOLD}Estado actual de la sesión:{END} {self.state_name}')
            print(f'{BOLD}Turno actual:{END} {self.current_shift}')
            print(separator)
            wrapped_robot_message = textwrap.fill(self.robot_message, width=total_width)
            print(f'{BOLD}Último mensaje del robot:{END}\n{wrapped_robot_message}')
            wrapped_user_message = textwrap.fill(self.user_message, width=total_width)
            print(f'{BOLD}Último mensaje del estudiante:{END}\n{wrapped_user_message}')
            print(separator)
    def on_shutdown_callback(self, msg):
        if msg.data == 'Cerrar supervisor':
            self.get_logger().info('Finalizada la sesión')
            self.destroy_node()    

def main(args=None):
    rclpy.init(args=args)
    node = Supervisor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.handle:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()