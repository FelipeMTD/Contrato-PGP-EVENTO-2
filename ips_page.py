import sys
from playwright.async_api import Page

class IpsPage:
    def __init__(self, page: Page):
        self.page = page
        self.select_ips = 'select[id="j_id121:ips"]'
        self.select_sucursal = 'select[id="j_id121:sucIps"]'
        self.btn_aceptar = 'input[id="j_id121:acceptButton"]'

    async def configurar_parametros(self):
        # 1. Seleccionar la única IPS disponible (la segunda opción del select)
        print("Seleccionando IPS por defecto...")
        await self.page.wait_for_selector(self.select_ips)
        # Seleccionamos por índice 1 (el 0 es "Seleccionar")
        await self.page.select_option(self.select_ips, index=1)
        
        # 2. Esperar a que las sucursales carguen (ICEfaces suele refrescar el DOM)
        await self.page.wait_for_timeout(1000) 
        
        # 3. Obtener todas las opciones de sucursal
        opciones = await self.page.locator(f"{self.select_sucursal} option").all_inner_texts()
        
        # Filtrar la opción "Seleccionar"
        sucursales_validas = [opt for opt in opciones if opt != "Seleccionar"]

        # 4. Preguntar al usuario por consola
        print("\n--- SUCURSALES DISPONIBLES ---")
        for i, nombre in enumerate(sucursales_validas, 1):
            print(f"{i}. {nombre}")
        
        try:
            seleccion = int(input("\nElija el número de la sucursal para la búsqueda: "))
            if 1 <= seleccion <= len(sucursales_validas):
                nombre_elegido = sucursales_validas[seleccion - 1]
                print(f"Has elegido: {nombre_elegido}")
                
                # Seleccionar por etiqueta (label)
                await self.page.select_option(self.select_sucursal, label=nombre_elegido)
            else:
                print("Selección inválida. Terminando proceso por seguridad.")
                sys.exit()
        except ValueError:
            print("Entrada no válida. Debe ser un número.")
            sys.exit()

        # 5. Clic en Aceptar y esperar navegación
        async with self.page.expect_navigation():
            await self.page.click(self.btn_aceptar)