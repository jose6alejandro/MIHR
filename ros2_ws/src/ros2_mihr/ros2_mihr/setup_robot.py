from lasdai_ula.modulo import pr1_ula as pr1
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
import json

from std_msgs.msg import String

robot_id = None  
robot_conectado = False  


# Modo validación y cantidad de pruebas
validate_operation = False
num_shots = 3

pr1.load_dotenv()

def get_objective():
    objective_file_path = 'lasdai_ula/rules/objetivo.txt'

    try:
        with open(objective_file_path, 'r', encoding='utf-8') as file:
            objective_data  = file.read()
        #print("cargado exitosamente.")
    except FileNotFoundError:
        print(f"Error: El archivo '{objective_file_path}' no fue encontrado.")
        objective_data = None 

    return objective_data


def get_ontology():
    ontology_file_path = 'lasdai_ula/rules/ontologia.txt'
    
    try:
        with open(ontology_file_path, 'r', encoding='utf-8') as file:
            ontology_data  = file.read()
        #print("cargado exitosamente.")
    except FileNotFoundError:
        print(f"Error: El archivo '{ontology_file_path}' no fue encontrado.")
        ontology_data = None 

    return ontology_data

def configuration(api_key, path_prompt, version = 'gemini-2.5-flash', temp = 1.0):
   
    llm = ChatGoogleGenerativeAI(model=version, api_key=pr1.os.getenv(api_key),temperature=temp)
    prompt_file_path = f'lasdai_ula/prompts/{path_prompt}.txt'
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as file:
            prompt_template = file.read()
        #print("cargado exitosamente.")
    except FileNotFoundError:
        print(f"Error: El archivo '{prompt_file_path}' no fue encontrado.")
        prompt_template = None 
    return llm, prompt_template

def configuration_json(path_rule):
    rules_data = {}
    try:
        with open(f'lasdai_ula/rules/{path_rule}.json', 'r', encoding='utf-8') as file:
            rules_data = json.load(file)
    except FileNotFoundError:
                print(f"Error: El archivo '{path_rule}.json' no se encontró.")
    return rules_data

def update_json(path_rule, data):
    try:
        with open(f'lasdai_ula/rules/{path_rule}.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error al actualizar el archivo '{path_rule}.json': {e}")

def get_history(path_file):
    path_file_history = f'lasdai_ula/registro/{path_file}.txt'
    data = " "
    try:
        with open(path_file_history, 'r', encoding='utf-8') as file:
            data  = file.read()
        #print("cargado exitosamente.")
    except FileNotFoundError:
        print(f"Error: El archivo '{path_file_history}' no fue encontrado.")
        data = None 

    return data

def state_updated(pub):
    msg = String()
    msg.data = pub
    return msg

def extract_kg_data(api_key, prompt_name, rules_text, objective, format_output="entidades y todas sus propiedades"):

    graph = Neo4jGraph(
        url=pr1.os.getenv("NEO4J_URI"),
        username=pr1.os.getenv("NEO4J_USERNAME"),
        password=pr1.os.getenv("NEO4J_PASSWORD")
    )
    llm_kg, prompt_template = configuration(api_key, prompt_name, 'gemini-2.5-flash')
    
    cypher_generation_prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["schema", "question", "rules"], 
    
    )

    cypher_chain = GraphCypherQAChain.from_llm(
        llm_kg,
        graph=graph,
        cypher_prompt=cypher_generation_prompt,
        verbose=True,
        allow_dangerous_requests=True, 
        top_k=25
    )

    query_text = f''' 
        {objective}

        El formato de salida debe ser extrictamente un JSON ({format_output})
    '''

    result = cypher_chain.invoke({
        "query": query_text,
        "rules": rules_text
    })

    return result['result'] 

class RobotBase:
    def __init__(self):
        global robot_id, robot_conectado
        if not robot_conectado:
            try:
                robot_id = pr1.ula.conectarRobot(pr1.ROBOT.encode('utf-8'))
                print(f'Conectado al robot con ID: {robot_id}')
                robot_conectado = True
            except Exception as e:
                print(f"Error al conectar al robot: {e}")
        else:
            print(f"Ya existe una conexión al robot con ID: {robot_id}")
        self.id = robot_id 

    def get_robot_id(self):
        return self.id

    def disconnect(self):
        global robot_conectado
        if self.id is not None and robot_conectado:
            pr1.ula.desconectarRobot(self.id)
            print(f'Desconectado del robot con ID: {self.id}')
            robot_conectado = False
            robot_id = None
        else:
            print("No hay robot conectado")

import platform

if platform.machine() == "aarch64":
    # --- CONFIGURACIONES PARA EL LED RGB ---
    import RPi.GPIO as GPIO

    COLOR = {"RED": 0xFF0000, "GREEN": 0x00FF00, "YELLOW": 0xFFFF00} 
    INTENSITY_PERCENT = 100  # Intensidad deseada

    # Pines GPIO (BCM) conectados a los canales R, G, B del LED
    PINS = {'Red': 22, 'Green': 27, 'Blue': 17} 

    # Variables para los objetos PWM
    R_PWM = None 
    G_PWM = None
    B_PWM = None

    # Frecuencia para el PWM
    FREQUENCY = 2000

    def mapea(x, in_min, in_max, out_min, out_max):
        """Mapea Mapea un valor (0-255) a un ciclo de trabajo (0-100)"""
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def set_color(color, intensity_percent):
        """Asigna el color y ajusta el ciclo de trabajo con la intensidad deseada."""
        global R_PWM, G_PWM, B_PWM 

        # 1. Calcula el valor para cada canal R, G, B (0~255)
        R_val = (color & 0xFF0000) >> 16
        G_val = (color & 0x00FF00) >> 8
        B_val = (color & 0x0000FF) >> 0

        # 2. Convierte el valor de 0~255 a un ciclo de trabajo (Duty Cycle) de 0~100
        R_duty = mapea(R_val, 0, 255, 0, 100)
        G_duty = mapea(G_val, 0, 255, 0, 100)
        B_duty = mapea(B_val, 0, 255, 0, 100)
        
        # 3. Aplica la intensidad de porcentaje
        R_final_duty = R_duty * (intensity_percent / 100.0)
        G_final_duty = G_duty * (intensity_percent / 100.0)
        B_final_duty = B_duty * (intensity_percent / 100.0)
        
        # Asegúrate de que no exceda 100 o sea menor que 0
        R_final_duty = max(0, min(100, R_final_duty))
        G_final_duty = max(0, min(100, G_final_duty))
        B_final_duty = max(0, min(100, B_final_duty))
        
        # 4. Asigna el nuevo ciclo de trabajo a los objetos PWM
        R_PWM.ChangeDutyCycle(R_final_duty)
        G_PWM.ChangeDutyCycle(G_final_duty)
        B_PWM.ChangeDutyCycle(B_final_duty)

        #print(f"Intensidad: {intensity_percent}%")

    def reset():
        """Apaga los LEDs poniendo el ciclo de trabajo a 0%."""
        global R_PWM, G_PWM, B_PWM
        if R_PWM: R_PWM.ChangeDutyCycle(0)
        if G_PWM: G_PWM.ChangeDutyCycle(0)
        if B_PWM: B_PWM.ChangeDutyCycle(0)

