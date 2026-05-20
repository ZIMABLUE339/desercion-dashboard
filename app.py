"""
Dashboard: Embarazo Adolescente y Deserción Escolar Femenina en Colombia
Período 2023–2026 | Metodología SEMMA
"""
from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
from datetime import datetime
from scipy import stats as scipy_stats
import numpy as np

app = Flask(__name__)

# ==================== CARGA DE DATOS ====================
try:
    df = pd.read_csv('data/desercion_embarazo.csv')
    df.columns = df.columns.str.strip()
    print(f"✓ Dataset cargado: {df.shape[0]} registros, {df.shape[1]} columnas")
except Exception as e:
    print(f"Error al cargar datos: {e}")
    df = None

DEPTO_COL   = 'Departamento'
YEAR_COL    = 'Año'
ZONA_COL    = 'Zona'
NUMERIC_INDICATORS = [
    'Tasa_Desercion_Femenina',
    'Tasa_Fecundidad_Adolescente',
    'Matriculadas_Secundaria',
    'Desertoras_Estimadas',
    'Nacimientos_10_14',
    'Nacimientos_15_19',
    'Cobertura_Edu_Sexual',
    'Tasa_Pobreza',
    'Indice_Vulnerabilidad'
]
INDICATOR_LABELS = {
    'Tasa_Desercion_Femenina':      'Tasa de Deserción Femenina (%)',
    'Tasa_Fecundidad_Adolescente':  'Tasa de Fecundidad Adolescente (x1000)',
    'Matriculadas_Secundaria':      'Matriculadas en Secundaria',
    'Desertoras_Estimadas':         'Desertoras Estimadas',
    'Nacimientos_10_14':            'Nacimientos niñas 10–14 años',
    'Nacimientos_15_19':            'Nacimientos adolescentes 15–19 años',
    'Cobertura_Edu_Sexual':         'Cobertura Educación Sexual (%)',
    'Tasa_Pobreza':                 'Tasa de Pobreza Multidimensional (%)',
    'Indice_Vulnerabilidad':        'Índice de Vulnerabilidad (0–1)'
}

# ==================== FUNCIONES AUXILIARES ====================

def get_unique(col):
    if df is None or col not in df.columns:
        return []
    return sorted([str(v) for v in df[col].dropna().unique()])

def filter_data(depto=None, year=None, zona=None, indicator=None):
    filtered = df.copy()
    if year:
        try:
            filtered = filtered[filtered[YEAR_COL].astype(str) == str(int(year))]
        except:
            pass
    if depto:
        filtered = filtered[filtered[DEPTO_COL].str.contains(depto, case=False, na=False)]
    if zona:
        filtered = filtered[filtered[ZONA_COL].str.contains(zona, case=False, na=False)]
    if indicator and indicator in filtered.columns:
        filtered = filtered[[DEPTO_COL, YEAR_COL, ZONA_COL, indicator]]
    return filtered

def prepare_chart_data(fdf):
    if fdf.empty:
        return []
    data = []
    for _, row in fdf.iterrows():
        row_data = {
            'departamento': row[DEPTO_COL],
            'year': str(row[YEAR_COL]),
            'zona': row.get(ZONA_COL, ''),
            'values': {}
        }
        for col in fdf.columns:
            if col in [DEPTO_COL, YEAR_COL, ZONA_COL]:
                continue
            try:
                v = float(row[col]) if pd.notna(row[col]) else None
            except:
                v = None
            row_data['values'][col] = v
        data.append(row_data)
    return data

def aggregate_values(fdf):
    result = {}
    for col in NUMERIC_INDICATORS:
        if col in fdf.columns:
            s = pd.to_numeric(fdf[col], errors='coerce')
            result[col] = round(float(s.mean()), 2) if not s.dropna().empty else None
    return result

# ==================== RUTAS ====================

@app.route('/')
def index():
    if df is None:
        return "Error: Dataset no cargado", 500
    deptos = get_unique(DEPTO_COL)
    years  = get_unique(YEAR_COL)
    zonas  = get_unique(ZONA_COL)
    return render_template('dashboard.html',
        deptos=deptos, years=years, zonas=zonas,
        indicators=NUMERIC_INDICATORS,
        indicator_labels=json.dumps(INDICATOR_LABELS)
    )

