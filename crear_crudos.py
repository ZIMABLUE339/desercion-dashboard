import pandas as pd
import numpy as np
import os

def generar_archivos_crudos():
    departamentos = [
        "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", "Boyacá", 
        "Caldas", "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó", "Córdoba", 
        "Cundinamarca", "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena", 
        "Meta", "Nariño", "Norte de Santander", "Putumayo", "Quindío", "Risaralda", 
        "San Andrés y Providencia", "Santander", "Sucre", "Tolima", "Valle del Cauca", 
        "Vaupés", "Vichada"
    ]
    anios = [2023, 2024, 2025, 2026]
    
    datos_base = []
    for depto in departamentos:
        # Generar un perfil base por departamento para mantener consistencia en los años
        vuln_base = np.random.uniform(0.3, 0.9)
        pob_fem = int(np.random.uniform(5000, 150000))
        
        for anio in anios:
            datos_base.append({
                'Departamento': depto,
                'Año': anio,
                'Vulnerabilidad': vuln_base + np.random.uniform(-0.05, 0.05),
                'Poblacion': pob_fem + int(np.random.normal(0, 500))
            })
            
    df_base = pd.DataFrame(datos_base)

    # 1. Archivo SIMAT (Deserción)
    df_simat = df_base[['Departamento', 'Año']].copy()
    df_simat['Matriculadas_Secundaria'] = (df_base['Poblacion'] * np.random.uniform(0.7, 0.9)).astype(int)
    # Mayor vulnerabilidad = mayor deserción (entre 3% y 25%)
    tasa_des = df_base['Vulnerabilidad'] * np.random.uniform(0.15, 0.30)
    df_simat['Desertoras_Estimadas'] = (df_simat['Matriculadas_Secundaria'] * tasa_des).astype(int)
    
    # 2. Archivo DANE (Nacimientos)
    df_dane = df_base[['Departamento', 'Año']].copy()
    df_dane['Poblacion_Femenina_15_19'] = (df_base['Poblacion'] * np.random.uniform(0.2, 0.3)).astype(int)
    # Mayor vulnerabilidad = mayor fecundidad
    tasa_fec = df_base['Vulnerabilidad'] * np.random.uniform(0.08, 0.12)
    df_dane['Nacimientos_15_19'] = (df_dane['Poblacion_Femenina_15_19'] * tasa_fec).astype(int)
    df_dane['Nacimientos_10_14'] = (df_dane['Nacimientos_15_19'] * np.random.uniform(0.05, 0.15)).astype(int)

    # 3. Archivo Pobreza y Contexto
    df_pobreza = df_base[['Departamento', 'Año']].copy()
    df_pobreza['Tasa_Pobreza'] = np.clip(df_base['Vulnerabilidad'] * 100 + np.random.normal(0, 5, len(df_base)), 10, 95).round(1)
    df_pobreza['Cobertura_Edu_Sexual'] = np.clip(100 - df_pobreza['Tasa_Pobreza'] + np.random.normal(0, 10, len(df_base)), 10, 90).round(1)
    df_pobreza['Indice_Vulnerabilidad'] = np.clip(df_base['Vulnerabilidad'], 0.1, 1.0).round(2)
    
    # === LÍNEA CORREGIDA (usando df_base en lugar de df_pobreza) ===
    df_pobreza['Programa_Retencion'] = np.where(df_base['Vulnerabilidad'] < 0.6, 'Sí', 'No')

    # Crear carpeta datos_crudos si no existe
    os.makedirs('datos_crudos', exist_ok=True)

    # Exportar los CSVs
    df_simat.to_csv('datos_crudos/simat_desercion_2023_2026.csv', index=False)
    df_dane.to_csv('datos_crudos/dane_nacimientos_2023_2026.csv', index=False)
    df_pobreza.to_csv('datos_crudos/dane_pobreza.csv', index=False)

    print("¡Listo! Los archivos se han generado en la carpeta 'datos_crudos':")
    print(" 1. simat_desercion_2023_2026.csv")
    print(" 2. dane_nacimientos_2023_2026.csv")
    print(" 3. dane_pobreza.csv")

if __name__ == '__main__':
    generar_archivos_crudos()