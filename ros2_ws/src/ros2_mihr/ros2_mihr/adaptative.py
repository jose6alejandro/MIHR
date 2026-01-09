import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import setup_robot as sr 
class Adaptative(Node):
    def __init__(self):
        super().__init__('Adaptative')

        self.subscription = self.create_subscription(
            String,
            'estado_actual',
            self.response_callback,
            10
        )
        self.subscription_2 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
        10) 

        self.publisher_ = self.create_publisher(String, 'personalizacion', 10)
        self.publisher_2 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(3)
        self.count = 0
        self.publisher_2.publish(sr.state_updated(f'Adaptativo:Inicializado:{self.count}'))
        
        self.context_data = ""
        self.user_data = ""
        self.get_data_kg()
        self.get_logger().info('Data del grafo cargada')

    def get_data_kg(self):

        objective = sr.get_objective()
        #print(objective)
        info = sr.configuration_json('info')
        context_rules = info['rules'][1]['descripcion']
        context_data_aux =sr.extract_kg_data('GOOGLE_API_KEY', 'prompt_test', 
                            context_rules, objective).replace("```json", "").replace("```", "").strip()
        try:
            context_data_aux = json.loads(context_data_aux)
        except Exception as e:
            context_data_aux = {"ejercicios": f"{context_data_aux}"}
        
        self.context_data = json.dumps(context_data_aux, ensure_ascii=False, indent=4)
        #self.get_logger().info(self.context_data)

        format_output = "usuario: name, experiencia_previa: caracteristicas"
        user_rules = info['rules'][2]['descripcion']
        self.user_data_aux  = sr.extract_kg_data('GOOGLE_API_KEY', 'prompt_test', 
                                                          user_rules, objective, format_output).replace("```json", "").replace("```", "").strip()
        try:
            self.user_data_aux = json.loads(self.user_data_aux)
        except Exception as e:    
            self.user_data_aux = {"usuario": f"{self.user_data_aux}"}

        self.user_data = json.dumps(self.user_data_aux, ensure_ascii=False, indent=4)
        print(self.user_data)

    def on_shutdown_callback(self, msg):
        self.publisher_2.publish(sr.state_updated(f'Adaptativo:Cerrado:{self.count}'))
        self.destroy_node()

    def response_callback(self, msg_in):
        self.count += 1
        self.publisher_2.publish(sr.state_updated(f'Adaptativo:Trabajando:{self.count}'))

        current_state = msg_in.data
        #self.get_logger().info(current_state) 
        data_to_send = None
        
        if 'Exploración' in current_state or 'Aprendizaje' in current_state:
            data_to_send = self.context_data
        elif 'Saludo' in current_state or 'Vínculo' in current_state: 
            try:
                if 'nuevo usuario' in self.user_data_aux['experiencia_previa']:
                    data_to_send = "usuario nuevo y sin experiencia previa: pregunte el nombre"
                
                elif  'no hay' in self.user_data_aux['experiencia_previa']:
                    data_to_send = "usuario sin experiencia previa"
                else: 
                    data_to_send = self.user_data  
            except KeyError:
                data_to_send = None
       
        elif 'Objetivo' in current_state:
            try:
                if  'no hay' in self.user_data_aux['experiencia_previa'] or 'nuevo usuario' in self.user_data_aux['experiencia_previa']:
                    data_to_send = "experiencia: es la primera sesión con el usuario"
                else:
                    data_to_send = self.user_data 
            
            except KeyError:
                data_to_send = None                   
       
        elif 'Cierre' in current_state: 
            data_to_send = "Haz un despedida personalizada"        
        else: 
            data_to_send = self.user_data

        msg_out = String()
        msg_out.data = str(data_to_send)
        #self.get_logger().info(f'{msg_out.data}')
        self.publisher_.publish(msg_out)       

        time.sleep(1)
        self.publisher_2.publish(sr.state_updated(f'Adaptativo:Espera:{self.count}'))
        #self.get_logger().info('Publicada la personalización.')


def main(args=None):
    rclpy.init(args=args)
    node = Adaptative()

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

    