@app.route('/api/data', methods=['GET'])
def get_data():
    depto     = request.args.get('depto')
    year      = request.args.get('year')
    zona      = request.args.get('zona')
    indicator = request.args.get('indicator')

    filtered = filter_data(depto, year, zona, indicator)

    if filtered.empty:
        fallback = filter_data(depto, None, zona, indicator)
        if not fallback.empty:
            return jsonify({
                'success': True,
                'rows': len(fallback),
                'data': prepare_chart_data(fallback),
                'note': f'Sin datos para año {year}. Se muestran todos los años disponibles.'
            })
        return jsonify({'success': False, 'message': 'Sin datos para los filtros seleccionados', 'data': []})

    return jsonify({'success': True, 'rows': len(filtered), 'data': prepare_chart_data(filtered)})

@app.route('/api/filters', methods=['GET'])
def get_filters():
    if df is None:
        return jsonify({'error': 'Dataset no cargado'}), 500
    return jsonify({
        'deptos':   get_unique(DEPTO_COL),
        'years':    get_unique(YEAR_COL),
        'zonas':    get_unique(ZONA_COL),
        'indicators': NUMERIC_INDICATORS,
        'indicator_labels': INDICATOR_LABELS
    })

@app.route('/api/compare', methods=['POST'])
def compare():
    data  = request.get_json()
    d1    = data.get('depto1')
    d2    = data.get('depto2')
    year  = data.get('year')
    ind   = data.get('indicator')
    if not all([d1, d2, ind]):
        return jsonify({'error': 'Parámetros insuficientes'}), 400

    def build(dep):
        fdf = filter_data(dep, year, None, ind)
        if fdf.empty:
            fdf = filter_data(dep, None, None, ind)
            if fdf.empty:
                return []
            agg = aggregate_values(fdf)
            return [{'departamento': f'{dep} (promedio)', 'values': agg,
                     'note': f'Promedio calculado (sin datos para {year})'}]
        return prepare_chart_data(fdf)

    return jsonify({'depto1': {'name': d1, 'data': build(d1)},
                    'depto2': {'name': d2, 'data': build(d2)}})

