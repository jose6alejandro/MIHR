import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import setup_robot as sr 

class Paraverbal(Node):
    def __init__(self):
        super().__init__('Paraverbal')
        
        self.subscription = self.create_subscription(
            String,
            'personalidad',
            self.profile_callback,
            10)
                
        self.subscription_2 = self.create_subscription(
            String,
            'emocion_robot',
            self.emotion_callback,
            10
        )

        self.subscription_3 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
        10) 
        self.message_store = {}
        self.last_sync_time = self.get_clock().now()
        self.timer = self.create_timer(1.0, self.sync_callback)

        self.rules = sr.configuration_json('paraverbal') 
        self.voice_initial = 0
        self.publisher_ = self.create_publisher(String, 'voz_robot', 10)
        
        self.publisher_2 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(2)
        self.count = 0
        self.publisher_2.publish(sr.state_updated(f'Paraverbal:Inicializado:{self.count}')) 
        #self.get_logger().info('Nodo paraverbal inicializado')

    def profile_callback(self, msg):
        self.message_store['profile'] = msg.data
        self.voice_initial += 1

    def emotion_callback(self, msg):
        self.emotion_data = msg.data.split(":")
        if self.emotion_data[0] == 'Affective':
            self.message_store['emotion'] = self.emotion_data[1]
    
    def on_shutdown_callback(self, msg):
        self.publisher_2.publish(sr.state_updated(f'Paraverbal:Cerrado:{self.count}')) 
        self.destroy_node()

    def sync_callback(self):
        if self.voice_initial == 1:
            self.message_store['emotion'] = 'neutral'

        if 'emotion' in self.message_store and self.rules:
            #if 'emotion' in self.message_store and 'profile' in self.message_store and self.rules:
            self.count += 1
            self.publisher_2.publish(sr.state_updated(f'Paraverbal:Trabajando:{self.count}')) 

            current_profile = self.message_store.get('profile', 'analitico') #default
            current_emotion = self.message_store.pop('emotion', 'neutral') #default

            profile_rules = self.rules.get(current_profile, self.rules.get('analitico', {}))
            output_value = profile_rules.get(current_emotion, profile_rules.get('neutral'))

            if output_value:
                msg = String()
                msg.data = output_value
                #self.get_logger().info(f'{current_profile}-----{msg.data}')
                self.publisher_.publish(msg)
                time.sleep(1)
                self.voice_initial += 1
                self.publisher_2.publish(sr.state_updated(f'Paraverbal:Espera:{self.count}'))

def main(args=None):
    rclpy.init(args=args)
    node = Paraverbal()
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