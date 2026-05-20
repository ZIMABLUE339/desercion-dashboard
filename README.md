# Dashboard: Deserción Escolar Femenina & Embarazo Adolescente en Colombia
### Período 2023–2026 | Edwin Rodrigo Pedraza Quintero | U. Cundinamarca, Ext. Chía

---

## ¿Qué hace este proyecto?

Dashboard web interactivo para analizar la relación entre la **tasa de fecundidad adolescente** y la **tasa de deserción escolar femenina** en los 32 departamentos de Colombia, período 2023–2026.

Aplica metodología **SEMMA**: Selección → Exploración → Modelado → Visualización → Evaluación.

---

## Estructura

```
desercion_proyecto/
├── app.py                  # Backend Flask + API REST
├── requirements.txt
├── README.md
├── data/
│   └── desercion_embarazo.csv   # Dataset sintético (128 registros, 13 variables)
└── templates/
    └── dashboard.html           # Frontend Bootstrap + Chart.js
```

---

## Instalación y ejecución

```bash
# 1. Clonar / descomprimir el proyecto
cd desercion_proyecto

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python app.py

# 5. Abrir en navegador
# http://localhost:5000
```

---

## Variables del dataset

| Variable | Descripción |
|---|---|
| Departamento | Nombre del departamento |
| Año | 2023, 2024, 2025 o 2026 |
| Zona | Rural / Mixta / Urbana |
| Tasa_Desercion_Femenina | % desertoras / matriculadas (secundaria) |
| Tasa_Fecundidad_Adolescente | Nacimientos x 1.000 mujeres 15–19 |
| Matriculadas_Secundaria | Total mujeres matriculadas en secundaria |
| Desertoras_Estimadas | Número estimado de desertoras |
| Nacimientos_10_14 | Nacimientos de niñas 10–14 años |
| Nacimientos_15_19 | Nacimientos de adolescentes 15–19 años |
| Cobertura_Edu_Sexual | % colegios con educación sexual activa |
| Tasa_Pobreza | Tasa de pobreza multidimensional (%) |
| Programa_Retencion | ¿Tiene programa de retención escolar? |
| Indice_Vulnerabilidad | Índice 0–1 basado en perfil departamental |

---

## API Endpoints

| Endpoint | Método | Descripción |
|---|---|---|
| `/` | GET | Dashboard principal |
| `/api/data` | GET | Datos filtrados (depto, year, zona, indicator) |
| `/api/filters` | GET | Opciones disponibles de filtros |
| `/api/statistics` | GET | KPIs globales del dataset |
| `/api/compare` | POST | Comparación entre dos departamentos |
| `/api/trend` | GET | Serie temporal por departamento |
| `/api/correlation` | GET | Coeficiente de correlación por año |

---

## Nota sobre los datos

El dataset es **sintético** con base en patrones reales reportados por el DANE y el MEN para 2020–2023.
Para el trabajo de investigación final, reemplazar `data/desercion_embarazo.csv` con los datos reales del SIMAT y DANE-EEVV siguiendo la misma estructura de columnas.

---

## Fuentes oficiales para reemplazar con datos reales

- **SIMAT** (deserción por municipio, sexo y grado): [datos.gov.co](https://datos.gov.co) → buscar "deserción escolar SIMAT"
- **DANE Estadísticas Vitales** (nacimientos por edad madre): [datos.gov.co](https://datos.gov.co) → buscar "Estadísticas Vitales Nacimientos"
- **Microdatos EEVV 2022**: [microdatos.dane.gov.co](https://microdatos.dane.gov.co)
