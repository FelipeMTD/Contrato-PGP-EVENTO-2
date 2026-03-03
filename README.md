# RPA Consulta de Afiliados - Nueva EPS

Este proyecto es un bot de **Automatización Robótica de Procesos (RPA)** diseñado para realizar consultas masivas del estado de afiliación de pacientes en el portal transaccional de la Nueva EPS.

El sistema lee un archivo Excel con los documentos de los pacientes, navega por el portal evadiendo sistemas de detección de bots (Cloudflare), extrae la información requerida interactuando con iframes dinámicos (ICEfaces), y finalmente clasifica el tipo de contrato (PGP o EVENTO) cruzando los datos con un diccionario JSON externo.

## ✨ Características Principales

* **Arquitectura POM (Page Object Model):** Código altamente modular y escalable. Cada página del portal tiene su propia clase y lógica de extracción.
* **Evasión de Defensas (Stealth):** * Simulación de tecleo humano con latencias aleatorias (`press_sequentially`).
  * Pausas dinámicas entre acciones para romper patrones algorítmicos.
  * Inyección de clics por JavaScript para evadir "loaders" invisibles.
* **Manejo de "Caminos Tristes" (Sad Paths):** Detección inteligente de pacientes que no existen en el sistema, limpiando variables y saltando al siguiente registro sin romper la ejecución.
* **Pipeline ETL Completo:** Extracción, limpieza (eliminación de caracteres corruptos de Excel como `_x000d_`), y carga de datos usando `pandas`.
* **Clasificación de Negocio:** Cruce automatizado de la "IPS Primaria" extraída con archivos `.json` locales para determinar automáticamente el "Tipo Contrato".

---

## 🛠️ Requisitos del Sistema

* **Python** 3.9 o superior.
* Navegador **Google Chrome** (o Chromium) instalado en el sistema.

### Instalación de Dependencias

1. Crea un entorno virtual (recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

## ***Cambios internos en archivos***

.**env** HEADLESS=TRUE para cerrar navegador

**main.py**

 ruta_json_boyaca = os.path.join(directorio_base, "json", "json_boyaca", "Contrato_Pgp_Boyaca.json")

  ruta_json_tolima = os.path.join(directorio_base, "json", "json_tolima", "Contrato_Pgp_Tolima.json")
