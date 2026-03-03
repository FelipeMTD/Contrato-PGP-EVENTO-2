import pandas as pd
import json
import os
import re  # <-- LIBRERÍA NUEVA AGREGADA AQUÍ

class ClasificadorContratos:
    def __init__(self, ruta_json: str):
        self.ruta_json = ruta_json
        self.ips_pgp_lista = self._cargar_ips_pgp()

    def _cargar_ips_pgp(self) -> list:
        """Carga y normaliza la lista de IPS desde el archivo JSON."""
        if not os.path.exists(self.ruta_json):
            print(f"[!] ADVERTENCIA: No se encontró el JSON en {self.ruta_json}")
            return []
            
        try:
            with open(self.ruta_json, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            # --- MEJORA DINÁMICA ---
            # Tomamos la primera llave del JSON automáticamente (sea PGP_BOYACA o PGP_TOLIMA)
            llave_departamento = list(datos.keys())[0] 
            
            # Navegamos hasta la lista de IPS usando esa llave
            ips_crudas = datos.get(llave_departamento, {}).get("IPS_PRIMARIA", [])
            # -----------------------

            # Normalizamos: todo a mayúsculas y sin espacios a los lados
            return [str(ips).strip().upper() for ips in ips_crudas]
            
        except Exception as e:
            print(f"[!] Error leyendo el JSON: {e}")
            return []


    # --- NUEVA FUNCIÓN DE LIMPIEZA EXTREMA ---
    def limpiar_texto(self, texto):
        """Elimina saltos de línea ocultos, espacios dobles y pasa a mayúsculas."""
        texto_limpio = str(texto).replace('_x000d_', '').strip().upper()
        return re.sub(r'\s+', ' ', texto_limpio) # Convierte 2+ espacios en 1 solo
    # -----------------------------------------

    def procesar_excel(self, ruta_excel: str):
        """Lee el Excel, cruza la información con el JSON y guarda el resultado."""
        if not os.path.exists(ruta_excel):
            print(f"[!] Error: No se encontró el archivo Excel {ruta_excel}")
            return

        print(f"\n--- INICIANDO CLASIFICACIÓN PGP/EVENTO ---")
        print(f"Cruzando datos de: {ruta_excel}")
        
        try:
            df = pd.read_excel(ruta_excel)
            
            # Verificamos que la columna 'IPS Primaria' exista
            if 'IPS Primaria' not in df.columns:
                print("[!] El Excel no tiene la columna 'IPS Primaria'. No se puede clasificar.")
                return

            # Si la lista del JSON está vacía, marcamos todo como EVENTO por seguridad
            if not self.ips_pgp_lista:
                print("La lista PGP está vacía o no se pudo leer. Todo será EVENTO.")
                df['Tipo Contrato'] = "EVENTO"
            else:
                # --- APLICAMOS LA FUNCIÓN DE LIMPIEZA AQUÍ ---
                df['Tipo Contrato'] = df['IPS Primaria'].apply(
                    lambda ips: "PGP" if self.limpiar_texto(ips) in self.ips_pgp_lista else "EVENTO"
                )
            
            # Guardamos el archivo sobrescribiendo el de Resultados
            df.to_excel(ruta_excel, index=False)
            
            print(f"✅ Clasificación exitosa. Archivo guardado como: {ruta_excel}")
            
        except Exception as e:
            print(f"[!] Error procesando el Excel: {e}")