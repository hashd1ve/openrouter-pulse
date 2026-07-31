# OpenRouter Pulse — diseño

**Fecha:** 2026-07-31
**Estado:** aprobado
**Tesis:** los datos públicos de OpenRouter permiten clasificar cada modelo por el *tipo de trabajo* que realmente hace — agéntico, conversacional, extractivo o de salida pesada — usando únicamente la forma de su consumo de tokens. Nadie publica esa clasificación y se deriva sin coste de datos abiertos.

---

## 1. Contexto y motivación

OpenRouter expone públicamente, sin autenticación, más datos de los que su web muestra. El objetivo de este proyecto es construir un pipeline reproducible sobre esos datos y extraer de ellos una conclusión que no sea observable a simple vista.

El proyecto es a la vez un artefacto de ingeniería de datos (ingesta tolerante a fallos, modelado dimensional, validación) y un análisis (la huella de carga de trabajo).

## 2. Qué expone OpenRouter — verificado en vivo el 2026-07-31

### Endpoints documentados

| Endpoint | Contenido |
|---|---|
| `GET /api/v1/models` | 365 modelos: precios, `context_length`, modalidades, `supported_parameters`, `created` |
| `GET /api/v1/models/{author}/{slug}/endpoints` | Proveedores que sirven cada modelo |
| `GET /api/v1/providers` | Catálogo de proveedores |

### Endpoints no documentados (alimentan la web de rankings)

| Endpoint | Contenido |
|---|---|
| `GET /api/frontend/v1/rankings/models?view=day\|week\|month` | Agregado de uso por modelo y variante |
| `GET /api/frontend/v1/rankings/apps` | Top 20 apps por día/semana/mes |
| `GET /api/frontend/v1/stats/endpoint?permaslug=X&variant=Y` | Latencia y throughput p50–p99 por endpoint de proveedor |
| `GET /api/frontend/v1/rankings/tools`, `/rankings/images` | Leaderboards menores |

Estos endpoints no tienen contrato público. Pueden cambiar sin aviso. El diseño lo asume (§7).

### Hallazgo crítico: no existe serie temporal pública

La intuición inicial —que `rankings/models` devolvía una serie diaria— **es falsa**. Verificación con `deepseek/deepseek-v4-flash-20260423`:

| `view` | prompt tokens | requests |
|---|---|---|
| `day` | 1,09 T | 107 M |
| `week` | 7,08 T | 706 M |
| `month` | 23,95 T | 2.358 M |

El endpoint devuelve **una fila por (modelo, variante)** con el agregado de una ventana móvil. El campo `date` **no es un índice temporal**: es la última fecha con tráfico del modelo. Agrupar por él produciría un gráfico convincente y falso.

Dos consecuencias de diseño:

1. Capturar snapshots propios es la **única** vía para obtener serie temporal. El valor del dataset crece monótonamente con el tiempo.
2. Las tres ventanas anidadas permiten derivar tendencia **sin histórico previo** (§5.2).

### Campos vacíos en el feed público

`total_native_tokens_cached`, `total_native_tokens_reasoning`, `total_tool_calls` y `requests_with_tool_call_errors` están presentes en el esquema pero valen 0 para los 446 modelos. **No se construye nada sobre ellos.** Se ingieren igualmente, por si OpenRouter empieza a poblarlos.

### Dimensionamiento

- Barrido completo de stats por endpoint: ~365 peticiones, ~6 MB crudos, ~2 min secuencial
- Comprimido: ~0,6 MB/día
- Tablas de hechos normalizadas: ~440 filas/día de uso, ~2.500 de rendimiento

Cabe entero en un repositorio git sin infraestructura externa.

## 3. Alcance

