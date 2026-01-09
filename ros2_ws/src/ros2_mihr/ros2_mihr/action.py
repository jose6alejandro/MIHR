import time
import random   
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from lasdai_ula.modulo import pr1_ula as pr1

import setup_robot as sr 
from setup_robot import RobotBase
from rclpy.executors import SingleThreadedExecutor

import numpy as np
import soundfile as sf
import pyrubberband as pyrb
import pygame
import io
import re
import concurrent.futures
from gtts import gTTS

import RPi.GPIO as GPIO

PATH = 'lasdai_ula/sonidos' 

robot = RobotBase()
id = robot.get_robot_id()
pygame.mixer.init(frequency=24000, buffer=1024)

class Action(Node):
    def __init__(self, node_name ='action_default'):
        super().__init__(node_name)
        
        self.subscription = self.create_subscription(
            String,
            'respuesta_verbal',
            self.response_callback,
            10)
        
        self.subscription_2 = self.create_subscription(
            String,
            'voz_robot',
            self.voice_callback,
        10)    
        
        self.subscription_3 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
        10) 

        self.subscription_4 = self.create_subscription(
            String,
            'led',
            self.led_callback,
        10) 
        self.delay = True
        self.declare_led()
        self.pitch = pr1.PITCH
        self.speed = pr1.SPEED
        self.volume = pr1.VOLUME
        self.publisher_ = self.create_publisher(String, 'respuesta_robot', 10)
        self.publisher_2 = self.create_publisher(String, 'monitoreo', 10)
        time.sleep(2)
        self.count = 0
        self.publisher_2.publish(sr.state_updated(f'Actuador:Inicializado:{self.count}'))   

        sr.reset()
        sr.set_color(sr.COLOR["YELLOW"], sr.INTENSITY_PERCENT)                
        #self.speak_robot(id, "¡Me estoy configurando, esto puede tardar un momento!")     

    def declare_led(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for pin in sr.PINS.values():
            GPIO.setup(pin, GPIO.OUT)
        
        sr.R_PWM = GPIO.PWM(sr.PINS['Red'], sr.FREQUENCY)
        sr.G_PWM = GPIO.PWM(sr.PINS['Green'], sr.FREQUENCY)
        sr.B_PWM = GPIO.PWM(sr.PINS['Blue'], sr.FREQUENCY)
        
        sr.R_PWM.start(0)
        sr.G_PWM.start(0)
        sr.B_PWM.start(0)

    def cleanup(self):
        if sr.R_PWM: sr.R_PWM.stop()
        if sr.G_PWM: sr.G_PWM.stop()
        if sr.B_PWM: sr.B_PWM.stop()
        GPIO.cleanup()

    def led_callback(self, msg):
        sr.reset()
        if msg.data == 'yellow':
            sr.set_color(sr.COLOR["YELLOW"], sr.INTENSITY_PERCENT)
        else:
            sr.set_color(sr.COLOR["GREEN"], sr.INTENSITY_PERCENT) 

    def split_text_into_chunks(self, text: str) -> list[str]:
        
        text = re.sub(r'\n+', ' ', text).strip()
        sentences = re.split(r'(?<!\d)([.!])\s*', text)

        chunks = []

        temp_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if sentences[i].strip():
                temp_sentences.append((sentences[i] + sentences[i+1]).strip())
        
        if len(sentences) % 2 != 0 and sentences[-1].strip():
            temp_sentences.append(sentences[-1].strip())
        
        current_chunk = ""
        for sentence in temp_sentences:
            if len(current_chunk) + len(sentence) < 60: # Limite de caracteres
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def process_audio_chunk(self, chunk_text):

        try:
            tts = gTTS(text=chunk_text, lang='es', tld='com')
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)

            audio_data, srade = sf.read(mp3_buffer, dtype='float32')

            if audio_data.ndim > 1:
                audio_data = audio_data[:, 0]

            if self.pitch != 0 or self.speed != 1:
                pitched_audio = pyrb.pitch_shift(audio_data, srade, n_steps=self.pitch)
                if self.speed != 1:
                    pitched_audio = pyrb.time_stretch(pitched_audio, srade, rate=self.speed)
                final_audio = pitched_audio
            else:
                final_audio = audio_data

            final_audio = final_audio * self.volume
            final_audio = np.clip(final_audio, -1.0, 1.0)

            output_buffer = io.BytesIO()
            sf.write(output_buffer, final_audio, srade, format='WAV')
            output_buffer.seek(0)
            
            return output_buffer

        except Exception as e:
            #print(f"Error procesando chunk '{chunk_text[:20]}...': {e}")
            return None

    def speak_robot(self, id, texto):
        text_chunks = self.split_text_into_chunks(texto)
        
        if not text_chunks:
            return

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_chunk = {executor.submit(self.process_audio_chunk, chunk): chunk for chunk in text_chunks}
            
            futures_list = list(future_to_chunk.keys())
            
            for i, future in enumerate(futures_list):

                audio_buffer = future.result()
                
                if audio_buffer:
                    try:
                        pr1.ula.enviarRobot(id, pr1.comando["comenzarHabla"])
                        sr.reset()
                        sr.set_color(sr.COLOR["RED"], sr.INTENSITY_PERCENT)                         
                        sound = pygame.mixer.Sound(audio_buffer)
                        sound.play()
                        
                        while pygame.mixer.get_busy():
                            pygame.time.Clock().tick(10)

                        pr1.ula.enviarRobot(id, pr1.comando["terminarHabla"])
                        time.sleep(1)

                    except pygame.error as e:
                        #print(f"Error de Pygame al reproducir el chunk: {e}")
                        break
                    except KeyboardInterrupt:
                        pr1.ula.enviarRobot(id, pr1.comando["terminarHabla"])

    def response_callback(self, msg):
        self.count += 1
        self.publisher_2.publish(sr.state_updated(f'Actuador:Trabajando:{self.count}'))
        self.response_data =  msg.data
                
        self.speak_robot(id, f"{self.response_data}")

        msg = String()
        msg.data = '¡Listo!'
        self.publisher_.publish(msg)
        self.publisher_2.publish(sr.state_updated(f'Actuador:Espera:{self.count}'))
      
        #self.get_logger().info(f'Ejecutando respuesta del robot')

    def on_shutdown_callback(self, msg):
        self.publisher_2.publish(sr.state_updated(f'Actuador:Cerrado:{self.count}'))
        self.cleanup()
        pygame.mixer.quit()
        self.destroy_node()

    def voice_callback(self, msg):       
        self.voice_data = msg.data
        self.pitch, self.speed, self.volume =  self.voice_data.split(':')
        
        self.pitch = float(self.pitch)
        self.speed = float(self.speed)
        self.volume = float(self.volume)
        #self.get_logger().info(f'acabo de recibir pitch: {self.pitch} y este es el valor actual {pr1.PITCH}')


