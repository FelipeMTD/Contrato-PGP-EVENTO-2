import os
import sys
from dotenv import load_dotenv

# --- ESTRATEGIA DE RUTAS PARA EL .EXE ---
if getattr(sys, 'frozen', False):
    directorio_base = os.path.dirname(sys.executable) # Ruta si es .exe
else:
    directorio_base = os.path.dirname(os.path.abspath(__file__)) # Ruta si es .py

# Forzamos a que lea el .env exactamente en la carpeta del ejecutable
ruta_env = os.path.join(directorio_base, '.env')
load_dotenv(dotenv_path=ruta_env)
# ----------------------------------------

class Config:
    URL = os.getenv("EPS_URL")
    USER_TYPE = os.getenv("EPS_USER_TYPE")
    USER_ID = os.getenv("EPS_USER_ID")
    PASSWORD = os.getenv("EPS_USER_PASS")
    HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"
    SLOW_MO = int(os.getenv("SLOW_MO", 0))