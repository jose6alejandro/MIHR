import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import random 
import setup_robot as sr 
import json

class Affective(Node):
    def __init__(self):
        super().__init__('Affective')
        
        self.publisher_2 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(2)
        #self.profile_data = "analitico" # por defecto
        self.count = 0
        self.publisher_2.publish(sr.state_updated(f'Afectivo:Inicializado:{self.count}'))   

    
    def profile_callback(self, msg):
        self.message_store['profile'] = msg.data

    def emotion_callback(self, msg):
        self.message_store['emotion'] = msg.data

    def on_shutdown_callback(self, msg):
        self.publisher_2.publish(sr.state_updated(f'Afectivo:Cerrado:{self.count}'))  
        self.destroy_node()
    
    def sync_callback(self):
       
        if 'emotion' in self.message_store:
            self.count += 1
            self.publisher_2.publish(sr.state_updated(f'Afectivo:Trabajando:{self.count}'))  
            
            self.profile_data = self.message_store.get('profile')
            self.emotion_data = self.message_store.pop('emotion')

            if self.emotion_data.lower() == "none":
                self.emotion_data = "neutral"
                        
            #self.get_logger().info(f'recibido: {self.emotion_data}, {self.profile_data}')
            prompt_llm  = self.prompt_template.format(emotion=self.emotion_data, profile=self.profile_data)
            
            response = self.llm.invoke(
                prompt_llm, 
                response_model=String
            )
            response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())
            
            msg = String()
            msg.data = f'{self.node_name}:{response_json["emocion"]}'
            self.publisher_.publish(msg)
            self.publisher_2.publish(sr.state_updated(f'Afectivo:Espera:{self.count}'))  
            #self.get_logger().info(f'Publicado: emoción del robot {msg.data}')

    def validation_of_operation(self):
         
        #self.get_logger().info('Nodo afectivo en validación')
        
        llm, prompt_affective = sr.configuration('GOOGLE_API_KEY3', 'prompt_afectivo', 'gemini-2.5-flash-lite')
        llm2, prompt_evaluator = sr.configuration('GOOGLE_API_KEY3', 'prompt_evaluador', 'gemini-2.5-flash-lite')

        info = sr.configuration_json('info')
        description = info['node'][0]['descripcion']
       
        rules_text = info['rules'][0]['descripcion']

        objective = f'Dame {sr.num_shots} pruebas unitarias del componente afectivo con todas las propiedades: name, entrada1, entrada2, salida, score'

        data = sr.extract_kg_data('GOOGLE_API_KEY2', 'prompt_test', rules_text, objective)

        data_json = json.loads(data.replace("```json", "").replace("```", "").strip())

        few_shots = json.dumps(data_json, ensure_ascii=False, indent=8)
        print(few_shots)

        score = 0
        for i in range(sr.num_shots):
            
            self.count += 1
            self.publisher_2.publish(sr.state_updated(f'Afectivo:Validando:{self.count}'))

            current_case = data_json[i]
            #self.get_logger().info(f'Prueba: {i}')
            #Execution node     
            prompt_llm  = prompt_affective.format(emotion=current_case["entrada1"], profile=current_case["entrada2"])
            response = llm.invoke(
                prompt_llm, 
                response_model=String
            )
            response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())

            _case_to_evaluated = {
                "entrada1": current_case["entrada1"],
                "entrada2": current_case["entrada2"],
                "salida": response_json["emocion"]
            }
            case_to_evaluated = json.dumps(_case_to_evaluated, ensure_ascii=False, indent=8) 

            #Validation node
            prompt_llm  = prompt_evaluator.format(description=description, few_shots=few_shots, case_to_evaluated=case_to_evaluated)
            #self.get_logger().info(f'{prompt_llm}')
            response = llm2.invoke(
                prompt_llm, 
                response_model=String
            )
            response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())
            #self.get_logger().info(f'resultado: {response_json["score"]}, {response_json["explicacion"]}')
            score += int(response_json["score"])
        
        score = score / sr.num_shots
        self.get_logger().info(f'Score final: {score}, porcentaje {(score/3)*100}%')
        self.publisher_2.publish(sr.state_updated(f'Afectivo:Cerrado:{self.count}'))
        time.sleep(2)
        self.destroy_node()


    def execution(self):
        self.subscription_ = self.create_subscription(
            String,
            'personalidad',
            self.profile_callback,
            10
        )

        self.subscription_2 = self.create_subscription(
            String,
            'emocion',
            self.emotion_callback,
            10
        )

        self.subscription_3 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
            10
        ) 
               
        self.message_store = {}
        self.last_sync_time = self.get_clock().now()
        self.timer = self.create_timer(1.0, self.sync_callback)
        
        self.publisher_ = self.create_publisher(String, 'emocion_robot', 10)
        self.node_name  = self.get_name()
        self.profile_data = 'analitico'  #por defecto 
        self.llm, self.prompt_template = sr.configuration('GOOGLE_API_KEY', 'prompt_afectivo', 'gemini-2.5-flash')


def main(args=None):
    rclpy.init(args=args)
    node = Affective()
   
    if sr.validate_operation:
        #self.get_logger().info(f'validando')
        node.validation_of_operation()
    else:
        #self.get_logger().info(f'ejecutando')
        node.execution()
   
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