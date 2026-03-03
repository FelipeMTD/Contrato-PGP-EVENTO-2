import os
import sys
import asyncio
import shutil
from playwright.async_api import async_playwright
# from playwright_stealth import stealth# Importación de tus módulos locales
from config import Config
from login_page import LoginPage
from ips_page import IpsPage
from afiliacion_page import AfiliacionPage
from clasificador_contratos import ClasificadorContratos
async def iniciar_proyecto_privado():
    """
    Orquestador principal del bot de consulta Nueva EPS.
    Diseñado para ejecución limpia (Zero Trace) y evasión de detección.
    """
    
    # 1. GESTIÓN DE RASTRO: Limpieza de archivos temporales previos
    tmp_dir = "./tmp"
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    async with async_playwright() as p:
        print("--- INICIANDO MOTOR DE NAVEGACIÓN (MODO SIGILO) ---")
        
        # 2. LANZAMIENTO: Configuración de navegador para anonimato
        browser = await p.chromium.launch(
            channel="msedge",
            headless=Config.HEADLESS,
            slow_mo=Config.SLOW_MO,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        # 3. CONTEXTO: Creación de sesión aislada con User-Agent real
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        page = await context.new_page()
        
        # 4. STEALTH: Aplicar scripts para ocultar huellas de automatización
        # await stealth(page)
        # Instancia de las clases POM
        login = LoginPage(page)
        ips_selection = IpsPage(page)
        afiliacion = AfiliacionPage(page)

        try:
            # EVENTO 1: Navegación Inicial y Login
            print(f"Paso 1: Accediendo a {Config.URL}...")
            await login.navegar()
            
            print("Paso 2: Ejecutando Login...")
            await login.realizar_login()
            
            # EVENTO 2: Transición a Servicios en Línea
            print("Paso 3: Entrando a Servicios en Línea...")
            await login.ir_a_servicios_linea()
            
            # --- EL DETALLE QUE FALTABA: REDIRECCIÓN EXPLÍCITA ---
            print("Redirigiendo a la pantalla de selección de IPS...")
            await page.goto("https://portal.nuevaeps.com.co/Portal/pages/ips/chooseParameter.jspx", wait_until="networkidle")
            # -----------------------------------
            
            # EVENTO 3: Configuración Dinámica de IPS (Consola)
            # Aquí el script se detendrá para pedirte la sucursal por consola
            print("Paso 4: Configurando parámetros de IPS...")
            await ips_selection.configurar_parametros()
            
            # EVENTO 4: Navegación a Consulta de Afiliación
            # Forzamos la URL directa para evitar navegación por menús complejos
            print("Paso 5: Navegando al módulo de Estado de Afiliación...")
            target_url = "https://portal.nuevaeps.com.co/Portal/pages/ips/autorizaciones/consultarEstadoAfiliacion.jspx"
            await page.goto(target_url, wait_until="networkidle")

            # --- ESTRATEGIA DE RUTAS ABSOLUTAS PARA EL .EXE ---
            # --- ESTRATEGIA DE RUTAS PARA .EXE ---
            # Detectar si estamos en el .exe o en el .py
            if getattr(sys, 'frozen', False):
                directorio_base = os.path.dirname(sys.executable) # Donde está el .exe
            else:
                directorio_base = os.path.dirname(os.path.abspath(__file__)) # Donde está el .py
            
            # Construir las rutas exactas
            excel_file = os.path.join(directorio_base, "datos_afiliados.xlsx")
            archivo_resultados = os.path.join(directorio_base, "Resultados_datos_afiliados.xlsx")
            # ruta_json_boyaca = os.path.join(directorio_base, "json", "json_boyaca", "Contrato_Pgp_Boyaca.json")
            ruta_json_tolima = os.path.join(directorio_base, "json", "json_tolima", "Contrato_Pgp_Tolima.json")
            # -------------------------------------

            if os.path.exists(excel_file):
                print(f"Paso 6: Iniciando procesamiento de datos_afiliados.xlsx...")
                # Pasamos la ruta absoluta
                await afiliacion.procesar_consultas_excel(excel_file)
                
                # --- EVENTO 6: Clasificación PGP / EVENTO ---
                # print(f"Buscando archivo JSON en: {ruta_json_boyaca}") # <-- ESTO NOS DIRÁ SI LA RUTA ESTÁ BIEN
                # clasificador = ClasificadorContratos(ruta_json_boyaca)
                print(f"Buscando archivo JSON en: {ruta_json_tolima}") # <-- ESTO NOS DIRÁ SI LA RUTA ESTÁ BIEN
                clasificador = ClasificadorContratos(ruta_json_tolima)
                clasificador.procesar_excel(archivo_resultados)
                # --------------------------------------------------
            else:
                print(f"ADVERTENCIA: No se encontró el archivo 'datos_afiliados.xlsx' en: {directorio_base}")

            print("\n--- PROCESO FINALIZADO EXITOSAMENTE ---")

        except Exception as e:
            print(f"\n[!] ERROR CRÍTICO: {e}")
            # Captura de pantalla de error en la carpeta temporal (se borrará al final)
            await page.screenshot(path=f"{tmp_dir}/error_captura.png")
            
        finally:
            # 5. CIERRE SEGURO: Liberación de memoria y procesos
            await context.close()
            await browser.close()
            
            # 6. LIMPIEZA TOTAL: Eliminación física de cualquier rastro en disco
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            print("Sesión cerrada y rastro eliminado del sistema.")

if __name__ == "__main__":
    # En Windows, Playwright requiere ProactorEventLoop para abrir el navegador
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    asyncio.run(iniciar_proyecto_privado())