**Dentro:**
- Ingesta diaria idempotente con manifest de ejecución
- Modelado dimensional en DuckDB + Parquet
- Métrica de huella de carga y clasificación en arquetipos
- Métrica de momentum corregida por edad del modelo
- Validación de calidad de datos que rompe el pipeline
- Tests unitarios, de contrato y de calidad
- Informe generado desde los datos
- Dashboard estático autocontenido (un solo HTML, SVG en línea, sin servidor ni dependencias)
- Métricas avanzadas: economía implícita, estructura de mercado (HHI/Gini), utilización de contexto, competencia entre proveedores, elasticidad precio, canibalización de variantes
- Estimadores estadísticos propios y verificados: Kaplan-Meier con censura, OLS con errores robustos HC1
- Cron diario en GitHub Actions

**Fuera, deliberadamente:**
- Detección de revisiones retroactivas de cifras. Saldría casi gratis de los datos que ya se guardan, pero no hace falta para la tesis y no tendría material hasta pasadas semanas.
- Orquestador dedicado (Airflow/Dagster). Para 0,6 MB/día sería un error de dimensionamiento.
- Base de datos servidor. El dataset cabe en memoria varias veces.
- Framework de dashboard (Streamlit/Dash). Se descartó tras evaluarlo: obliga a mantener un servidor vivo para algo cuyo destino natural es un enlace, y añade dependencias de runtime que envejecen. Un HTML autocontenido con SVG en línea se abre en cualquier sitio, sobrevive a una política de seguridad estricta y no tiene nada que actualizar.
- Utilización de capacidad de proveedor. `capacity_tpm` solo viene informado en 18 de 925 endpoints: no da para nada.

## 4. Arquitectura

```
data/raw/YYYY-MM-DD/*.json.gz   inmutable, byte a byte como vino de la API
      ↓  normalización + tipado
data/staging/*.parquet          una fila por hecho, tipos explícitos
      ↓  SQL sobre DuckDB
data/marts/*.parquet            dimensiones + hechos + marts
```

**Regla invariante: `raw` nunca se reescribe.** Si la lógica de transformación cambia, staging y marts se reconstruyen desde raw sin tocar la red. Esto permite corregir un error de análisis meses después sin haber perdido información.

### Componentes

| Componente | Responsabilidad | Depende de |
|---|---|---|
| `orpulse.client` | HTTP con reintentos, backoff, jitter y ritmo limitado | Red |
| `orpulse.ingest` | Escribe raw + manifest | `client` |
| `orpulse.transform` | raw → staging → marts | Ficheros locales |
| `orpulse/sql/marts.sql` | Huella de carga, arquetipos, momentum, dominancia | staging |
| `orpulse.quality` | Checks que rompen el pipeline | marts |
| `orpulse.report` | Genera `docs/FINDINGS.md` | marts |
| `app/` | Dashboard Streamlit | marts |

**DuckDB en vez de Postgres:** lee Parquet directamente, no necesita servidor, el repo se clona y funciona.

**SQL en vez de pandas para transformar:** revisable por cualquiera, se parece a lo que se escribe en producción, y evita el bug silencioso de un `merge` mal especificado.

## 5. Modelo de datos

**Decisión central: la clave temporal de los hechos es la fecha de captura, no el campo `date` de la API.** Ese campo pasa a ser el atributo descriptivo `source_last_activity_date`, porque eso es lo que significa.

### Dimensiones

- **`dim_model`** — SCD tipo 2 sobre `pricing` y `context_length`. Los precios cambian y capturar el cambio tiene valor propio. Incluye `created` (lanzamiento), necesario para §5.2.
- **`dim_endpoint`** — proveedor, región, cuantización, política de datos, `capacity_tpm`, precios por endpoint.

### Hechos

- **`fct_model_usage_snapshot`** — grano `(snapshot_date, usage_window, model_permaslug, variant)`, `usage_window ∈ {day, week, month}` (se llama `usage_window` y no `window` porque esta última es palabra reservada en DuckDB). Unicidad del grano verificada: 0 duplicados en 497 filas.
- **`fct_endpoint_perf_snapshot`** — grano `(snapshot_date, endpoint_id)`.
- **`fct_app_usage_snapshot`** — grano `(snapshot_date, usage_window, app_id)`.

### Marts

- **`mart_model_fingerprint`** — ratio P:C, tokens por request, arquetipo, momentum corregido, tramo de volumen.

