import time
import rclpy
import json
from rclpy.node import Node
from std_msgs.msg import String
from lasdai_ula.modulo import pr1_ula as pr1
from langchain_google_genai import ChatGoogleGenerativeAI

import setup_robot as sr 

class Deliberative(Node):
    def __init__(self):
        super().__init__('Deliberative')

        self.publisher_2 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(2)
        self.count = 0
        self.publisher_2.publish(sr.state_updated(f'Deliberativo:Inicializado:{self.count}'))  

    def robot_message_callback(self, msg):
        self.message_store['robot_message'] = msg.data

    def user_message_callback(self, msg):
        self.message_store['user_message'] = msg.data

    def on_shutdown_callback(self, msg):
        self.publisher_2.publish(sr.state_updated(f'Deliberativo:Cerrado:{self.count}')) 
        self.destroy_node()

    def sync_callback(self):

        if 'robot_message' in self.message_store and 'user_message' in self.message_store:
            #self.get_logger().info(f' deliberativo{self.message_store}') 
            self.count += 1
            self.publisher_2.publish(sr.state_updated(f'Deliberativo:Trabajando:{self.count}')) 
            robot_message_data = self.message_store.pop('robot_message')
            user_message_data = self.message_store.pop('user_message')
            action, state = None, None

            while not action and not state:
                prompt_llm  = self.prompt_template.format(objective=self.objective_data, current_user_message=user_message_data, current_state=self.current_state, current_robot_message=robot_message_data)
            
                response = self.llm.invoke(
                    prompt_llm, 
                    response_model=String
                )
                response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())
                action = response_json.get("accion", None)
                state = response_json.get("estado", None)

            self.current_state_ = f'{state}: {action}'
            msg = String()
            msg.data = self.current_state_
            self.publisher_.publish(msg)
            self.current_state = response_json["estado"]
            self.publisher_2.publish(sr.state_updated(f'Deliberativo:Espera:{self.count}')) 
            #self.get_logger().info(f'Publicado {msg.data}\n')
        #else:
        #    self.get_logger().info('Aún esperando ambos mensajes...')

    def validation_of_operation(self):
        llm, prompt_deliberative = sr.configuration('GOOGLE_API_KEY3', 'prompt_deliberativo', 'gemini-2.5-flash-lite')
        llm2, prompt_evaluator = sr.configuration('GOOGLE_API_KEY3', 'prompt_evaluador', 'gemini-2.5-flash-lite')

        info = sr.configuration_json('info')
        description = info['node'][2]['descripcion']
       
        rules_text = info['rules'][0]['descripcion']

        objective = f'Dame {sr.num_shots} pruebas unitarias del componente deliberativo con todas las propiedades: name, entrada1, entrada2, entrada3, salida, score'

        data = sr.extract_kg_data('GOOGLE_API_KEY2', 'prompt_test', rules_text, objective)

        data_json = json.loads(data.replace("```json", "").replace("```", "").strip())

        few_shots = json.dumps(data_json, ensure_ascii=False, indent=8)
        print(few_shots)

        score = 0
        for i in range(sr.num_shots):
            self.count += 1
            self.publisher_2.publish(sr.state_updated(f'Deliberativo:Validando:{self.count}'))
           
            current_case = data_json[i]
            
            prompt_llm  = prompt_deliberative.format(objective="...", current_state=current_case["entrada1"], current_robot_message=current_case["entrada2"], current_user_message=current_case["entrada3"])
            response = llm.invoke(
                prompt_llm, 
                response_model=String
            )
            response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())
            
            _case_to_evaluated = {
                "entrada1": current_case["entrada1"],
                "entrada2": current_case["entrada2"],
                "entrada3": current_case["entrada3"],
                "salida": f'{response_json["estado"]}, {response_json["acción"]}'
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
        self.publisher_2.publish(sr.state_updated(f'Deliberativo:Cerrado:{self.count}'))
        time.sleep(2)
        self.destroy_node()

    def execution(self):
        self.subscription_ = self.create_subscription(
            String,
            'respuesta_verbal',
            self.robot_message_callback,
            10
        )
        self.subscription_2 = self.create_subscription(
            String,
            'mensaje',
            self.user_message_callback,
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

        self.llm, self.prompt_template = sr.configuration('GOOGLE_API_KEY', 'prompt_deliberativo', 'gemini-2.5-flash-lite', 0.5)
        self.objective_data = sr.get_objective()

        self.current_state = 'Saludo: el robot debe iniciar la conversación'
        self.publisher_ = self.create_publisher(String, 'estado_actual', 10)

def main(args=None):
    rclpy.init(args=args)
    node = Deliberative()
   
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