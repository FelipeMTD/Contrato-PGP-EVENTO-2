import random
import pandas as pd
import os
from playwright.async_api import Page

class AfiliacionPage:
    def __init__(self, page: Page):
        self.page = page
        self.iframe_selector = 'iframe[src*="consultarAfiliacion"]'
        self.select_tipo_doc = 'select[name="appForm:solTipdoc"]'  
        self.input_doc = 'input[name="appForm:itNumdoc"]'      
        self.btn_consultar = 'input[id="appForm:cbQAfil"]'        
        # Actualizado al botón real de Retornar
        self.btn_retornar = 'input[src*="btnRetornar"]'        
    
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

        # --- NUEVA VALIDACIÓN DE COLUMNAS ---
        df.columns = df.columns.str.replace('_x000d_', '', regex=False).str.strip()

        if 'Tipo' not in df.columns or 'Documento' not in df.columns:
            print("\n[!] ERROR DE EXCEL: No se encontraron las columnas correctas.")
            print(f"-> Columnas que el bot está viendo en tu archivo: {df.columns.tolist()}")
            print("-> Solución: Abre tu Excel y asegúrate de que la Fila 1 tenga 'Tipo' y 'Documento'.")
            return  

        # 1. Crear las nuevas columnas y FORZARLAS a ser texto
        columnas_extraer = [
            'Nombre Usuario', 'Estado Afiliación Usuario', 'Departamento', 
            'Municipio', 'Tipo Afiliado', 'Categoría Afiliado', 'IPS Primaria'
        ]
        for col in columnas_extraer:
            if col not in df.columns:
                df[col] = ""
            df[col] = df[col].astype(object) 

        print(f"Se procesarán {len(df)} registros.")

        # 2. Localizar el iFrame
        await self.page.wait_for_selector(self.iframe_selector, state="visible", timeout=20000)
        frame = self.page.frame_locator(self.iframe_selector)

        try:
            print("Esperando a que el contenido del iFrame cargue...")
            await frame.locator(self.select_tipo_doc).wait_for(state="visible", timeout=15000)
        except Exception:
            print("\n[!] ALERTA: No se encontró el campo Tipo de Documento.")
            print("Por favor verifica si el selector (self.select_tipo_doc) es el correcto.")
            return

  
        # 3. Iniciar el ÚNICO bucle de procesamiento
        for index, row in df.iterrows():
            tipo = str(row['Tipo']).strip()
            doc = str(row['Documento']).strip()
            
            print(f"[{index + 1}/{len(df)}] Consultando: {tipo} - {doc} ... ", end="", flush=True)

            try:
                await frame.locator(self.select_tipo_doc).select_option(label=tipo)
                await self.pausa_humana(300, 700) 
                
                # --- CAMBIO 1: LIMPIEZA PREVENTIVA ---
                # Borramos cualquier número viejo que haya quedado de una consulta fallida anterior
                await frame.locator(self.input_doc).clear()
                
                # Escribir el documento simulando tecleo humano
                await frame.locator(self.input_doc).press_sequentially(doc, delay=random.randint(40, 90))
                await self.pausa_humana(400, 900) 
                
                # Clic robusto en consultar
                btn_locator = frame.locator(self.btn_consultar)
                try:
                    await btn_locator.click(force=True, timeout=5000)
                except Exception:
                    await btn_locator.evaluate("el => el.click()")
                
                await self.page.wait_for_timeout(3000) 
                
                # --- CAMBIO 2: DETECCIÓN DE "CAMINO TRISTE" (EL PACIENTE NO EXISTE) ---
                # Verificamos si la tabla realmente cargó buscando la etiqueta "Nombre Usuario"
                validador_tabla = frame.locator("xpath=//label[contains(normalize-space(text()), 'Nombre Usuario')]")
                
                if await validador_tabla.count() == 0:
                    # Si no hay tabla, buscamos si el portal arrojó un mensaje de error rojo/amarillo
                    msg_error_locator = frame.locator("xpath=//ul[contains(@id, 'msg')]//li | //span[contains(@class, 'mensajes')]")
                    
                    if await msg_error_locator.count() > 0:
                        mensaje_error = await msg_error_locator.first.inner_text()
                        print(f"❌ {mensaje_error}")
                        df.at[index, 'Estado Afiliación Usuario'] = f"NO ENCONTRADO - {mensaje_error}"
                    else:
                        print("❌ No encontrado / No registra")
                        df.at[index, 'Estado Afiliación Usuario'] = "NO ENCONTRADO"
                    
                    # Saltamos inmediatamente al siguiente paciente sin intentar extraer ni dar clic en "Retornar"
                    continue
                # ----------------------------------------------------------------------

                # Si el código llega aquí, es porque el paciente SÍ existe (Camino Feliz)
                df.at[index, 'Nombre Usuario'] = await self.extraer_dato_tabla(frame, "Nombre Usuario")
                df.at[index, 'Estado Afiliación Usuario'] = await self.extraer_dato_tabla(frame, "Estado Afiliación Usuario")
                df.at[index, 'Departamento'] = await self.extraer_dato_tabla(frame, "Departamento")
                df.at[index, 'Municipio'] = await self.extraer_dato_tabla(frame, "Municipio")
                df.at[index, 'Tipo Afiliado'] = await self.extraer_dato_tabla(frame, "Tipo Afiliado")
                df.at[index, 'Categoría Afiliado'] = await self.extraer_dato_tabla(frame, "Categoría Afiliado")
                df.at[index, 'IPS Primaria'] = await self.extraer_dato_tabla(frame, "IPS Primaria") 
                
                print("¡Extraído!")
                await self.pausa_humana(1500, 3000)

                # 6. Limpiar el formulario usando el botón "Retornar"
                if await frame.locator(self.btn_retornar).count() > 0:
                    await frame.locator(self.btn_retornar).click(delay=random.randint(50, 100))
                    await self.page.wait_for_timeout(2000) 

            except Exception as e:
                print(f"Error crítico en consulta: {str(e)}")
                df.at[index, 'Estado Afiliación Usuario'] = "Error interno del bot"

        # 7. Guardar el nuevo Excel
        nombre_archivo_salida = f"Resultados_{os.path.basename(ruta_excel)}"
        df.to_excel(nombre_archivo_salida, index=False)
        print(f"\n--- ✅ EXTRACCIÓN FINALIZADA ---")
        print(f"Los datos han sido guardados exitosamente en: {nombre_archivo_salida}")

    async def extraer_dato_tabla(self, frame, label_text: str) -> str:
        """
        Busca dinámicamente un texto (label) en la pantalla y extrae el valor contiguo.
        Adaptado específicamente para la tabla de ICEfaces (inputs y textareas de Solo Lectura).
        """
        try:
            clean_label = label_text.strip()
            
            # 1. Buscamos primero en los INPUTS normales (Nombre, Estado, Municipio, etc.)
            xpath_input = f"xpath=//label[contains(normalize-space(text()), '{clean_label}')]/ancestor::td/following-sibling::td//input"
            locator_input = frame.locator(xpath_input)
            
            if await locator_input.count() > 0:
                texto = await locator_input.first.input_value()
                return " ".join(texto.split()) if texto else "Dato Vacío"

            # 2. Si no es un input, buscamos en TEXTAREA (Exclusivo para la "IPS Primaria")
            xpath_textarea = f"xpath=//label[contains(normalize-space(text()), '{clean_label}')]/ancestor::td/following-sibling::td//textarea"
            locator_textarea = frame.locator(xpath_textarea)
            
            if await locator_textarea.count() > 0:
                texto = await locator_textarea.first.input_value() 
                return " ".join(texto.split()) if texto else "Dato Vacío"

            # 3. Respaldo: Si algún dato está suelto como texto normal
            xpath_text = f"xpath=//label[contains(normalize-space(text()), '{clean_label}')]/ancestor::td/following-sibling::td"
            locator_text = frame.locator(xpath_text)
            
            if await locator_text.count() > 0:
                texto = await locator_text.first.inner_text()
                return " ".join(texto.split()) if texto else "Dato Vacío"

            return "No encontrado"
            
        except Exception as e:
            print(f"  -> Error interno extrayendo '{label_text}': {e}")
            return "Error"