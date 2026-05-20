import pandas as pd
import os
import traceback

def integrar_y_transformar():
    try:
        # 1. Obtener la ruta absoluta del directorio actual
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        ruta_crudos = os.path.join(ruta_base, 'datos_crudos')
        ruta_salida = os.path.join(ruta_base, 'data')
        
        print(f"Buscando archivos crudos en: {ruta_crudos}")
        
        # 2. Cargar fuentes de datos
        archivo_simat = os.path.join(ruta_crudos, 'simat_desercion_2023_2026.csv')
        archivo_dane = os.path.join(ruta_crudos, 'dane_nacimientos_2023_2026.csv')
        archivo_pobreza = os.path.join(ruta_crudos, 'dane_pobreza.csv')
        
        df_simat = pd.read_csv(archivo_simat)
        df_dane = pd.read_csv(archivo_dane)
        df_pobreza = pd.read_csv(archivo_pobreza)

        print("Integrando datasets...")
        # 3. Integración (INNER JOIN)
        df_merged = pd.merge(df_simat, df_dane, on=['Departamento', 'Año'], how='inner')
        df_final = pd.merge(df_merged, df_pobreza, on=['Departamento', 'Año'], how='inner')

        # 4. Cálculos
        df_final['Tasa_Desercion_Femenina'] = round((df_final['Desertoras_Estimadas'] / df_final['Matriculadas_Secundaria']) * 100, 2)
        df_final['Tasa_Fecundidad_Adolescente'] = round((df_final['Nacimientos_15_19'] / df_final['Poblacion_Femenina_15_19']) * 1000, 2)
        
        zonas_regionales = {
            'Antioquia': 'Urbana', 'Atlántico': 'Urbana', 'Cundinamarca': 'Urbana', 'Valle del Cauca': 'Urbana', 'Santander': 'Urbana',
            'Chocó': 'Rural', 'Vaupés': 'Rural', 'Vichada': 'Rural', 'Guainía': 'Rural', 'Amazonas': 'Rural', 'Guaviare': 'Rural'
        }
        df_final['Zona'] = df_final['Departamento'].apply(lambda depto: zonas_regionales.get(depto, 'Mixta'))

        columnas_dashboard = [
            'Departamento', 'Año', 'Zona', 'Tasa_Desercion_Femenina', 'Tasa_Fecundidad_Adolescente',
            'Matriculadas_Secundaria', 'Desertoras_Estimadas', 'Nacimientos_10_14', 'Nacimientos_15_19',
            'Cobertura_Edu_Sexual', 'Tasa_Pobreza', 'Programa_Retencion', 'Indice_Vulnerabilidad'
        ]
        
        df_final = df_final[columnas_dashboard]

        # 5. Crear carpeta de salida si no existe
        os.makedirs(ruta_salida, exist_ok=True)

        # 6. Exportar
        archivo_final = os.path.join(ruta_salida, 'desercion_embarazo.csv')
        df_final.to_csv(archivo_final, index=False)
        
        print("\n" + "="*50)
        print("✓ ¡ÉXITO! El dataset se ha creado correctamente.")
        print(f"✓ RUTA EXACTA DEL ARCHIVO: {archivo_final}")
        print("="*50 + "\n")
        
        print("Siguiente paso: Ejecuta 'python app.py' para abrir el Dashboard.")

    except FileNotFoundError as e:
        print("\nERROR: No se encontraron los archivos crudos.")
        print("Asegúrate de haber ejecutado primero 'python crear_crudos.py'")
        print(f"Detalle: {e}")
    except Exception as e:
        print("\nERROR INESPERADO:")
        traceback.print_exc()

if __name__ == '__main__':
    integrar_y_transformar()