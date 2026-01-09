import io
import os
import ctypes
import tempfile
import pyaudio
import wave
import audioop
import time
import json
import platform


from dotenv import load_dotenv
from vosk import Model, KaldiRecognizer, SetLogLevel

import numpy as np
import soundfile as sf
import pyrubberband as pyrb
import io
from gtts import gTTS

# Permiso para el puerto del robot
RUTA_PUERTO = "/dev"

# Modelo de reconocimiento de voz
MODEL = "vosk-model-small-es-0.42"

# Parámetros de grabación
CHUNK = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
SILENCE_THRESHOLD = 1000
MAX_SILENCE_SECONDS = 2

# Configuraciones del robot
ROBOT = "LRS2"

# Parámetros para la voz del robot
PITCH = -1
SPEED = 1  
VOLUME = 1

# Acciones del robot
comando = {
    "expresarNormal": 4, 
    "cerrarOjos": 59, 
    "abrirOjos": 64,
    "cerrarIzquierdo": 5, 
    "abrirIzquierdo": 6, 
    "cerrarDerecho": 7,
    "abrirDerecho": 8, 
    "comenzarHabla": 9, 
    "terminarHabla": 44,
    "moverIzquierda": 45, 
    "moverCentro": 46, 
    "moverDerecha": 47,
    "moverArriba": 48, 
    "mover_cuelloCe": 49, 
    "moverAbajo": 54,
    "expresarFeliz": 55, 
    "expresarTriste": 56, 
    "habilitarEntradas": 57,
    "deshabilitarEntradas": 58, 
    "apagarBoca": 65
}

arq = "64bits" if platform.machine() == "x86_64" else "Raspberry"
path = f'./lasdai_ula/modulo/{arq}/pr1-ula.so'
ula = ctypes.CDLL(path) if os.path.exists(path) else None

# import pygame
# def inicializar_audio():
#   pygame.mixer.init()

# def respuestaRobot(id, texto):
#     try: 
#       tts = gTTS(text=texto, lang='es', tld='co.ve')    

#       mp3_buffer = io.BytesIO()
#       tts.write_to_fp(mp3_buffer)
#       mp3_buffer.seek(0)

#       audio_data, sr = sf.read(mp3_buffer, dtype='float32')

#       pitched_audio = pyrb.pitch_shift(audio_data, sr, n_steps=PITCH)
#       speed_audio = pyrb.time_stretch(pitched_audio, sr, rate=SPEED)
#       volume_audio = speed_audio * VOLUME
#       modified_audio = np.clip(volume_audio, -1.0, 1.0)
      
#       mp3_buffer = io.BytesIO()
#       sf.write(mp3_buffer, modified_audio, sr, format='MP3')
#       mp3_buffer.seek(0)   
      

#       sonido = pygame.mixer.Sound(mp3_buffer)
     
#       ula.enviarRobot(id, comando["comenzarHabla"])

#       sonido.play()
#       while pygame.mixer.get_busy():
#           pygame.time.Clock().tick(10)

#     except KeyboardInterrupt:
#       pass
#     finally:
#       ula.enviarRobot(id, comando["terminarHabla"])

# def cerrar_audio():
#   pygame.mixer.quit()