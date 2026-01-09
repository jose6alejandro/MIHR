import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from lasdai_ula.modulo import pr1_ula as pr1

import time
import setup_robot as sr

import cv2
import datetime

from rclpy.executors import SingleThreadedExecutor

class Perception(Node):
    def __init__(self,node_name ='perception_default'):
        super().__init__(node_name)
        
        self.subscription = self.create_subscription(
            String,
            'respuesta_robot',
            self.response_callback,
            10)
        self.subscription_2 = self.create_subscription(
            String,
            'estado_actual',
            self.state_callback,
            10)        
        self.flag = False
        self.state = ''
        self.publisher_ = self.create_publisher(String, 'aviso', 10)
        self.publisher_2 = self.create_publisher(String, 'cerrar_nodo', 10)

        self.publisher_3 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(2)
        self.count = 0
        self.publisher_3.publish(sr.state_updated(f'Percepción:Inicializado:{self.count}'))

        #self.get_logger().info('Nodo de percepción inicializado')

    def response_callback(self, msg):
        self.count += 1
        self.publisher_3.publish(sr.state_updated(f'Percepción:Trabajando:{self.count}'))

        msg = String()
        msg.data = 'Turno del estudiante'
        self.flag = True
        self.on_shutdown_callback(msg)
    
    def state_callback(self, msg):
        self.state = msg.data.split(':')[0]
        
    def on_shutdown_callback(self, msg):
        #self.get_logger().info(f'<<<{self.state}, {self.flag}>>>')
        if self.flag == True:
            if self.state != 'Cierre':
                self.flag = False
                self.publisher_.publish(msg)
                time.sleep(1)
                self.publisher_3.publish(sr.state_updated(f'Percepción:Espera:{self.count}'))
                #self.get_logger().info(f'<<<{msg.data}>>>')
            else:
                msg = String()
                msg.data = 'Cerrar nodo'
                self.publisher_2.publish(msg)
                self.publisher_3.publish(sr.state_updated(f'Percepción:Cerrado:{self.count}'))
                time.sleep(5)
                msg.data = 'Cerrar supervisor'
                self.publisher_2.publish(msg)               
                self.destroy_node()

class Perception_Img(Node):
    def __init__(self, node_name ='perception_default'):
        super().__init__(node_name)

        self.subscription = self.create_subscription(
            String,
            'respuesta_verbal',
            self.response_callback,
            10)

        self.subscription_2 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
        10) 

        self.publisher_ = self.create_publisher(String, 'imagen', 10)

        self.publisher_2 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(2)
        self.count = 0
        self.publisher_2.publish(sr.state_updated(f'Percepción_Img:Inicializado:{self.count}')) 

        #self.get_logger().info('Nodo de percepción de imagen inicializado')


    def capture_img(self, image_file):     
        
        cap = cv2.VideoCapture(0)
        try:
            if not cap.isOpened():
                self.get_logger().error("Error: No se pudo abrir la cámara. Asegúrese de que esté conectada y no en uso.")
                return None

            # self.get_logger().info("Ajustando la exposición de la cámara...")
            for _ in range(10):
                cap.read()
                pr1.time.sleep(0.1)

            ret, frame = cap.read()
            if not ret:
                self.get_logger().error("Error: No se pudo capturar un fotograma de la cámara.")
                return None

            cv2.imwrite(image_file, frame)
            # self.get_logger().info(f"Foto guardada como {image_file}")
            return image_file

        except Exception as e:
            self.get_logger().error(f"Ocurrió un error inesperado durante la captura de la imagen: {e}")
            return None
        finally:
            if cap.isOpened():
                cap.release()

    def on_shutdown_callback(self, msg):
        self.publisher_2.publish(sr.state_updated(f'Percepción_Img:Cerrado:{self.count}')) 
        self.destroy_node()

    def response_callback(self, msg):
        # Capturar imagen
        self.count += 1
        self.publisher_2.publish(sr.state_updated(f'Percepción_Img:Trabajando:{self.count}'))          
        
        now = datetime.datetime.now()
        image_name = now.strftime("IMG_%Y%d%m_%H%M%S")
        image_file = f'lasdai_ula/images/{image_name}.jpg'
        self.capture_img(image_file)
        msg = String()
        msg.data = image_file
        
        self.publisher_.publish(msg)
        self.publisher_2.publish(sr.state_updated(f'Percepción_Img:Espera:{self.count}')) 
        #self.get_logger().info(f'Publicada la imagen')


def main(args=None):
    rclpy.init(args=args)
    executor = SingleThreadedExecutor()
    node = Perception(node_name = 'Perception')
    node_img = Perception_Img(node_name = 'Perception_img')
    executor.add_node(node)
    executor.add_node(node_img)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        if node.handle:
            node.destroy_node()
        if node_img.handle:    
            node_img.destroy_node()
        if rclpy.ok():
            executor.shutdown()

if __name__ == '__main__':
    main()