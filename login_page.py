import random
from playwright.async_api import Page
from config import Config

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        # Selectores basados en el HTML que proveíste
        self.select_tipo = 'select[id="loginForm:tipoId"]'
        self.input_id = 'input[id="loginForm:id"]'
        self.input_pass = 'input[id="loginForm:clave"]'
        self.btn_login = 'input[id="loginForm:loginButton"]'
        self.btn_servicios_linea = 'img#tabServicios'

    async def pausa_humana(self, min_ms=500, max_ms=1500):
        """Genera una pausa aleatoria para simular comportamiento humano."""
        tiempo_espera = random.uniform(min_ms, max_ms)
        await self.page.wait_for_timeout(tiempo_espera)

    async def navegar(self):
        # Esperamos a que la red esté tranquila para asegurar que los scripts anti-bot cargaron
        await self.page.goto(Config.URL, wait_until="networkidle")
        await self.pausa_humana(1000, 2500) # El humano espera a que cargue la página y la mira

    async def realizar_login(self):
        # 1. Seleccionar tipo (CC, TI, etc.)
        await self.page.select_option(self.select_tipo, value=str(Config.USER_TYPE))
        await self.pausa_humana(300, 700) # Pausa para mover la vista al siguiente campo
        
        # 2. Llenar credenciales (Tecleando como humano)
        # El número de documento
        await self.page.locator(self.input_id).press_sequentially(str(Config.USER_ID), delay=random.randint(40, 90))
        await self.pausa_humana(400, 800) # Verifica lo escrito
        
        # La contraseña
        await self.page.locator(self.input_pass).press_sequentially(Config.PASSWORD, delay=random.randint(40, 90))
        await self.pausa_humana(500, 1000) # Mueve el mouse hacia el botón

        # 3. Disparar evento de click (Con retención de clic) y esperar navegación
        async with self.page.expect_navigation():
            await self.page.locator(self.btn_login).click(delay=random.randint(50, 150))

    async def ir_a_servicios_linea(self):
        print("Esperando botón de Servicios en Línea...")
        # Pausa humana leyendo la pantalla de bienvenida (Hola, Viviana Marcela...)
        await self.pausa_humana(1500, 3000) 
        
        # Esperamos a que la imagen del tab esté visible
        await self.page.wait_for_selector(self.btn_servicios_linea, state="visible")
        
        # Hacemos clic simulando el dedo en el ratón
        async with self.page.expect_navigation():
            await self.page.locator(self.btn_servicios_linea).click(delay=random.randint(50, 150))
            
        print("Accediendo al panel de Servicios en Línea.")