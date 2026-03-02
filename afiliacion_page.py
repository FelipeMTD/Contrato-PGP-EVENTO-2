import random
import pandas as pd
import os
from playwright.async_api import Page

class AfiliacionPage:
    def __init__(self, page: Page):
        self.page = page
        # Selectores del formulario (ajústalos si los name/ids son diferentes)
        self.iframe_selector = 'iframe[src*="consultarAfiliacion"]'
        self.select_tipo_doc = 'select[name="appForm:solTipdoc"]'  
        self.input_doc = 'input[name="appForm:itNumdoc"]'      
        self.btn_consultar = 'input[id="appForm:cbQAfil"]'        
        self.btn_limpiar = 'input[value="Limpiar"]'        
    
    async def pausa_humana(self, min_ms=800, max_ms=2500):
        """
        Genera una pausa aleatoria entre min_ms y max_ms (milisegundos).
        Imita el tiempo de reacción de una persona leyendo la pantalla.
        """
        tiempo_espera = random.uniform(min_ms, max_ms)
        await self.page.wait_for_timeout(tiempo_espera)        


    async def procesar_consultas_excel(self, ruta_excel: str):
            print(f"Cargando archivo: {ruta_excel}...")
            df = pd.read_excel(ruta_excel)

            # 1. Crear las nuevas columnas y FORZARLAS a ser texto (Solución Error Pandas float64)
            columnas_extraer = [
                'Nombre Usuario', 'Estado Afiliación Usuario', 'Departamento', 
                'Municipio', 'Tipo Afiliado', 'Categoría Afiliado', 'IPS Primaria'
            ]
            for col in columnas_extraer:
                if col not in df.columns:
                    df[col] = ""
                df[col] = df[col].astype(object) # Forzamos el tipo de dato a texto/objeto

            print(f"Se procesarán {len(df)} registros.")

            # 2. Localizar el iFrame y esperar a que exista en la página
            await self.page.wait_for_selector(self.iframe_selector, state="visible", timeout=20000)
            frame = self.page.frame_locator(self.iframe_selector)

            # Esperamos explícitamente a que el primer campo cargue dentro del iFrame
            try:
                print("Esperando a que el contenido del iFrame cargue...")
                # 4. Clic en consultar (Estrategia Anti-Bloqueos ICEfaces)
                btn_locator = frame.locator(self.btn_consultar)
                
                try:
                    # Intento 1: Clic forzado (ignora si hay un loader invisible bloqueando)
                    await btn_locator.click(force=True, timeout=5000)
                except Exception:
                    print("Clic normal interceptado. Usando JavaScript...")
                    # Intento 2: Inyección de clic por JavaScript (Infalible en ICEfaces)
                    await btn_locator.evaluate("el => el.click()")
                
                print("Clic realizado, esperando respuesta del servidor...")
                
            except Exception:
                print("\n[!] ALERTA: No se encontró el campo Tipo de Documento.")
                print("Por favor verifica si el selector (self.select_tipo_doc) es el correcto en el HTML del iFrame.")
                return

            # 3. Iniciar el ÚNICO bucle de procesamiento
            for index, row in df.iterrows():
                tipo = str(row['Tipo']).strip()
                doc = str(row['Documento']).strip()
                
                print(f"[{index + 1}/{len(df)}] Consultando: {tipo} - {doc} ... ", end="", flush=True)

                try:
                    # --- INYECCIÓN DE COMPORTAMIENTO HUMANO ---
                    
                    # Seleccionar tipo de documento
                    await frame.locator(self.select_tipo_doc).select_option(label=tipo)
                    await self.pausa_humana(300, 700) 
                    
                    # Escribir el documento simulando tecleo humano
                    await frame.locator(self.input_doc).press_sequentially(doc, delay=random.randint(40, 90))
                    await self.pausa_humana(400, 900) 
                    
                    # Clic en consultar con leve retardo
                    await frame.locator(self.btn_consultar).click(delay=random.randint(50, 150))
                    
                    # Esperar a que la tabla de resultados se renderice
                    await self.page.wait_for_timeout(3000) 
                    
                    # 5. Extracción de datos usando nuestra función dinámica
                    df.at[index, 'Nombre Usuario'] = await self.extraer_dato_tabla(frame, "Nombre Usuario")
                    df.at[index, 'Estado Afiliación Usuario'] = await self.extraer_dato_tabla(frame, "Estado")
                    df.at[index, 'Departamento'] = await self.extraer_dato_tabla(frame, "Departamento")
                    df.at[index, 'Municipio'] = await self.extraer_dato_tabla(frame, "Municipio")
                    df.at[index, 'Tipo Afiliado'] = await self.extraer_dato_tabla(frame, "Tipo Afiliado")
                    df.at[index, 'Categoría Afiliado'] = await self.extraer_dato_tabla(frame, "Categoría")
                    df.at[index, 'IPS Primaria'] = await self.extraer_dato_tabla(frame, "IPS Primaria")
                    
                    print("¡Extraído!")

                    # Pausa larga imitando el tiempo de lectura humana
                    await self.pausa_humana(1500, 3000)

                    # 6. Limpiar el formulario para el siguiente paciente
                    if await frame.locator(self.btn_limpiar).count() > 0:
                        await frame.locator(self.btn_limpiar).click(delay=random.randint(50, 100))
                        await self.page.wait_for_timeout(1000)

                except Exception as e:
                    print(f"Error: {str(e)}")
                    df.at[index, 'Estado Afiliación Usuario'] = "Error en extracción"

            # 7. Guardar el nuevo Excel sin sobrescribir el original
            import os # Asegúrate de que el import os esté arriba en tu archivo
            nombre_archivo_salida = f"Resultados_{os.path.basename(ruta_excel)}"
            df.to_excel(nombre_archivo_salida, index=False)
            print(f"\n--- ✅ EXTRACCIÓN FINALIZADA ---")
            print(f"Los datos han sido guardados exitosamente en: {nombre_archivo_salida}")

    async def extraer_dato_tabla(self, frame, label_text: str) -> str:
        """
        Busca dinámicamente un texto en la pantalla y extrae el valor que está a su lado.
        Maneja la estructura típica de tablas <td>Label:</td> <td>Valor</td> de Nueva EPS.
        """
        try:
            # Estrategia 1: Buscar un <td> que contenga el texto y agarrar el <td> hermano siguiente
            xpath_td = f"xpath=//td[contains(text(), '{label_text}')]/following-sibling::td[1]"
            locator_td = frame.locator(xpath_td)
            
            if await locator_td.count() > 0:
                texto = await locator_td.first.inner_text()
                return " ".join(texto.split())

            # Estrategia 2: Por si la estructura usa <span> en lugar de textos sueltos en <td>
            xpath_span = f"xpath=//span[contains(text(), '{label_text}')]/following::span[1]"
            locator_span = frame.locator(xpath_span)
            
            if await locator_span.count() > 0:
                texto = await locator_span.first.inner_text()
                return " ".join(texto.split())

            return "No encontrado"
            
        except Exception:
            return "Error de lectura"