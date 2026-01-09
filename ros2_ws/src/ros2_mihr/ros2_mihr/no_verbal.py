import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time
from sympy import symbols
from sympy.parsing.sympy_parser import parse_expr
import setup_robot as sr 

import random

class No_verbal(Node):
    def __init__(self):
        super().__init__('No_verbal')
        
        self.subscription_ = self.create_subscription(
            String,
            'emocion_robot',
            self.emotion_callback,
            10
        )

        self.subscription_2 = self.create_subscription(
            String,
            'mensaje',
            self.response_robot_callback,
            10
        )

        self.subscription_3 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
        10) 

        self.subscription_4 = self.create_subscription(
            String,
            'respuesta_verbal',
            self.response_verbal_callback,
        10) 
        self.posibilities = ['excelente', 'correcto', 'bien hecho', 'muy bien', 'perfecto', 'me alegra', 'increible']
        self.node_name  = self.get_name()
        self.message_store = {}
        self.last_sync_time = self.get_clock().now()
        self.timer = self.create_timer(0.5, self.sync_callback)

        self.rules = sr.configuration_json('no_verbal')

        self.publisher_ = self.create_publisher(String, 'posicion_robot', 10)
    
        self.publisher_2 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(2)
        self.count = 0
        self.publisher_2.publish(sr.state_updated(f'No_verbal:Inicializado:{self.count}')) 

    def emotion_callback(self, msg):
        self.emotion_data = msg.data.split(":")
        if self.emotion_data[0] == 'Affective':
            self.message_store['emotion'] = self.emotion_data[1]

    def response_robot_callback(self, msg):
        self.message_store['flag'] = msg.data  

    def response_verbal_callback(self, msg):
        
        message = msg.data
        found = any(find_word in message.lower() for find_word in self.posibilities)
       
        if found:
            self.count += 1
            self.publisher_2.publish(sr.state_updated(f'No_verbal:Trabajando:{self.count}'))
            
            msg = String()
            msg.data = f'pos2_{self.node_name}:mov_verbal'
            self.publisher_.publish(msg)
       
            time.sleep(1)
            self.publisher_2.publish(sr.state_updated(f'No_verbal:Espera:{self.count}')) 

    def on_shutdown_callback(self, msg):
        self.publisher_2.publish(sr.state_updated(f'No_verbal:Cerrado:{self.count}')) 
        self.destroy_node()

    def sync_callback(self):
        if 'emotion' in self.message_store and 'flag' in self.message_store:
            self.count += 1
            self.publisher_2.publish(sr.state_updated(f'No_verbal:Trabajando:{self.count}')) 

            current_emotion = self.message_store.pop('emotion', 'neutral')
            self.message_store.pop('flag')

            select_mov = random.randint(0, 10)
            
            
            possible_emotions = ["feliz", "triste", "neutral"]
            possible_numbers = [f"n_{i}" for i in range(11)]

            facts = {emo: current_emotion == emo for emo in possible_emotions}
            facts.update({num_str: f"n_{select_mov}" == num_str for num_str in possible_numbers})

            variables = symbols(list(facts.keys()))
            simbolos_map = {str(var): var for var in variables}
            
            msg = String()
            rule_matched = False

            for rule in self.rules:
                condition_str = rule['condicion']
                output_mov = rule['salida']

                try:
                    expresion = eval(condition_str, {}, simbolos_map)
                
                    if expresion.subs(facts):
                        msg.data = f'pos_{self.node_name}:{output_mov}'
                        time.sleep(2)
                        self.publisher_.publish(msg)
                        
                        rule_matched = True
                        break
                except Exception as e:
                    self.get_logger().error(f"Error al evaluar la condición '{condition_str}': {e}")
            
            if not rule_matched:
                self.get_logger().warn(f"Ninguna regla coincidió para emoción '{current_emotion}' y número '{select_mov}'")
            
            time.sleep(1.5)
            self.publisher_2.publish(sr.state_updated(f'No_verbal:Espera:{self.count}')) 

def main(args=None):
    rclpy.init(args=args)
    node = No_verbal()
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