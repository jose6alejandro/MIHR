import time
import rclpy
import json
from rclpy.node import Node
from std_msgs.msg import String
from lasdai_ula.modulo import pr1_ula as pr1
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import textwrap
from neo4j import GraphDatabase
import setup_robot as sr

BOLD = '\33[1m'
END = '\33[0m'
WIDTH = 80
SEPARATOR = '-' * WIDTH

class Spur(Node):
    def __init__(self):
        super().__init__('SPUR')
        #print(textwrap.fill('Nodo SPUR inicializado.', width=50))

    def execute(self):
        while True:
            os.system('clear')

            SEPARATOR = '-' * WIDTH

            print(SEPARATOR)
            print(f"{BOLD} {'EVALUACIÓN SPUR':^{WIDTH}} {END}")
            print(SEPARATOR)
            print(f"1) Preproceso: (extraer patrones y generar rúbricas)")
            print(f"2) Evaluación de satisfacción: (obtener resultado y actualizar grafo)")
            print(f"3) Salir")
            print(SEPARATOR)

            choice = input(f"{BOLD}Seleccione una opción:{END} ")

            if choice == '1':
                self.generate_rubrics()
            elif choice == '2':
                self.evaluate_satisfaction()
            elif choice == '3':
                print(textwrap.fill("Finalizado", width=WIDTH))
                break
            else:
                print(textwrap.fill("Opción no válida. Por favor, intente de nuevo.", width=WIDTH))
                time.sleep(2)

    def extract_patterns(self):
        os.system('clear')
        print(SEPARATOR)
        print(f"{BOLD} {'Extraer pátrones de conversaciones':^{WIDTH}} {END}")
        print(SEPARATOR)
        print("1) Aprendizaje de matemáticas")
        print("2) Manejo del estrés")
        print("3) Regresar")
        print(SEPARATOR)
        choice = input(f"{BOLD}Seleccione una opción:{END} ")

        n_files = 10  #número de archivos a procesar       
        llm, prompt_template = sr.configuration('GOOGLE_API_KEY', 'prompt_patrones', 'gemini-2.5-pro')
        patterns = {}
        context = ""
        if choice == '1':
            print("\nSAT:")
            patterns['satisfaccion'] = self.get_batch_patterns(llm, prompt_template, "matemáticas/sat", n_files)
            print("\nDSAT:")
            patterns['insatisfaccion'] = self.get_batch_patterns(llm, prompt_template, "matemáticas/dsat", n_files)
            #patterns = json.dumps(patterns, ensure_ascii=False, indent=4)
            context = "aprendizaje de matematicas"
        elif choice == '2':
            print("\nSAT:")
            patterns['satisfaccion'] = self.get_batch_patterns(llm, prompt_template, "estrés/sat", n_files)
            print("\nDSAT:")
            patterns['insatisfaccion'] = self.get_batch_patterns(llm, prompt_template, "estrés/dsat", n_files)
            context = "manejo del estres"
        elif choice == '3':
            return patterns, context
        else:
            print(textwrap.fill("Opción no válida. Por favor, intente de nuevo.", width=WIDTH))
            time.sleep(2)

        return patterns, context
   
    def get_batch_patterns(self, llm, prompt_template, path_file_s, n_files):
            
        i = 1
        batch = {}
        while i <= n_files:

            path_file = sr.get_history(f"simulaciones/{path_file_s}/test{i}")
            print(textwrap.fill(f"\nProcesando... ({i}/{n_files})\n\n", width=WIDTH))
            prompt_llm  = prompt_template.replace("{conversation}", path_file)
            response = llm.invoke(prompt_llm)
            json_patterns = json.loads(response.content.replace("```json", "").replace("```", ""))
            #str_i = str(i)
            batch[f'patrones_{i}'] = json_patterns['patrones']

            i+= 1
        
        print(textwrap.fill(f"\nListo... ({i-1}/{n_files})\n\n", width=WIDTH))
        time.sleep(2)
        return batch

    def generate_rubrics(self):
        print(textwrap.fill("Aquí se generan las rúbricas.", width=WIDTH))
        final_batch, context = self.extract_patterns()
        
        if context == "": return
        
        final_batch_sat = json.dumps(final_batch['satisfaccion'], ensure_ascii=False, indent=4)
        final_batch_dsat = json.dumps(final_batch['insatisfaccion'], ensure_ascii=False, indent=4)

        while True:
            os.system('clear')
            print(SEPARATOR)
            print(f"{BOLD} {'Generar Rúbricas':^{WIDTH}} {END}")
            print(SEPARATOR)
            print("1) Ver patrones SAT")
            print("2) Ver patrones DSAT")
            print("3) Obtener rúbricas")
            print("4) Regresar")
            print(SEPARATOR)
            choice = input(f"{BOLD}Seleccione una opción:{END} ")

            if choice == '1':
                print(f"\n\n{final_batch_sat}\n")
                input("Presione Enter para continuar...")
            elif choice == '2':
                print(f"\n\n{final_batch_dsat}\n")
                input("Presione Enter para continuar...")    
            elif choice == '3':
                print(f"\nProcesando...\n\n")
                llm, prompt_template = sr.configuration('GOOGLE_API_KEY', 'prompt_rubrica', 'gemini-2.5-pro')
                prompt_llm  = prompt_template.replace("{patterns}", json.dumps(final_batch, ensure_ascii=False, indent=4))
                response = llm.invoke(prompt_llm)
                json_rubrics = json.loads(response.content.replace("```json", "").replace("```", ""))
                #rubrics_output = json.dumps(json_rubrics, ensure_ascii=False, indent=4)
                #print(f"{rubrics_output}")

                rubric = sr.configuration_json('rubrica')
                rubric[context] = json_rubrics['rubrica']
                sr.update_json('rubrica', rubric)

                input("Listo. Presione Enter para regresar el manú principal...")
                break
            elif choice == '4':
                break
            else:
                print(textwrap.fill("Opción no válida. Por favor, intente de nuevo.", width=WIDTH))
                time.sleep(2)


    def evaluate_satisfaction(self):

        rubric = ""

        while True:
            os.system('clear')
            print(SEPARATOR)
            print(f"{BOLD} {'Cargar Rúbrica':^{WIDTH}} {END}")
            print(SEPARATOR)
            print("1) Aprendizaje de matemáticas")
            print("2) Manejo del estrés")
            print(SEPARATOR)
            choice = input(f"{BOLD}Seleccione una opción:{END} ")

            if choice == '1':
                _rubric = sr.configuration_json('rubrica')
                rubric = json.dumps(_rubric['aprendizaje de matematicas'], ensure_ascii=False, indent=4)
                break
            elif choice == '2':
                _rubric = sr.configuration_json('rubrica')
                rubric = json.dumps(_rubric['manejo del estres'], ensure_ascii=False, indent=4)
                break
            else:
                print(textwrap.fill("Opción no válida. Por favor, intente de nuevo.", width=WIDTH))
                time.sleep(2)

        history = None
        while True:
            os.system('clear')
            print(SEPARATOR)
            print(f"{BOLD} {'Cargar Registro':^{WIDTH}} {END}")
            print(SEPARATOR)
            print(f"{BOLD}Registros de interacción más recientes:{END}\n")

            try:
                files = os.listdir('lasdai_ula/registro/')
                files = [f for f in files if f.endswith('.txt')]
                files.sort(key=lambda x: os.path.getmtime(os.path.join('lasdai_ula/registro/', x)), reverse=True)
                recent_files = files[:5]
                for f in recent_files:
                    print(f" - {f[:-4]}")
            except FileNotFoundError:
                print(textwrap.fill("ERROR: El directorio 'lasdai_ula/registro/' no fue encontrado.", width=WIDTH))

            print(SEPARATOR)
            path_file = input(f"{BOLD}Introduzca el registro:{END} ")
            history = sr.get_history(path_file)

            if history is not None:
                input("\nListo. Presione Enter para realizar la evaluación...")
                break
            else:
                print(textwrap.fill("Archivo no encontrado. Por favor, intente de nuevo.", width=WIDTH))
                time.sleep(2)

        llm, prompt_template = sr.configuration('GOOGLE_API_KEY', 'prompt_sat', 'gemini-2.5-pro')
        prompt_llm  = prompt_template.replace("{rubric}", rubric).replace("{conversation}", history)
        response = llm.invoke(prompt_llm)
        response_json = json.loads(response.content.replace("```json", "").replace("```", "").strip())
        result = json.dumps(response_json["SPUR_feedback"], ensure_ascii=False, indent=4)

        while True:
            os.system('clear')
            print(SEPARATOR)
            print(f"{BOLD} {'Actualizar Grafo de Conocimiento':^{WIDTH}} {END}")
            print(SEPARATOR)
            print(f"{BOLD}Resultado de la evaluación:{END}")
            for line in result.splitlines():
                print(textwrap.fill(line, width=WIDTH))
            print(SEPARATOR)

            question = f" {BOLD}¿Desea actualizar el grafo con este resultado? {END}"
            for line in textwrap.wrap(question, width=WIDTH):
                print(line)

            print("1) Si")
            print("2) No")
            print(SEPARATOR)
            choice = input(f"{BOLD}Seleccione una opción:{END} ")

            if choice == '1':
                self.update_graph(result)
                input("\n¡Grafo actualizado! Presione Enter para volver al menú principal...")
                break
            elif choice == '2':
                print(textwrap.fill("Actualización del grafo cancelada.", width=WIDTH))
                time.sleep(2)
                break
            else:
                print(textwrap.fill("Opción no válida. Por favor, intente de nuevo.", width=WIDTH))
                time.sleep(2)



    def update_graph(self, result):
        print(textwrap.fill("Generando instrucciones Cypher\n", width=WIDTH))
        ontology = sr.get_ontology()
        #print(ontology)
        llm, prompt_template = sr.configuration('GOOGLE_API_KEY', 'prompt_grafo', 'gemini-2.5-pro')
        prompt_llm  = prompt_template.replace("{ontology}", ontology).replace("{result}", result)
        #sprint(textwrap.fill(f"{prompt_llm}", width=WIDTH))
        response = llm.invoke(prompt_llm)
        cypher_query  = response.content.replace("```cypher", "").replace("```", "")
        print(textwrap.fill(f"{cypher_query}", width=WIDTH))

        input("\nPresione Enter para confirmar...")
        try:
            with GraphDatabase.driver(pr1.os.getenv("NEO4J_URI"), auth=(pr1.os.getenv("NEO4J_USERNAME"), pr1.os.getenv("NEO4J_PASSWORD"))) as driver:
                with driver.session() as session:
                    session.run(cypher_query)

        except Exception as e:
            print(f"Error al conectar o ejecutar Cypher: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = Spur()
        node.execute()
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()