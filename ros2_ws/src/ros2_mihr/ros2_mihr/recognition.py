import time
import rclpy

import base64
import json
from langchain_core.messages import HumanMessage
from rclpy.node import Node
from std_msgs.msg import String
from lasdai_ula.modulo import pr1_ula as pr1
from lasdai_ula.modulo.pr1_ula import pyaudio, wave, audioop, time, json, io
from lasdai_ula.modulo.pr1_ula import Model, KaldiRecognizer, SetLogLevel
from rclpy.executors import SingleThreadedExecutor

import setup_robot as sr

class Recognition(Node):
    def __init__(self, node_name ='recognition_default'):
        super().__init__(node_name)
        
        self.subscription = self.create_subscription(
            String,
            'aviso', 
            self.response_callback,
            10)

        self.subscription_2 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
            10) 

        self.publisher_ = self.create_publisher(String, 'mensaje', 10)
        self.publisher_2 = self.create_publisher(String, 'monitoreo', 10)
        self.publisher_3 = self.create_publisher(String, 'led', 10)
        
        self.configuration()
        time.sleep(3)
        self.count = 0
        self.publisher_2.publish(sr.state_updated(f'Reconocimiento:Inicializado:{self.count}'))  
        #self.get_logger().info('Nodo de reconocimiento inicializado')

    def configuration(self):
        SetLogLevel(-1)
        self.p = pyaudio.PyAudio()
        self.model = Model(pr1.MODEL)
        self.rec = KaldiRecognizer(self.model, pr1.RATE)

    def on_shutdown_callback(self, msg):
        self.publisher_2.publish(sr.state_updated(f'Reconocimiento:Cerrado:{self.count}')) 
        self.p.terminate()
        self.destroy_node()

    def response_callback(self, msg):  
        
        self.count += 1
        self.publisher_2.publish(sr.state_updated(f'Reconocimiento:Trabajando:{self.count}')) 
        # mientras no se detecta voz
        activation = True
        
        while True:
            stream = self.p.open(format=pr1.FORMAT, channels=pr1.CHANNELS,
                                  rate=pr1.RATE, input=True,
                                  frames_per_buffer=pr1.CHUNK)
            
            texto_transcrito = ""
            silence_start = None

            if activation:
                self.publisher_3.publish(sr.state_updated('green'))
                activation = False 
            #self.get_logger().info('<<< Escuchando >>>')

            while True:
                data = stream.read(pr1.CHUNK, exception_on_overflow=False)
                rms = audioop.rms(data, 2)

                # Transcripción
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    partial_text = result.get("text", "")
                    if partial_text:
                        texto_transcrito += partial_text + " "
                        # self.get_logger().info(f'Parcial: "{partial_text}"')

                # Detección de silencio
                if rms < pr1.SILENCE_THRESHOLD:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > pr1.MAX_SILENCE_SECONDS:
                        break
                else:
                    silence_start = None
           
            stream.stop_stream()
            stream.close()

            final = json.loads(self.rec.FinalResult())
            texto_transcrito += final.get("text", "")
            user_message = texto_transcrito.strip()

            if user_message:
                msg = String()
                msg.data = user_message
                self.publisher_.publish(msg)
                #self.get_logger().info(f' ¡Listo! publicando respuesta del estudiante')
                self.publisher_2.publish(sr.state_updated(f'Reconocimiento:Espera:{self.count}')) 
                self.publisher_3.publish(sr.state_updated('yellow'))
                break
            #else:
            #    self.get_logger().info('<<< No se detectó voz. Reiniciando la grabación >>>')