### 5.1 Huella de carga de trabajo

Dos señales derivadas del uso agregado:

```
pc_ratio           = total_prompt_tokens / total_completion_tokens
tokens_per_request = (total_prompt_tokens + total_completion_tokens) / count
```

`pc_ratio` mide cuánto contexto consume el modelo por cada token que produce. `tokens_per_request` mide el tamaño de la interacción. Juntas separan regímenes de uso que la cuota de mercado esconde: dos modelos con el mismo volumen de tokens pueden estar haciendo trabajos completamente distintos.

**Los cortes entre arquetipos se ajustan una vez contra la distribución observada, se congelan y se declaran explícitamente**, no se derivan por clustering. Razón: k-means sobre dos dimensiones con ~400 puntos produce clusters cuya identidad cambia entre ejecuciones, y un cluster que cambia de significado cada día es inservible en una serie temporal. En su lugar se fijan umbrales estables y se **mide** la estabilidad de la asignación en el tiempo (proporción de modelos que cambian de arquetipo entre capturas consecutivas), que es la pregunta que realmente importa.

**Valores ajustados (2026-07-31, congelados).** Ambos ejes resultaron genuinamente bimodales al ponderar la densidad por volumen de tokens, así que los cortes son los mínimos entre modas, no números redondos:

| Eje | Moda 1 | Moda 2 | Valle → corte |
|---|---|---|---|
| `pc_ratio` | 17,1 | 75,9 | **26,6** |
| `tokens_per_request` | 10.457 | 61.734 | **18.607** |

Esa bimodalidad es en sí misma el hallazgo: el mercado no es un continuo de estilos de uso, son dos poblaciones.

El tercer corte, `pc_ratio < 2`, es **semántico y no ajustado** — ahí no hay valle, la región simplemente está vacía. Al inspeccionarla resultó estar dominada por modelos de salida de imagen, no por generación de texto, de ahí que el arquetipo se llame `output_heavy` y no `generative` como se planteó inicialmente.

El titular es insensible al corte exacto: la cuota agéntica va de 70,8 % (corte en 20) a 62,6 % (corte en 40).

### 5.2 Momentum corregido por edad

```
effective_days = min(30, días desde created)
avg_daily      = month_tokens / effective_days
momentum       = day_tokens / avg_daily
```

**La corrección por edad no es opcional.** Sin ella, la media mensual divide entre 30 días aunque el modelo lleve cuatro vivos, y todo lanzamiento reciente aparece con momentum inflado por pura aritmética. El análisis "descubriría" que los modelos nuevos crecen, que es una tautología.

Además, el momentum solo se reporta si el modelo es *calificable*:

```
is_ratable = created_ts IS NOT NULL
             AND effective_days >= 7
             AND month_requests >= 1_000_000
```

La primera condición se añadió durante la implementación. 144 model-variants —casi todos modelos de embeddings, ausentes de `/api/v1/models`— no tienen fecha de lanzamiento. Asignarles los 30 días por defecto publicaría un momentum **sin corregir** presentándolo como corregido, que es peor que no publicarlo. Son el 1,75 % de los tokens.

Los modelos con menos de una semana de vida se marcan como "demasiado nuevos para calificar" en lugar de recibir una cifra sin sentido. Los de tráfico residual quedan fuera porque en ellos el ratio es ruido: la distribución observada tiene mediana 0,98 y p25–p75 de 0,74–1,23, pero los extremos (0,00x y 12,07x) están dominados por modelos con volumen despreciable.

### 5.3 Advertencias grabadas en el esquema

**`fct_endpoint_perf_snapshot` es una muestra, no un agregado.** La API devuelve una ventana móvil de 30 minutos (`window_minutes: 30`). Una captura diaria mide media hora concreta, no el día. La columna `window_minutes` viaja con el dato y el mart nunca promedia entre snapshots sin ponderar por `request_count`.

