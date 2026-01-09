# MIHR
Evaluación del Modelo de Interacción Humano-Robot (MIHR) mediante el desarrollo 
de dos casos de estudio: aprendizaje de las matemáticas y manejo del estrés.

![interacción estudiante y robot](/ros2_ws/src/ros2_mihr/ros2_mihr/lasdai_ula/images/figura.png)

## Requerimientos
- Para este proyecto se utilizó ROS2 en la versión humble compatible con ubuntu 22.04, los pasos de descarga estan en el enlace: https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html

- Se quiere Python >= 3.10 y los siguientes paquetes:
    - gtts 
    - vosk 
    - PyAudio 
    - pygame
    - pyrubberband
    - langchain
    - langchain_google_genai
    - langchain_neo4j
    - python-dotenv
    - opencv-python
    - RPi.GPIO (para raspberry)
    - pandas y pingouin (para ejecutar el analisis ANOVA) 
- Este proyecto usa la API de gemini: 
    - Crea un archivo .env en el directorio ```MIHR/ros2_ws/src/ros2_mihr/ros2_mihr``` y agregue la linea ```GOOGLE_API_KEY = "aquí su key"```
- Este proyecto usa Aura DB de Neo4j para acceder al grafo de conocimiento solicite el acceso (castroj@ula.ve)
## Compilación y ejecución
- El archivo **run.sh** tiene varias opciones para ejecutar y las principales a usar son:
    - ```./run.sh 1```: habilita y configura el entorno de ROS, y habilita el puerto para el robot LRS2
    - ```./run.sh <nodo>```: ejecute un nodo especifico añadiendo el nombre como párametro 
    - ```./run.sh ```: ejecute varios nodos en una misma terminal, los nodos disponibles están en el archivo launch.py  

## Enlaces importantes 
- Documento - proyecto de grado (proximamente)
- [Modelo de Interacción Humano-Robot (MIHR)](https://ieeexplore.ieee.org/document/9381793)
- [Prompts](ros2_ws/src/ros2_mihr/ros2_mihr/lasdai_ula/prompts)
- [Historial de conversaciones](ros2_ws/src/ros2_mihr/ros2_mihr/lasdai_ula/registro)
- Ejemplo de una interacción (proximamente)
