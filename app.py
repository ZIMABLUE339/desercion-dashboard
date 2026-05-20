"""
Dashboard: Embarazo Adolescente y Deserción Escolar Femenina en Colombia
Período 2023–2026 | Metodología SEMMA
"""
from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
from datetime import datetime

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

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Dashboard Deserción & Embarazo Adolescente – Colombia")
    print("="*60)
    print(f"  Dataset: {df.shape if df is not None else 'No cargado'}")
    print(f"  Período: 2023–2026")
    print(f"  Acceder en: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