**Suelo de volumen para comparar endpoints.** El p10 de `stat_request_count` son 45 peticiones; unos percentiles sobre eso son ruido, no medición. Los endpoints por debajo de 100 peticiones en la ventana quedan fuera de la comparación de dominancia. El resultado es insensible al umbral: la proporción de endpoints dominados se mantiene en 53–55 % para cualquier suelo entre 0 y 1.000, y esa insensibilidad se reporta en lugar de ocultarse.

## 6. Manejo de errores

| Modo de fallo | Respuesta |
|---|---|
| Parcial (404 en un modelo — observado) | Registrar en el manifest con su código, continuar el barrido |
| Total del feed | Fallar ruidosamente y **no escribir nada** |
| Degradación silenciosa | Check de cobertura (§7) |

**Regla dura: nunca escribir un snapshot incompleto marcado como completo.** La escritura del manifest es lo último que ocurre; su ausencia marca el día como fallido.

**Snapshot ausente ≠ snapshot vacío.** Sin fichero = no se ejecutó. Fichero con cero filas = se ejecutó y no había datos. Confundirlos convierte una caída del cron en una caída del mercado.

**El manifest por ejecución** registra timestamp UTC, endpoints solicitados, cuáles respondieron, cuáles fallaron con qué código, bytes y duración. Sin él, un hueco en la serie dentro de tres meses es indistinguible de un día sin tráfico.

**Cortesía de red:** reintentos con backoff exponencial y jitter, ritmo limitado y `User-Agent` identificable con contacto. Los endpoints no están documentados; un barrido educado y firmado es defendible, un scraper agresivo en los logs de acceso de la empresa no lo es.

## 7. Calidad de datos

Checks que rompen el pipeline:

| Check | Detecta |
|---|---|
| Unicidad del grano | Duplicados por reejecución |
| No nulos en claves | Corrupción de parseo |
| Tokens y requests ≥ 0 | Valores imposibles |
| **`day ≤ week ≤ month`** por (modelo, variante) | Cambio de semántica en la API |
| Cobertura dentro de ±20% del snapshot previo | Fallo parcial silencioso |
| Frescura < 48 h | Cron muerto |

El check de ventanas anidadas es un **invariante semántico**, no de formato. Es exactamente el que habría detectado automáticamente el malentendido sobre la serie temporal descrito en §2.

## 8. Tests

Tres niveles, deliberadamente separados:

1. **Unitarios** — parseo y transformación contra fixtures JSON congelados. Sin red, deterministas.
2. **De contrato** — contra la API real, en un job aparte que **no bloquea** la ingesta. Verifica que el esquema sigue siendo el esperado.
3. **De calidad** — sobre los marts, en cada ingesta.

Separar 1 de 2 es intencionado: si el test de contrato viviera en la suite normal, un cambio de OpenRouter pondría el repo en rojo y acabaría desactivándose. Aislado, el rojo comunica lo correcto.

## 9. Entregables

| Comando | Salida |
|---|---|
| `make ingest` | Snapshot crudo + manifest |
| `make build` | staging + marts, con checks de calidad |
| `make report` | `docs/FINDINGS.md` regenerado desde los datos |
| `make app` | Dashboard Streamlit |
| `make test` | Unitarios + calidad |
| `make contract` | Test de contrato contra la API real |

El informe se regenera desde los marts en cada build, de modo que las cifras publicadas nunca se desincronizan del dataset. Es **función pura de los datos**: mismos marts, fichero byte a byte idéntico. No lleva marca de tiempo de generación, deliberadamente, porque CI comprueba que el informe commiteado coincide con el que producen los datos commiteados y un reloj haría imposible esa comprobación.

**CI:** un workflow diario ejecuta ingesta, build y report, y commitea los Parquet. Un segundo workflow ejecuta el test de contrato de forma independiente.

## 10. Criterios de éxito

1. `git clone && make all` reproduce el pipeline completo desde cero sin secretos.
2. Todo hueco en la serie tiene causa documentada en un manifest.
3. La clasificación en arquetipos es estable entre capturas consecutivas (< 5 % de reasignaciones fuera de las fronteras).
4. El informe contiene al menos una afirmación cuantificada que no sea observable en la web pública de OpenRouter.
