import rclpy
import datetime
from rclpy.node import Node
from std_msgs.msg import String
from functools import partial

import setup_robot as sr 

class Record(Node):
    def __init__(self):
        super().__init__('Record')

        self.subscription_1 = self.create_subscription(
            String,
            'mensaje',
            partial(self.listener_callback, 'Estudiante'),
            10
        )

        self.subscription_2 = self.create_subscription(
            String,
            'respuesta_verbal', # Suscripción al tópico 'respuesta_robot' arreglar
            partial(self.listener_callback, 'Robot'),
            10
        )

        self.subscription_3 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
            10
        ) 

        self.publisher_ = self.create_publisher(String, 'historial', 10)

        self.chat_history = []
        self.str_chat =''

        #self.get_logger().info(f'Nodo de registro inicializado')

    def listener_callback(self, topic_name, msg):
        #self.get_logger().info(f'Guardado mensaje del {topic_name}')
        new_msg = f'{topic_name}: {msg.data}'
        self.chat_history.append(new_msg)
        msg = String()
        self.str_chat = str(self.chat_history).replace("',", "\'\n").replace("[", "").replace("]", "").strip()
        msg.data = self.str_chat
        self.publisher_.publish(msg)
        #self.get_logger().info(f'Publicado el historial actual')

    def on_shutdown_callback(self, msg):
        #self.save_data()
        #self.get_logger().info('Nodo record cerrado')
        self.destroy_node()

    def save_data(self):
        now = datetime.datetime.now()
        time_now = "%Y%d%m_%H%M%S"
        record_name = now.strftime(f"{time_now}")
        config = self.load_ablation_settings()
        file_name = f"lasdai_ula/registro/Historial_{record_name}_{config}.txt"
        
        with open(file_name, 'w') as file:
            file.write(f'Objetivo: {sr.get_objective()}\n')
            file.write(f'Sesion: {record_name}\n')
            file.write(self.str_chat)

    def load_ablation_settings(self):
        with open('../config.txt', 'r') as archivo:
            config = archivo.read()
        
        return config


def main(args=None):
    rclpy.init(args=args)
    node = Record()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:

        if node.handle:
            node.save_data()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()