@app.route('/api/statistics', methods=['GET'])
def statistics():
    if df is None:
        return jsonify({'error': 'Dataset no cargado'}), 500
    total_desertoras = int(df['Desertoras_Estimadas'].sum())
    total_nac_15_19  = int(df['Nacimientos_15_19'].sum())
    total_nac_10_14  = int(df['Nacimientos_10_14'].sum())
    avg_desercion    = round(float(df['Tasa_Desercion_Femenina'].mean()), 2)
    avg_fecundidad   = round(float(df['Tasa_Fecundidad_Adolescente'].mean()), 2)
    depto_mas_desercion = df.groupby(DEPTO_COL)['Tasa_Desercion_Femenina'].mean().idxmax()
    depto_mas_fec       = df.groupby(DEPTO_COL)['Tasa_Fecundidad_Adolescente'].mean().idxmax()
    missing_pct = round((df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100, 2)
    return jsonify({
        'total_registros':      len(df),
        'total_departamentos':  df[DEPTO_COL].nunique(),
        'periodo':              f"{df[YEAR_COL].min()}–{df[YEAR_COL].max()}",
        'total_desertoras':     total_desertoras,
        'total_nac_15_19':      total_nac_15_19,
        'total_nac_10_14':      total_nac_10_14,
        'avg_tasa_desercion':   avg_desercion,
        'avg_fecundidad':       avg_fecundidad,
        'depto_mayor_desercion': depto_mas_desercion,
        'depto_mayor_fecundidad': depto_mas_fec,
        'missing_data_pct':     missing_pct
    })

@app.route('/api/trend', methods=['GET'])
def trend():
    """Serie temporal por departamento para ambas tasas clave"""
    depto = request.args.get('depto')
    if not depto:
        return jsonify({'error': 'Se requiere departamento'}), 400
    fdf = df[df[DEPTO_COL].str.contains(depto, case=False, na=False)].sort_values(YEAR_COL)
    if fdf.empty:
        return jsonify({'error': 'Departamento no encontrado'}), 404
    result = {
        'departamento': depto,
        'years': fdf[YEAR_COL].tolist(),
        'desercion': fdf['Tasa_Desercion_Femenina'].tolist(),
        'fecundidad': fdf['Tasa_Fecundidad_Adolescente'].tolist(),
        'pobreza': fdf['Tasa_Pobreza'].tolist(),
        'cobertura_edu': fdf['Cobertura_Edu_Sexual'].tolist()
    }
    return jsonify(result)

@app.route('/api/correlation', methods=['GET'])
def correlation():
    """Correlación entre deserción y fecundidad por año"""
    results = []
    for year in sorted(df[YEAR_COL].unique()):
        sub = df[df[YEAR_COL] == year][['Tasa_Desercion_Femenina','Tasa_Fecundidad_Adolescente']].dropna()
        if len(sub) > 2:
            corr = round(float(sub.corr().iloc[0,1]), 4)
            results.append({'year': int(year), 'correlation': corr, 'n': len(sub)})
    return jsonify(results)

@app.errorhandler(404)
def not_found(e):
    return "404 - No encontrado", 404

@app.errorhandler(500)
def server_error(e):
    return "500 - Error del servidor", 500
def calcular_indice_riesgo(row):
    """
    Indice ponderado 0-100 con 4 variables del dataset.
    Pesos alineados con el objetivo especifico 5 del articulo.
    """
    # Normalizar cada variable a escala 0-1 sobre rangos reales Colombia
    d_norm  = min(row['Tasa_Desercion_Femenina'] / 10.0, 1.0)       # max ~10%
    f_norm  = min(row['Tasa_Fecundidad_Adolescente'] / 100.0, 1.0)  # max ~100 x1000
    p_norm  = min(row.get('Tasa_Pobreza', 50) / 80.0, 1.0)          # max ~80%
    e_norm  = 1 - min(row.get('Cobertura_Edu_Sexual', 50) / 100.0, 1.0)  # inverso
 
    # Pesos academicamente justificados
    indice = (d_norm * 0.35 + f_norm * 0.35 + p_norm * 0.15 + e_norm * 0.15) * 100
    return round(indice, 1)
 
 
def nivel_riesgo(indice):
    if indice >= 65: return 'Critico'
    if indice >= 45: return 'Alto'
    if indice >= 25: return 'Medio'
    return 'Bajo'
 
 
def color_riesgo(nivel):
    return {'Critico': '#c62828', 'Alto': '#e65100',
            'Medio':   '#f57f17', 'Bajo': '#2e7d32'}.get(nivel, '#607d8b')
 
 
def generar_recomendacion(row, nivel):
    """
    Recomendacion de politica publica personalizada segun perfil.
    Basada en el objetivo especifico 5 del articulo IEEE.
    """
    zona    = row.get('Zona', 'Mixta')
    cobert  = row.get('Cobertura_Edu_Sexual', 50)
    progr   = row.get('Programa_Retencion', 'No')
    fec     = row['Tasa_Fecundidad_Adolescente']
    deser   = row['Tasa_Desercion_Femenina']
 
    acciones = []
 
    if nivel == 'Critico':
        acciones.append('Intervencion intersectorial urgente MEN-MinSalud-secretarias departamentales.')
        if str(progr).lower() in ['no', 'false', '0', 'nan']:
            acciones.append('Implementar programa de retencion escolar con modalidad hibrida inmediatamente.')
        if cobert < 50:
            acciones.append('Desplegar brigadas moviles de educacion sexual en instituciones educativas.')
        if 'Rural' in str(zona) or 'rural' in str(zona):
            acciones.append('Habilitar aulas satelite y educacion a distancia para zonas de alta dispersion.')
 
    elif nivel == 'Alto':
        acciones.append('Fortalecer programas de prevencion del embarazo en colegios de secundaria.')
        if deser > 4.5:
            acciones.append('Ampliar cupos en programas de madres gestantes y lactantes en instituciones educativas.')
        if fec > 55:
            acciones.append('Articular con secretaria de salud para ampliar cobertura de salud reproductiva.')
 
    elif nivel == 'Medio':
        acciones.append('Monitorear indicadores trimestralmente via SIMAT para detectar deterioro.')
        acciones.append('Fortalecer red de apoyo psicosocial en instituciones educativas.')
        if str(progr).lower() in ['no', 'false', '0', 'nan']:
            acciones.append('Evaluar implementacion de programa piloto de retencion escolar.')
 
    else:  # Bajo
        acciones.append('Mantener programas vigentes y replicar buenas practicas en departamentos criticos.')
        acciones.append('Documentar estrategias exitosas para transferencia de conocimiento interterritorial.')
 
    return acciones
 
 
def predecir_2027(serie_valores, anios):
    """
    Regresion lineal simple sobre los 4 años disponibles.
    Retorna prediccion para 2027 con intervalo de confianza 95%.
    """
    if len(serie_valores) < 3:
        return None, None, None
 
    x = np.array(anios, dtype=float)
    y = np.array(serie_valores, dtype=float)
 
    slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, y)
    pred_2027 = round(slope * 2027 + intercept, 2)
 
    # Intervalo de confianza simplificado (±2*std_err * t_critico)
    n = len(x)
    t_crit = 2.776 if n == 4 else 3.182  # t al 95% para n=4 y n=3
    margen = round(t_crit * std_err, 2)
 
    return max(0, pred_2027), max(0, pred_2027 - margen), pred_2027 + margen
 
 