class Recognition_Img(Node):
    def __init__(self, node_name ='recognition_default'):
        super().__init__(node_name)
        

        self.llm, self.prompt_template = sr.configuration("GOOGLE_API_KEY", 'prompt_imagen', 'gemini-2.5-flash')
        self.response_json = {"emocion":"neutral", "posicion":"centro"} #por defecto
        
        self.publisher_3 = self.create_publisher(String, 'monitoreo', 10)
        
        time.sleep(2)
        self.count = 0

        self.publisher_3.publish(sr.state_updated(f'Reconocimiento_Img:Inicializado:{self.count}'))
        #self.get_logger().info('Nodo de reconocimiento de imagen inicializado')


    def listener_callback(self, msg):
        image_file = msg.data
        self.count += 1
        self.publisher_3.publish(sr.state_updated(f'Reconocimiento_Img:Trabajando:{self.count}'))
        #self.get_logger().info(f'¡Recibí: {image_file}!')
        self.recognize_image(image_file)

        self.publish_dectetion()

        self.publisher_3.publish(sr.state_updated(f'Reconocimiento_Img:Espera:{self.count}'))

    def on_shutdown_callback(self, msg):
        self.publisher_3.publish(sr.state_updated(f'Reconocimiento_Img:Cerrado:{self.count}'))
        rclpy.shutdown()

    def recognize_image(self, image_file):

        try:

            with open(image_file, "rb") as img:
                encoded_image = base64.b64encode(img.read()).decode("utf-8")            
            
            prompt_llm = self.prompt_template
           
            prompt = [ 
                HumanMessage(
                content=[
                {   "type": "text",
                    "text": prompt_llm, 
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f'data:image/jpeg;base64,{encoded_image}'}
                },
                    ]
                )
            ]
            response = self.llm.invoke(prompt)
            
            self.response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())

           
        except FileNotFoundError:
            self.response_json = {"emocion":"neutral", "posicion":"centro"}

    def publish_dectetion(self):
        msg = String()
        msg2 = String()
        #time.sleep(2)
        msg.data = self.response_json["emocion"]            
        self.publisher_.publish(msg)
        msg2.data = self.response_json["posicion"]
        self.publisher_2.publish(msg2)

    def validation_of_operation(self):
        time.sleep(2)
        self.count += 1
        self.publisher_3.publish(sr.state_updated(f'Reconocimiento_Img:Validando:{self.count}'))
        
        llm2, prompt_evaluator = sr.configuration('GOOGLE_API_KEY3', 'prompt_evaluador', 'gemini-2.5-flash')
        
        image_number = 1

        info = sr.configuration_json('info')
        description = info['node'][4]['descripcion']
       
        rules_text = info['rules'][0]['descripcion']

        objective = f'Dame {sr.num_shots} pruebas unitarias del componente reconocimiento_img con todas las propiedades: name, entrada, salida, score'

        data = sr.extract_kg_data('GOOGLE_API_KEY2', 'prompt_test', rules_text, objective)

        data_json = json.loads(data.replace("```json", "").replace("```", "").strip())

        few_shots = json.dumps(data_json, ensure_ascii=False, indent=8)
        print(few_shots)

        score = 0
        for i in range(sr.num_shots): 
            image_number = i + 1
            image_file = f'lasdai_ula/images/test/{image_number}.jpg'
            #self.get_logger().info(f'{image_file}')
            
            self.recognize_image(image_file)
            #self.get_logger().info(f'Publicado emocion: {self.response_json["emocion"]}, posición {self.response_json["posicion"]}')

            _case_to_evaluated = {
                "entrada": f'{image_number}.jpg',
                "salida": f'{self.response_json["emocion"]}, {self.response_json["posicion"]}'
            }
            case_to_evaluated = json.dumps(_case_to_evaluated, ensure_ascii=False, indent=8) 
            #self.get_logger().info(f'{case_to_evaluated}')

            one_shot = json.dumps(data_json[i], ensure_ascii=False, indent=8)
            
            prompt_llm  = prompt_evaluator.format(description=description, few_shots=one_shot, case_to_evaluated=case_to_evaluated)
            
            response = llm2.invoke(
                prompt_llm, 
                response_model=String
            )
            response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())
            self.get_logger().info(f'resultado: {response_json["score"]}, {response_json["explicacion"]}')
            score += int(response_json["score"])        
        
        score = score / sr.num_shots
        self.get_logger().info(f'Score final: {score}, porcentaje {(score/3)*100}%')
        self.publisher_3.publish(sr.state_updated(f'Reconocimiento_Img:Cerrado:{self.count}'))
        time.sleep(2)
        self.destroy_node()

    def execution(self):
        self.subscription = self.create_subscription(
            String,
            'imagen',
            self.listener_callback,
        10)
        
        self.subscription_2 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
        10) 

        self.publisher_ = self.create_publisher(String, 'emocion', 10)
        self.publisher_2 = self.create_publisher(String, 'posicion', 10)
        
def main(args=None):
    rclpy.init(args=args)
    executor = SingleThreadedExecutor()
    node = Recognition(node_name = 'Recognition_')
    node_img = Recognition_Img(node_name = 'Recognition_img')
    
    if sr.validate_operation:
        node_img.validation_of_operation()
    else:
        node_img.execution()
    
    executor.add_node(node)
    executor.add_node(node_img)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        if node.handle:
            node.p.terminate()
            node.destroy_node()
        if node_img.handle:    
            node_img.destroy_node()     
        if rclpy.ok():
            executor.shutdown()

if __name__ == '__main__':
    main()
