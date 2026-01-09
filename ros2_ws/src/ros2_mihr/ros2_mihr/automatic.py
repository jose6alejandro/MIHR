import time
import rclpy
import json
from rclpy.node import Node
from std_msgs.msg import String
from sympy.logic.boolalg import And, Or
from sympy import symbols

import setup_robot as sr 

class Automatic(Node):
    def __init__(self):
        super().__init__('Automatic')
               
        self.subscription_ = self.create_subscription(
            String,
            'emocion',
            self.emotion_callback,
            10
        )

        self.subscription_2 = self.create_subscription(
            String,
            'posicion',
            self.position_callback,
            10
        )

        self.subscription_3 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
        10) 
        
        self.message_store = {}
        self.last_sync_time = self.get_clock().now()
        self.timer = self.create_timer(0.5, self.sync_callback)
        self.node_name  = self.get_name()
        
        self.rules = sr.configuration_json('automatico')

        self.publisher_ = self.create_publisher(String, 'emocion_robot', 10)
        self.publisher_2 = self.create_publisher(String, 'posicion_robot', 10)
        self.publisher_3 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(3)
        self.count = 0
        self.publisher_3.publish(sr.state_updated(f'Automático:Inicializado:{self.count}'))  

        #self.get_logger().info('Nodo automático inicializado')

    def emotion_callback(self, msg):
        self.message_store['emotion'] = msg.data

    def position_callback(self, msg):
        self.message_store['position'] = msg.data

    def on_shutdown_callback(self, msg):
        self.publisher_3.publish(sr.state_updated(f'Automático:Cerrado:{self.count}'))
        self.destroy_node()

    def sync_callback(self):
        if 'emotion' in self.message_store and 'position' in self.message_store:
            self.count += 1
            self.publisher_3.publish(sr.state_updated(f'Automático:Trabajando:{self.count}'))             
            self.emotion_data = self.message_store.pop('emotion')
            self.position_data = self.message_store.pop('position')
            
            self.emotions = ["triste", "feliz", "ira", "miedo", "neutral", "sorpresa"]
            self.positions = ["derecha", "izquierda", "centro"]
        
            facts = {emocion: self.emotion_data == emocion for emocion in self.emotions}
            facts.update({posicion: self.position_data == posicion for posicion in self.positions})

            variables = symbols(list(facts.keys()))
            simbolos_map = {str(var): var for var in variables}
        
            msg = String()
            msg_2 = String()
            rule_matched = False

            for rule in self.rules:
                condition_str = rule['condicion']
                emotion_output = rule['emocion_salida']
                position_output = rule['posicion_salida']

                try:
                    
                    expresion = eval(condition_str, {}, simbolos_map)
                
                    if expresion.subs(facts):
                        #self.get_logger().info(f"La condición '{condition_str}' es verdadera.")
                        #self.get_logger().info(f"El robot muestra la emoción: {emotion_output} y mira a la posición: {position_output}")
                        msg.data = f'{self.node_name}:{emotion_output}'         
                        self.publisher_.publish(msg)
                        msg_2.data = f'pos_{self.node_name}:{position_output}'
                        self.publisher_2.publish(msg_2)
                        time.sleep(1)
                        self.publisher_3.publish(sr.state_updated(f'Automático:Espera:{self.count}')) 
                        #self.get_logger().info(f'Publicado: {msg.data}, {msg_2.data}')
                        rule_matched = True
                        break
                except Exception as e:
                    self.get_logger().info(f"Error al evaluar la condición '{condition_str}': {e}")
        
            if not rule_matched:
                msg.data = f'{self.node_name}:neutral'
                msg_2.data = f'pos_{self.node_name}:centro'
                self.publisher_.publish(msg)
                self.publisher_2.publish(msg_2)
                time.sleep(1)
                self.publisher_3.publish(sr.state_updated(f'Automático:Espera:{self.count}')) 
               #self.get_logger().info(f'Publicado {msg.data}, {msg_2.data}')   
                
def main(args=None):
    rclpy.init(args=args)
    node = Automatic()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.handle:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown() 