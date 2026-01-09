import time

import rclpy
import json
from rclpy.node import Node
from std_msgs.msg import String
from lasdai_ula.modulo import pr1_ula as pr1
from langchain_google_genai import ChatGoogleGenerativeAI

import setup_robot as sr

class Normative(Node):
    def __init__(self):
        super().__init__('Normative')

        self.publisher_ = self.create_publisher(String, 'genero', 10)
        self.publisher_2 = self.create_publisher(String, 'personalidad', 10)

        self.llm, self.prompt_template = sr.configuration('GOOGLE_API_KEY', 'prompt_normativo', 'gemini-2.5-flash')
        self.objective_data = sr.get_objective()

        self.publisher_3 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(2)
        self.count = 0
        self.publisher_3.publish(sr.state_updated(f'Normativo:Inicializado:{self.count}'))
        #self.get_logger().info('Nodo normativo inicializado')

    def validation_of_operation(self):
        llm, prompt_normative = sr.configuration('GOOGLE_API_KEY2', 'prompt_normativo', 'gemini-2.5-flash')
        llm2, prompt_evaluator = sr.configuration('GOOGLE_API_KEY2', 'prompt_evaluador', 'gemini-2.5-flash')

        info = sr.configuration_json('info')
        description = info['node'][1]['descripcion']
       
        rules_text = info['rules'][0]['descripcion']

        objective = f'Dame {sr.num_shots} pruebas unitarias del componente normativo con todas las propiedades: name, entrada, salida, score'

        data = sr.extract_kg_data('GOOGLE_API_KEY2', 'prompt_test', rules_text, objective)

        data_json = json.loads(data.replace("```json", "").replace("```", "").strip())

        few_shots = json.dumps(data_json, ensure_ascii=False, indent=8)
        print(few_shots)

        score = 0
        for i in range(sr.num_shots):
            self.count += 1
            self.publisher_3.publish(sr.state_updated(f'Normativo:Validando:{self.count}'))

            current_case = data_json[i]

            prompt_llm  = prompt_normative.format(objective=current_case["entrada"])
            response = llm.invoke(
                prompt_llm,
                response_model=String
            )
            response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())

            _case_to_evaluated = {
                "entrada": current_case["entrada"],
                "salida": f'{response_json["personalidad"]}, {response_json["genero"]}'
            }
            case_to_evaluated = json.dumps(_case_to_evaluated, ensure_ascii=False, indent=8)

            prompt_llm  = prompt_evaluator.format(description=description, few_shots=few_shots, case_to_evaluated=case_to_evaluated)

            response = llm2.invoke(
                prompt_llm,
                response_model=String
            )
            response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())
            self.get_logger().info(f'resultado: {response_json["score"]}, {response_json["explicacion"]}')
            score += int(response_json["score"])

        score = score / sr.num_shots
        self.get_logger().info(f'Score final: {score}, porcentaje {(score/3)*100}%')
        self.publisher_3.publish(sr.state_updated(f'Normativo:Cerrado:{self.count}'))


    def execute_llm(self):
        if self.prompt_template and self.objective_data:
            self.count += 1
            self.publisher_3.publish(sr.state_updated(f'Normativo:Trabajando:{self.count}'))

            prompt_llm  = self.prompt_template.format(objective=self.objective_data)

            response = self.llm.invoke(
                prompt_llm,
                response_model=String
            )

            response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())

            msg = String()
            msg2 = String()
            self.gender = response_json["genero"]
            self.personality = response_json["personalidad"]
            msg.data = self.gender
            self.publisher_.publish(msg)
            msg2.data = self.personality
            self.publisher_2.publish(msg2)

            #self.publisher_3.publish(sr.state_updated(f'Normativo:Espera:{self.count}'))
            #self.get_logger().info(f'Publicado genero del estudiante: {msg.data} y perfil del robot: {msg2.data}')

        else:
            self.get_logger().info('El prompt no está disponible')


def main(args=None):
    rclpy.init(args=args)

    node = Normative()

    try:

        if sr.validate_operation:
            node.get_logger().info(f'validando')
            node.validation_of_operation()
        else:
            #node.get_logger().info(f'ejecutando')
            node.execute_llm()
    except KeyboardInterrupt:
        pass
    finally:
        node.publisher_3.publish(sr.state_updated(f'Normativo:Cerrado:{node.count}'))
        node.destroy_node()
        rclpy.shutdown()
if __name__ == '__main__':
    main()
