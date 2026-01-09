import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from lasdai_ula.modulo import pr1_ula as pr1

import random
import time 
import json
import setup_robot as sr 

class Verbal(Node):
    def __init__(self):
        super().__init__('Verbal')
               
        self.message_store = {}
        self.last_sync_time = self.get_clock().now()
        self.timer = self.create_timer(0.5, self.sync_callback)       

        self.publisher_ = self.create_publisher(String, 'respuesta_verbal', 10)       
        self.publisher_2 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(2)
        self.count = 0
        self.user_feature_data = ""
        self.gender_data = ""  
        self.profile_data = "" 
        self.publisher_2.publish(sr.state_updated(f'Verbal:Inicializado:{self.count}'))

    def profile_callback(self, msg):
        self.message_store['profile'] = msg.data

    def gender_callback(self, msg):
        self.message_store['gender'] = msg.data

    def personalization_callback(self, msg):
        self.message_store['user_feature'] = msg.data
    
    def record_callback(self, msg):
        self.message_store['record'] = msg.data

    def current_state_callback(self, msg):
        self.message_store['current_state'] = msg.data

    def on_shutdown_callback(self, msg):
        self.publisher_2.publish(sr.state_updated(f'Verbal:Cerrado:{self.count}'))
        self.destroy_node()

    def sync_callback(self):
        #self.get_logger().info(f'ssss>{self.message_store}')
        if  self.message_store and 'record' in self.message_store and 'current_state' in self.message_store:
            self.count += 1
            self.publisher_2.publish(sr.state_updated(f'Verbal:Trabajando:{self.count}'))
            
            self.profile_data = self.message_store.get('profile')
            self.gender_data = self.message_store.get('gender')
            self.user_feature_data = self.message_store.get('user_feature')
            self.get_logger().info(f'Adaptativo: {self.user_feature_data}')
            self.record_data = self.message_store.pop('record')
            self.current_state_data = self.message_store.pop('current_state')
            #self.get_logger().info(f'{self.profile_data}, {self.gender_data}, {self.personalization_data}, {self.record_data}')
            self.execute_prompt()
            
            self.publisher_2.publish(sr.state_updated(f'Verbal:Espera:{self.count}'))
    
    def execute_prompt(self):
        
        if self.prompt_template:
            prompt_llm  = self.prompt_template.format(profile=self.profile_data, gender=self.gender_data, user_feature=self.user_feature_data, record=self.record_data, current_state=self.current_state_data) 

            response = self.llm.invoke(
                prompt_llm, 
                response_model=String
            )
            msg = String()
            msg.data = response.content
            self.publisher_.publish(msg)
            #self.get_logger().info(f'Publicada la respuesta del robot: {msg.data}')

    def init_message(self):
        greetings = ["¡Hola! listo para comenzar?", "¡Hola! ¿estás preparado?", "¡Buenas! ¿empezamos?", "¡Bienvenido! ¿arrancamos?", "¡Saludos! ¿listo para iniciar?", "¡Qué tal! ¿comenzamos la sesión?", "¿Cómo estás? ¿preparado para empezar?", "¡Hola! ¿estamos listos?"]
        selected_index = random.randint(0, len(greetings) - 1)
        self.count += 1
        self.publisher_2.publish(sr.state_updated(f'Verbal:Trabajando:{self.count}'))
        init_msg = String()
        init_msg.data = greetings[selected_index]
        self.publisher_.publish(init_msg)
        self.publisher_2.publish(sr.state_updated(f'Verbal:Espera:{self.count}'))

    def validation_of_operation(self):
        llm, prompt_verbal = sr.configuration('GOOGLE_API_KEY3', 'prompt_verbal', 'gemini-2.5-flash')
        llm2, prompt_evaluator = sr.configuration('GOOGLE_API_KEY3', 'prompt_evaluador', 'gemini-2.5-flash')

        info = sr.configuration_json('info')
        description = info['node'][3]['descripcion']
       
        rules_text = info['rules'][0]['descripcion']

        objective = f'Dame {sr.num_shots} pruebas unitarias del componente verbal con todas las propiedades: name, entrada1, entrada2, entrada3, entrada4, entrada5, salida, score'

        data = sr.extract_kg_data('GOOGLE_API_KEY2', 'prompt_test', rules_text, objective)

        data_json = json.loads(data.replace("```json", "").replace("```", "").strip())

        few_shots = json.dumps(data_json, ensure_ascii=False, indent=8)
        print(few_shots)

        score = 0
        for i in range(sr.num_shots):
            self.count += 1
            self.publisher_2.publish(sr.state_updated(f'Verbal:Validando:{self.count}'))
           
            current_case = data_json[i]
            prompt_llm  = prompt_verbal.format(profile=current_case["entrada1"], gender=current_case["entrada2"], user_feature=current_case["entrada3"], record=current_case["entrada4"], current_state=current_case["entrada5"]) 
            response = llm.invoke(
                prompt_llm, 
                response_model=String
            )
            
            _case_to_evaluated = {
                "entrada1": current_case["entrada1"],
                "entrada2": current_case["entrada2"],
                "entrada3": current_case["entrada3"],
                "entrada4": current_case["entrada4"],
                "entrada5": current_case["entrada5"],     
                "salida": response.content
            }
            case_to_evaluated = json.dumps(_case_to_evaluated, ensure_ascii=False, indent=8) 

            prompt_llm  = prompt_evaluator.format(description=description, few_shots=few_shots, case_to_evaluated=case_to_evaluated)
            
            response = llm2.invoke(
                prompt_llm, 
                response_model=String
            )
            response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())
            score += int(response_json["score"])

        score = score / sr.num_shots
        self.get_logger().info(f'Score final: {score}, porcentaje {(score/3)*100}%')
        self.publisher_2.publish(sr.state_updated(f'Verbal:Cerrado:{self.count}'))
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
            'genero',
            self.gender_callback,
            10
        )

        self.subscription_3 = self.create_subscription(
            String,
            'personalizacion',
            self.personalization_callback,
            10
        )
        self.subscription_4 = self.create_subscription(
            String,
            'historial',
            self.record_callback,
            10
        )
        self.subscription_5 = self.create_subscription(
            String,
            'estado_actual',
            self.current_state_callback,
            10
        )        

        self.subscription_6 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
            10
        ) 

        self.llm, self.prompt_template = sr.configuration('GOOGLE_API_KEY', 'prompt_verbal', 'gemini-2.5-flash')

        # self.message_store = {}
        # self.last_sync_time = self.get_clock().now()
        # self.timer = self.create_timer(0.5, self.sync_callback)
        time.sleep(1)
        self.init_message()

def main(args=None):
    rclpy.init(args=args)
    node = Verbal()
    
    if sr.validate_operation:
        #self.get_logger().info(f'validando')
        node.validation_of_operation()
    else:
        #self.get_logger().info(f'ejecutando'
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