# ---------- endpoint ----------
 
@app.route('/api/riesgo', methods=['GET'])
def get_riesgo():
    """
    Modelo de clasificacion de riesgo y prediccion 2027.
 
    Parametros opcionales:
      - nivel: filtrar por nivel de riesgo (Critico / Alto / Medio / Bajo)
      - zona:  filtrar por zona (Rural / Mixta / Urbana)
 
    Respuesta:
      {
        "resumen": { conteos por nivel, stats },
        "departamentos": [ lista ordenada por indice desc ],
        "predicciones_2027": [ lista de predicciones lineales ]
      }
    """
    if df is None:
        return jsonify({'error': 'Dataset no cargado'}), 500
 
    filtro_nivel = request.args.get('nivel', None)
    filtro_zona  = request.args.get('zona',  None)
 
    # --- Paso 1: promedio 2023-2026 por departamento ---
    cols_agg = {
        'Tasa_Desercion_Femenina':    'mean',
        'Tasa_Fecundidad_Adolescente':'mean',
        'Desertoras_Estimadas':       'sum',
        'Nacimientos_15_19':          'sum',
        'Nacimientos_10_14':          'sum',
        'Cobertura_Edu_Sexual':       'mean',
        'Tasa_Pobreza':               'mean',
        'Indice_Vulnerabilidad':      'mean',
    }
    # Solo agregar columnas que existan en el df
    cols_agg = {k: v for k, v in cols_agg.items() if k in df.columns}
 
    # Zona y Programa_Retencion: primer valor por departamento
    df_prom = df.groupby(DEPTO_COL).agg(cols_agg).reset_index()
 
    for col in ['Zona', 'Programa_Retencion']:
        if col in df.columns:
            primeros = df.groupby(DEPTO_COL)[col].first().reset_index()
            df_prom = df_prom.merge(primeros, on=DEPTO_COL, how='left')
 
    # --- Paso 2: calcular indice y nivel ---
    df_prom['indice_riesgo'] = df_prom.apply(calcular_indice_riesgo, axis=1)
    df_prom['nivel_riesgo']  = df_prom['indice_riesgo'].apply(nivel_riesgo)
    df_prom['color']         = df_prom['nivel_riesgo'].apply(color_riesgo)
    df_prom['recomendaciones'] = df_prom.apply(
        lambda r: generar_recomendacion(r, r['nivel_riesgo']), axis=1
    )
 
    # --- Paso 3: prediccion 2027 por regresion lineal ---
    anios_disp = sorted(df[YEAR_COL].unique())
    predicciones = []
    for dept in df[DEPTO_COL].unique():
        serie = df[df[DEPTO_COL] == dept].sort_values(YEAR_COL)
        vals_d = serie['Tasa_Desercion_Femenina'].tolist()
        vals_f = serie['Tasa_Fecundidad_Adolescente'].tolist()
 
        pred_d, lo_d, hi_d = predecir_2027(vals_d, anios_disp)
        pred_f, lo_f, hi_f = predecir_2027(vals_f, anios_disp)
 
        nivel = df_prom[df_prom[DEPTO_COL] == dept]['nivel_riesgo'].values
        nivel = nivel[0] if len(nivel) else 'Medio'
 
        predicciones.append({
            'departamento': dept,
            'nivel_riesgo': nivel,
            'prediccion_desercion_2027': pred_d,
            'ic_inferior_desercion': round(lo_d, 2) if lo_d else None,
            'ic_superior_desercion': round(hi_d, 2) if hi_d else None,
            'prediccion_fecundidad_2027': pred_f,
            'ic_inferior_fecundidad': round(lo_f, 2) if lo_f else None,
            'ic_superior_fecundidad': round(hi_f, 2) if hi_f else None,
            'tendencia': 'Mejora' if (pred_d and pred_d < vals_d[-1]) else 'Deterioro',
        })
 
    # --- Paso 4: filtros opcionales ---
    resultado = df_prom.copy()
    if filtro_nivel:
        resultado = resultado[resultado['nivel_riesgo'] == filtro_nivel]
    if filtro_zona and 'Zona' in resultado.columns:
        resultado = resultado[resultado['Zona'].str.contains(filtro_zona, case=False, na=False)]
 
    # --- Paso 5: serializar ---
    depts_list = []
    for _, row in resultado.sort_values('indice_riesgo', ascending=False).iterrows():
        d = {
            'departamento':             row[DEPTO_COL],
            'indice_riesgo':            row['indice_riesgo'],
            'nivel_riesgo':             row['nivel_riesgo'],
            'color':                    row['color'],
            'tasa_desercion_prom':      round(row['Tasa_Desercion_Femenina'], 2),
            'tasa_fecundidad_prom':     round(row['Tasa_Fecundidad_Adolescente'], 1),
            'desertoras_acumuladas':    int(row.get('Desertoras_Estimadas', 0)),
            'nacimientos_adol_acum':    int(row.get('Nacimientos_15_19', 0) + row.get('Nacimientos_10_14', 0)),
            'cobertura_edu_sexual':     round(row.get('Cobertura_Edu_Sexual', 0), 1),
            'tasa_pobreza':             round(row.get('Tasa_Pobreza', 0), 1),
            'indice_vulnerabilidad':    round(row.get('Indice_Vulnerabilidad', 0), 3),
            'zona':                     str(row.get('Zona', 'N/D')),
            'programa_retencion':       str(row.get('Programa_Retencion', 'No')),
            'recomendaciones':          row['recomendaciones'],
        }
        depts_list.append(d)
 
    # Resumen por nivel
    conteos = df_prom['nivel_riesgo'].value_counts().to_dict()
 
    return jsonify({
        'success': True,
        'total_departamentos': len(df_prom),
        'filtros_aplicados': {'nivel': filtro_nivel, 'zona': filtro_zona},
        'resumen': {
            'critico': conteos.get('Critico', 0),
            'alto':    conteos.get('Alto', 0),
            'medio':   conteos.get('Medio', 0),
            'bajo':    conteos.get('Bajo', 0),
            'indice_promedio_nacional': round(df_prom['indice_riesgo'].mean(), 1),
            'dept_mas_critico': df_prom.loc[df_prom['indice_riesgo'].idxmax(), DEPTO_COL],
            'dept_menos_critico': df_prom.loc[df_prom['indice_riesgo'].idxmin(), DEPTO_COL],
        },
        'departamentos': depts_list,
        'predicciones_2027': sorted(predicciones, key=lambda x: x.get('prediccion_desercion_2027') or 0, reverse=True),
    })
if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Dashboard Deserción & Embarazo Adolescente – Colombia")
    print("="*60)
    print(f"  Dataset: {df.shape if df is not None else 'No cargado'}")
    print(f"  Período: 2023–2026")
    print(f"  Acceder en: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
