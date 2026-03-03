import pandas as pd
import json
import os

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
            
            # Navegamos hasta la lista de IPS (Ajusta las llaves si tu JSON es diferente)
            ips_crudas = datos.get("PGP_BOYACA", {}).get("IPS_PRIMARIA", [])
            
            # Normalizamos: todo a mayúsculas y sin espacios a los lados
            return [str(ips).strip().upper() for ips in ips_crudas]
            
        except Exception as e:
            print(f"[!] Error leyendo el JSON: {e}")
            return []

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
                # Aplicamos la lógica de vectorización de Pandas
                df['Tipo Contrato'] = df['IPS Primaria'].apply(
                    lambda ips: "PGP" if str(ips).strip().upper() in self.ips_pgp_lista else "EVENTO"
                )
            
            # Guardamos el archivo sobrescribiendo el de Resultados (o creando uno nuevo)
            df.to_excel(ruta_excel, index=False)
            
            print(f"✅ Clasificación exitosa. Archivo guardado como: {ruta_excel}")
            
        except Exception as e:
            print(f"[!] Error procesando el Excel: {e}")