class Action_Mov(Node):
    def __init__(self, node_name ='action_default'):
        super().__init__(node_name)
        
        
        self.subscription_ = self.create_subscription(
            String,
            'emocion_robot',
            self.emotion_callback,
            10
        )

        self.subscription_2 = self.create_subscription(
            String,
            'posicion_robot',
            self.position_callback,
            10
        )

        self.subscription_3 = self.create_subscription(
            String,
            'aviso', #para ejecutar el reconocer la respuesta del usuario
            self.response_robot_callback,
            10
        )

        self.subscription_4 = self.create_subscription(
            String,
            'cerrar_nodo',
            self.on_shutdown_callback,
        10) 

        self.message_store = {}
        self.pos_flag = 0 #  si es 1 esta el no_verbal actua
        self.emo_flag = 0 #  0 neutral, 1 feliz, 2 triste
        self.aux = 'centro' 
        self.select_mov = 0
        self.last_sync_time = self.get_clock().now()
        self.timer = self.create_timer(0.5, self.sync_callback)
        
        self.publisher_ = self.create_publisher(String, 'monitoreo', 10)
        
        time.sleep(2)
        self.count = 0
        self.publisher_.publish(sr.state_updated(f'Actuador_Mov:Inicializado:{self.count}'))
        pr1.ula.enviarRobot(id, pr1.comando["abrirOjos"])
        pr1.ula.enviarRobot(id, pr1.comando["expresarNormal"])
        pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"])           
        #self.get_logger().info('Nodo action_mov inicializado')    
    
    def emotion_callback(self, msg):
        self.emotion_data = msg.data.split(":")
        if self.emotion_data[0] == 'Affective':
            self.message_store['affective'] = self.emotion_data[1]
        else:
            self.message_store['automatic'] = self.emotion_data[1]

    def position_callback(self, msg):
        self.position_data = msg.data.split(":")
        if self.position_data[0]  == 'pos_No_verbal':
            self.message_store['pos_no_verbal'] = self.position_data[1]
        elif self.position_data[0]  == 'pos2_No_verbal':
            self.message_store['pos2_no_verbal'] = self.position_data[1]
        else:
            self.message_store['pos_automatic'] = self.position_data[1]
    
    def response_robot_callback(self, msg):
        self.message_store['flag'] = msg.data           
    
    def on_shutdown_callback(self, msg):
        time.sleep(3)
        self.publisher_.publish(sr.state_updated(f'Actuador_Mov:Cerrado:{self.count}'))
        pygame.mixer.init()
        pr1.ula.enviarRobot(id, pr1.comando["apagarBoca"])
        pr1.ula.enviarRobot(id, pr1.comando["cerrarOjos"])
        pygame.mixer.Sound(f'{PATH}/apagar.mp3').play()
        time.sleep(1)
        pygame.mixer.quit()
        self.destroy_node()
    
    def sync_callback(self):
        
        emotion = ' '
        position = ' '

        #self.get_logger().info(f'{self.message_store}')
        if ('automatic' in self.message_store and 'pos_automatic' in self.message_store and 'flag' in self.message_store) or 'emotion' in self.message_store and 'position' in self.message_store:
            emotion = self.message_store.pop('automatic')
            position = self.message_store.pop('pos_automatic')
            self.message_store.pop('flag')
            self.pos_flag = 1

            self.select_mov = 0
            
            if self.aux == position:                   
                self.select_mov = random.randint(1, 8) 
           
           # if self.aux == 'derecha' and position == 'izquierda' or self.aux == 'izquierda' and position == 'derecha':
           #     position = 'centro' 
           
            #self.aux = position 
            #self.get_logger().info(f'¡Recibí: {self.select_mov}, {self.aux}, {position}!') 

        if  'affective' in self.message_store and 'pos_no_verbal' in self.message_store:
            emotion = self.message_store.pop('affective')
            position = self.message_store.pop('pos_no_verbal')
            self.pos_flag = 2
        elif 'pos2_no_verbal' in self.message_store:
            position = self.message_store.pop('pos2_no_verbal')
            self.pos_flag = 2          
        #self.get_logger().info(f'¡Recibí: {self.select_mov}, {position}!')
        
        if self.pos_flag != 0:
            self.count += 1
            self.publisher_.publish(sr.state_updated(f'Actuador_Mov:Trabajando:{self.count}'))
            #self.get_logger().info(f'Ejecutando expresión {position}, {emotion}')   
            if emotion == "feliz":
                if self.emo_flag != 1:
                    pr1.ula.enviarRobot(id, pr1.comando["moverArriba"])
                    pr1.ula.enviarRobot(id, pr1.comando["expresarFeliz"])
                    #pygame.mixer.Sound(f'{PATH}/{emotion}.mp3').play()
                    time.sleep(1.5)
                    pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"]) 
                    
                self.emo_flag = 1

            elif emotion == "triste":
                if self.emo_flag != 2:
                    pr1.ula.enviarRobot(id, pr1.comando["moverAbajo"])
                    pr1.ula.enviarRobot(id, pr1.comando["expresarTriste"])
                    #pygame.mixer.Sound(f'{PATH}/{emotion}.mp3').play()
                    time.sleep(1.5)
                    pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"]) 
                    pr1.ula.enviarRobot(id, pr1.comando["expresarNormal"])
                    
                self.emo_flag = 2
            
            elif emotion == "neutral":
                if self.emo_flag != 0:
                    pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"]) 
                    pr1.ula.enviarRobot(id, pr1.comando["expresarNormal"])
                self.emo_flag = 0   
            else:
                pass
            time.sleep(1)
            #self.get_logger().info(f'Ejecutando posicion {position}, {self.select_mov}')
            if self.pos_flag  == 1:
                if position == "derecha" and self.select_mov == 0:
                    pr1.ula.enviarRobot(id, pr1.comando["moverDerecha"])
                    time.sleep(2)
                    pr1.ula.enviarRobot(id, pr1.comando["moverCentro"])                    
                elif position == "izquierda" and self.select_mov == 0:
                    pr1.ula.enviarRobot(id, pr1.comando["moverIzquierda"])
                    time.sleep(2)
                    pr1.ula.enviarRobot(id, pr1.comando["moverCentro"])                        
                elif position == "centro" and self.select_mov == 0:
                    pr1.ula.enviarRobot(id, pr1.comando["moverCentro"])
                else:
                    if self.select_mov == 1 or self.select_mov == 3 or self.select_mov == 5: 
                      pr1.ula.enviarRobot(id, pr1.comando["moverArriba"])
                      time.sleep(2)
                      pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"])
                    elif self.select_mov == 4 or self.select_mov == 6 or self.select_mov == 8: 
                      pr1.ula.enviarRobot(id, pr1.comando["moverAbajo"])
                      time.sleep(2)
                      pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"])
                    else:
                        pr1.ula.enviarRobot(id, pr1.comando["cerrarOjos"])
                        pygame.mixer.Sound(f'{PATH}/ojo.mp3').play() 
                        time.sleep(0.3)
                        pr1.ula.enviarRobot(id, pr1.comando["abrirOjos"])
            else: # nodo no verbal
               # time.sleep(1)
                if position == "mov_positivo": 
                    pr1.ula.enviarRobot(id, pr1.comando["moverArriba"])
                    pr1.ula.enviarRobot(id, pr1.comando["cerrarOjos"])
                    pygame.mixer.Sound(f'{PATH}/ojo.mp3').play()
                    time.sleep(0.5)
                    pr1.ula.enviarRobot(id, pr1.comando["abrirOjos"])
                elif position == "mov_positivo2":
                    pr1.ula.enviarRobot(id, pr1.comando["moverArriba"])  
                
                elif position == "mov_negativo":
                    pr1.ula.enviarRobot(id, pr1.comando["moverAbajo"]) 
                    time.sleep(2)
                    pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"])
                    pr1.ula.enviarRobot(id, pr1.comando["cerrarOjos"])
                    pygame.mixer.Sound(f'{PATH}/ojo.mp3').play()
                    time.sleep(0.5)
                    pr1.ula.enviarRobot(id, pr1.comando["abrirOjos"])

                elif position == "mov_negativo2": 
                    pr1.ula.enviarRobot(id, pr1.comando["moverAbajo"]) 
                    time.sleep(2)
                    pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"])
                elif position == "mov_neutral": 
                    move = random.randint(1, 6) 
                    if move == 3:
                        pr1.ula.enviarRobot(id, pr1.comando["moverIzquierda"])
                        time.sleep(2)
                        pr1.ula.enviarRobot(id, pr1.comando["moverCentro"])
                    elif move == 5:
                        pr1.ula.enviarRobot(id, pr1.comando["moverDerecha"])
                        time.sleep(2)
                        pr1.ula.enviarRobot(id, pr1.comando["moverCentro"])
                    else:
                        pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"]) 
                        pr1.ula.enviarRobot(id, pr1.comando["moverCentro"])
                    
                    pr1.ula.enviarRobot(id, pr1.comando["expresarNormal"])   

                elif position == "mov_neutral2": 
                    pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"])
                    pr1.ula.enviarRobot(id, pr1.comando["cerrarOjos"])
                    pygame.mixer.Sound(f'{PATH}/ojo.mp3').play()
                    time.sleep(0.5)
                    pr1.ula.enviarRobot(id, pr1.comando["abrirOjos"])  
                    pr1.ula.enviarRobot(id, pr1.comando["expresarNormal"])             
                elif position == "mov_verbal": 
                    pr1.ula.enviarRobot(id, pr1.comando["moverArriba"])
                    time.sleep(2)
                    pr1.ula.enviarRobot(id, pr1.comando["mover_cuelloCe"])
                    pr1.ula.enviarRobot(id, pr1.comando["expresarFeliz"])
                else:
                    pass

            #self.get_logger().info(f'Ejecutando expresión y posición')   
            self.publisher_.publish(sr.state_updated(f'Actuador_Mov:Espera:{self.count}'))
        
        self.pos_flag = 0 
                       

def main(args=None):
    rclpy.init(args=args)
    executor = SingleThreadedExecutor()
    node = Action(node_name = 'Action')
    node_mov = Action_Mov(node_name = 'Action_Mov')
    executor.add_node(node)
    executor.add_node(node_mov)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        if node.handle:
            node.cleanup()
            pygame.mixer.quit()
            node.destroy_node()
        if node_mov.handle:
            node_mov.destroy_node()            
        if rclpy.ok():
            executor.shutdown()

if __name__ == '__main__':
    main()