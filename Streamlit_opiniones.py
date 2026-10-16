
import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# LIBRERÍAS OPCIONALES PARA NUBE DE PALABRAS
# =====================================================
try:
    from wordcloud import WordCloud, STOPWORDS
    import matplotlib.pyplot as plt
    NUBE_DISPONIBLE = True
except ImportError:
    NUBE_DISPONIBLE = False

# =====================================================
# CONFIGURACIÓN
# =====================================================
st.set_page_config(
    page_title="HITSS | Data Analytics",
    page_icon="👥",
    layout="wide"
)

AZUL = "#073B75"
AZUL_CLARO = "#1464A5"
ROJO = "#D92332"
FONDO = "#F4F7FB"

COLORES_NPS = {
    "Promotores": "#16803C",
    "Pasivos": "#E5A000",
    "Detractores": ROJO
}

ORDEN_NPS = ["Detractores", "Pasivos", "Promotores"]

RUTA_ARCHIVO = (
    r"C:\Users\juanf\Downloads"
    r"\Prueba_Tecnica_Analista_Datos_Experiencia_clasificado_resultados.xlsx"
)

# =====================================================
# CARGA DE DATOS
# =====================================================
@st.cache_data
def cargar_datos(ruta):
    return pd.read_excel(ruta)


try:
    df = cargar_datos(RUTA_ARCHIVO)
except Exception as e:
    st.error(f"No fue posible cargar el archivo Excel: {e}")
    st.stop()

# =====================================================
# VALIDACIÓN Y PREPARACIÓN
# =====================================================
columnas_obligatorias = [
    "fecha",
    "calificación_nps",
    "tipo_nps"
]

faltantes = [
    c for c in columnas_obligatorias
    if c not in df.columns
]

if faltantes:
    st.error(
        "Faltan columnas obligatorias: "
        + ", ".join(faltantes)
    )
    st.stop()

df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce",
    dayfirst=True
)

df["calificación_nps"] = pd.to_numeric(
    df["calificación_nps"],
    errors="coerce"
)

mapa_nps = {
    "promotor": "Promotores",
    "promotores": "Promotores",
    "pasivo": "Pasivos",
    "pasivos": "Pasivos",
    "detractor": "Detractores",
    "detractores": "Detractores"
}

df["tipo_nps"] = (
    df["tipo_nps"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(mapa_nps)
)

DIMENSIONES = [
    "motivo_contacto",
    "región",
    "canal",
    "subcategoria",
    "segmento",
    "sentimiento"
]

for col in DIMENSIONES:
    if col in df.columns:
        df[col] = (
            df[col]
            .fillna("Sin dato")
            .astype(str)
            .str.strip()
            .replace("", "Sin dato")
        )

# =====================================================
# FUNCIONES AUXILIARES
# =====================================================
def obtener_datos_nps(datos):
    return datos[
        datos["tipo_nps"].isin(ORDEN_NPS)
    ].copy()


def analizar_dimension(datos, columna, categoria_nps):
    temporal = datos.copy()

    temporal["_caso"] = (
        temporal["tipo_nps"] == categoria_nps
    ).astype(int)

    resumen = (
        temporal.groupby(columna, dropna=False)
        .agg(
            Respuestas=("tipo_nps", "size"),
            Casos=("_caso", "sum")
        )
        .reset_index()
        .rename(columns={columna: "Categoría"})
    )

    resumen["Porcentaje dentro del grupo (%)"] = (
        resumen["Casos"]
        / resumen["Respuestas"]
        * 100
    )

    total_casos = resumen["Casos"].sum()

    if total_casos > 0:
        resumen["Participación en los casos (%)"] = (
            resumen["Casos"] / total_casos * 100
        )
    else:
        resumen["Participación en los casos (%)"] = 0.0

    return resumen.sort_values(
        "Casos",
        ascending=False
    )


def calcular_resumen_nps(datos):
    conteos = (
        datos["tipo_nps"]
        .value_counts()
        .reindex(ORDEN_NPS, fill_value=0)
    )

    total = int(conteos.sum())

    if total == 0:
        return conteos, 0, 0, 0, 0

    pct_promotores = conteos["Promotores"] / total * 100
    pct_pasivos = conteos["Pasivos"] / total * 100
    pct_detractores = conteos["Detractores"] / total * 100

    nps = pct_promotores - pct_detractores

    return (
        conteos,
        pct_promotores,
        pct_pasivos,
        pct_detractores,
        nps
    )


# =====================================================
# ESTILOS
# =====================================================
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {FONDO};
        }}

        [data-testid="stSidebar"] {{
            background-color: {AZUL};
        }}

        [data-testid="stSidebar"] * {{
            color: white;
        }}

        .encabezado {{
            background: linear-gradient(
                100deg, {AZUL}, {AZUL_CLARO}
            );
            color: white;
            padding: 25px;
            border-radius: 12px;
            border-bottom: 5px solid {ROJO};
            margin-bottom: 25px;
        }}

        .encabezado h1,
        .encabezado p {{
            color: white;
        }}

        div[data-testid="stMetric"] {{
            background-color: white;
            padding: 16px;
            border-radius: 10px;
            border-top: 4px solid {AZUL};
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# ENCABEZADO
# =====================================================
st.markdown(
    """
    <div class="encabezado">
        <h1>HITSS | Data Analytics</h1>
        <p>Panel ejecutivo de análisis de resultados</p>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# NAVEGACIÓN
# =====================================================
with st.sidebar:
    st.title("HITSS")
    st.markdown("### Panel de análisis")
    st.divider()

    seccion = st.radio(
        "Selecciona una sección",
        [
            "Resumen ejecutivo",
            "Exploración de datos",
            "Calidad de datos",
            "Base de datos",
            "Evolución del NPS",
            "Diagnóstico y mejoras",
            "Comparativo"
        ]
    )

# =====================================================
# 1. RESUMEN EJECUTIVO
# =====================================================
if seccion == "Resumen ejecutivo":

    st.subheader("Resumen ejecutivo")

    total_registros = len(df)
    total_variables = len(df.columns)
    duplicados = int(df.duplicated().sum())
    total_celdas = df.size
    total_faltantes = int(df.isna().sum().sum())

    completitud = (
        (1 - total_faltantes / total_celdas) * 100
        if total_celdas > 0 else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total registros", f"{total_registros:,}")
    c2.metric("Variables", f"{total_variables:,}")
    c3.metric("Completitud", f"{completitud:.1f}%")
    c4.metric("Duplicados", f"{duplicados:,}")

    st.divider()
    st.subheader("Vista previa de los datos")

    st.dataframe(
        df.head(10),
        use_container_width=True
    )

    datos_nps = obtener_datos_nps(df)

    if not datos_nps.empty:
        conteos, pct_prom, pct_pas, pct_det, nps = (
            calcular_resumen_nps(datos_nps)
        )

        st.subheader("Indicadores generales de NPS")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Respuestas válidas NPS", f"{len(datos_nps):,}")
        c2.metric("Promotores", f"{int(conteos['Promotores']):,}")
        c3.metric("Detractores", f"{int(conteos['Detractores']):,}")
        c4.metric("NPS total", f"{nps:.2f}")

# =====================================================
# 2. EXPLORACIÓN DE DATOS
# =====================================================
elif seccion == "Exploración de datos":

    st.subheader("Exploración de datos")

    numericas = df.select_dtypes(
        include="number"
    ).columns.tolist()

    categoricas = df.select_dtypes(
        include=["object", "category", "bool", "string"]
    ).columns.tolist()

    if numericas:
        variable = st.selectbox(
            "Selecciona una variable numérica",
            numericas
        )

        fig = px.histogram(
            df,
            x=variable,
            title=f"Distribución de {variable}",
            color_discrete_sequence=[AZUL]
        )

        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    if categoricas:
        categoria = st.selectbox(
            "Selecciona una variable categórica",
            categoricas
        )

        conteos = (
            df[categoria]
            .fillna("Sin dato")
            .astype(str)
            .value_counts()
            .head(15)
            .rename_axis(categoria)
            .reset_index(name="Cantidad")
        )

        fig = px.bar(
            conteos.sort_values("Cantidad"),
            x="Cantidad",
            y=categoria,
            orientation="h",
            title=f"Distribución por {categoria}",
            color_discrete_sequence=[ROJO]
        )

        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 3. CALIDAD DE DATOS
# =====================================================
elif seccion == "Calidad de datos":

    st.subheader("Calidad de datos")

    calidad = pd.DataFrame({
        "Variable": df.columns,
        "Tipo de dato": [
            str(df[c].dtype) for c in df.columns
        ],
        "Valores faltantes": [
            int(df[c].isna().sum()) for c in df.columns
        ],
        "Porcentaje faltante": [
            round(df[c].isna().mean() * 100, 2)
            for c in df.columns
        ],
        "Valores únicos": [
            int(df[c].nunique()) for c in df.columns
        ]
    })

    st.dataframe(
        calidad,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Resumen estadístico")

    st.dataframe(
        df.describe(include="all").T,
        use_container_width=True
    )

    st.subheader("Validación de calificaciones NPS")

    calificaciones = df["calificación_nps"].dropna()

    st.write(
        f"Calificaciones válidas: {len(calificaciones):,}"
    )

    fuera_rango = (
        ~calificaciones.between(0, 10)
    ).sum()

    st.write(
        f"Calificaciones fuera del rango 0–10: {fuera_rango:,}"
    )

    st.caption(
        "Regla esperada: 0–6 detractores, 7–8 pasivos y "
        "9–10 promotores. Verifica que tipo_nps coincida "
        "con calificación_nps."
    )

# =====================================================
# 4. BASE DE DATOS
# =====================================================
elif seccion == "Base de datos":

    st.subheader("Base de datos")

    busqueda = st.text_input("Buscar registros")
    df_filtrado = df.copy()

    if busqueda:
        mascara = df.astype(str).apply(
            lambda columna: columna.str.contains(
                busqueda,
                case=False,
                regex=False,
                na=False
            )
        ).any(axis=1)

        df_filtrado = df.loc[mascara]

    st.caption(f"Registros encontrados: {len(df_filtrado):,}")

    st.dataframe(
        df_filtrado,
        use_container_width=True,
        height=450
    )

    st.download_button(
        "Descargar datos en CSV",
        data=df_filtrado.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="HITSS_datos_filtrados.csv",
        mime="text/csv"
    )

# =====================================================
# 5. EVOLUCIÓN DIARIA Y MENSUAL DEL NPS
# =====================================================
elif seccion == "Evolución del NPS":

    st.subheader("Evolución del NPS")

    datos_nps = obtener_datos_nps(df)
    datos_nps = datos_nps.dropna(subset=["fecha"])

    if datos_nps.empty:
        st.warning(
            "No existen registros con fechas y categorías NPS válidas."
        )
        st.stop()

    c1, c2 = st.columns(2)

    fecha_min = datos_nps["fecha"].min().date()
    fecha_max = datos_nps["fecha"].max().date()

    with c1:
        fecha_inicio = st.date_input(
            "Fecha inicial",
            value=fecha_min,
            min_value=fecha_min,
            max_value=fecha_max,
            key="nps_inicio"
        )

    with c2:
        fecha_fin = st.date_input(
            "Fecha final",
            value=fecha_max,
            min_value=fecha_min,
            max_value=fecha_max,
            key="nps_fin"
        )

    if fecha_inicio > fecha_fin:
        st.error("La fecha inicial no puede ser posterior a la final.")
        st.stop()

    datos_nps = datos_nps[
        (datos_nps["fecha"].dt.date >= fecha_inicio)
        & (datos_nps["fecha"].dt.date <= fecha_fin)
    ]

    if datos_nps.empty:
        st.warning("No hay respuestas en el rango seleccionado.")
        st.stop()

    periodicidad = st.radio(
        "Periodicidad",
        ["Diaria", "Mensual"],
        horizontal=True
    )

    if periodicidad == "Diaria":
        datos_nps["periodo"] = datos_nps["fecha"].dt.floor("D")
    else:
        datos_nps["periodo"] = (
            datos_nps["fecha"].dt.to_period("M").dt.to_timestamp()
        )

    composicion = (
        datos_nps.groupby(["periodo", "tipo_nps"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=ORDEN_NPS, fill_value=0)
        .sort_index()
    )

    porcentajes = composicion.div(
        composicion.sum(axis=1), axis=0
    ) * 100

    resultado = porcentajes.rename(columns={
        "Promotores": "Promotores (%)",
        "Pasivos": "Pasivos (%)",
        "Detractores": "Detractores (%)"
    })

    resultado["NPS"] = (
        porcentajes["Promotores"]
        - porcentajes["Detractores"]
    )
    resultado["Respuestas"] = composicion.sum(axis=1)

    ultimo = resultado.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NPS último periodo", f"{ultimo['NPS']:.2f}")
    c2.metric("Promotores", f"{ultimo['Promotores (%)']:.1f}%")
    c3.metric("Pasivos", f"{ultimo['Pasivos (%)']:.1f}%")
    c4.metric("Detractores", f"{ultimo['Detractores (%)']:.1f}%")

    st.divider()
    st.subheader("Evolución del NPS")

    fig_nps = px.line(
        resultado.reset_index(),
        x="periodo",
        y="NPS",
        markers=True,
        title=f"Evolución {periodicidad.lower()} del NPS",
        color_discrete_sequence=[AZUL]
    )

    fig_nps.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray"
    )

    fig_nps.update_layout(
        template="plotly_white",
        yaxis_title="NPS (puntos)",
        xaxis_title="Periodo",
        yaxis_range=[-100, 100],
        hovermode="x unified"
    )

    st.plotly_chart(fig_nps, use_container_width=True)

    st.subheader("Composición porcentual")

    comp_larga = (
        porcentajes.reset_index()
        .melt(
            id_vars="periodo",
            var_name="Tipo",
            value_name="Porcentaje"
        )
    )

    fig_comp = px.bar(
        comp_larga,
        x="periodo",
        y="Porcentaje",
        color="Tipo",
        barmode="stack",
        category_orders={"Tipo": ORDEN_NPS},
        color_discrete_map=COLORES_NPS,
        title="Composición de las respuestas"
    )

    fig_comp.update_layout(
        template="plotly_white",
        yaxis_range=[0, 100],
        yaxis_title="Porcentaje (%)"
    )

    st.plotly_chart(fig_comp, use_container_width=True)

    st.subheader("Volumen de respuestas")

    volumen = (
        composicion.reset_index()
        .melt(
            id_vars="periodo",
            var_name="Tipo",
            value_name="Cantidad"
        )
    )

    fig_vol = px.bar(
        volumen,
        x="periodo",
        y="Cantidad",
        color="Tipo",
        barmode="stack",
        category_orders={"Tipo": ORDEN_NPS},
        color_discrete_map=COLORES_NPS,
        title="Encuestas por periodo"
    )

    fig_vol.update_layout(template="plotly_white")
    st.plotly_chart(fig_vol, use_container_width=True)

    tabla = resultado.reset_index().rename(
        columns={"periodo": "Periodo"}
    )

    tabla["Periodo"] = tabla["Periodo"].dt.strftime(
        "%Y-%m-%d" if periodicidad == "Diaria" else "%Y-%m"
    )

    st.subheader("Tabla de resultados")
    st.dataframe(
        tabla.round(2),
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Descargar resultados NPS",
        data=tabla.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"HITSS_NPS_{periodicidad.lower()}.csv",
        mime="text/csv"
    )

# =====================================================
# 6. DIAGNÓSTICO Y MEJORAS
# =====================================================
elif seccion == "Diagnóstico y mejoras":

    st.subheader("Diagnóstico y oportunidades de mejora")

    st.write(
        "Identifica causas recurrentes de insatisfacción, "
        "segmentos críticos y oportunidades de mejora."
    )

    datos = obtener_datos_nps(df)

    if datos.empty:
        st.warning("No existen respuestas con categorías NPS válidas.")
        st.stop()

    total = len(datos)
    conteos, pct_prom, pct_pas, pct_det, nps_total = (
        calcular_resumen_nps(datos)
    )

    detractores = int(conteos["Detractores"])
    pasivos = int(conteos["Pasivos"])
    promotores = int(conteos["Promotores"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Respuestas válidas", f"{total:,}")
    c2.metric("Detractores", f"{detractores:,}", f"{pct_det:.1f}%")
    c3.metric("Pasivos", f"{pasivos:,}", f"{pct_pas:.1f}%")
    c4.metric("Promotores", f"{promotores:,}", f"{pct_prom:.1f}%")

    tabs = st.tabs([
        "Detractores",
        "Causas recurrentes",
        "Clientes pasivos",
        "Nube de palabras"
    ])

    # ---------------------------------------------
    # TAB 1: DETRACTORES
    # ---------------------------------------------
    with tabs[0]:

        st.markdown("### ¿Dónde se concentra la insatisfacción?")

        dimensiones = [
            c for c in [
                "motivo_contacto", "región", "canal",
                "subcategoria", "segmento"
            ]
            if c in datos.columns
        ]

        if dimensiones:
            dimension = st.selectbox(
                "Analizar detractores por",
                dimensiones,
                key="dim_detractores"
            )

            resumen = analizar_dimension(
                datos, dimension, "Detractores"
            )

            st.dataframe(
                resumen.head(15).round(2),
                use_container_width=True,
                hide_index=True
            )

            top = resumen.head(10).sort_values("Casos")

            fig = px.bar(
                top,
                x="Casos",
                y="Categoría",
                orientation="h",
                text="Casos",
                title=f"Categorías con más detractores: {dimension}",
                color_discrete_sequence=[ROJO],
                hover_data=[
                    "Respuestas",
                    "Porcentaje dentro del grupo (%)",
                    "Participación en los casos (%)"
                ]
            )

            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                "El porcentaje dentro del grupo indica qué proporción "
                "de sus respuestas son detractoras. La participación "
                "indica qué porcentaje de todos los detractores "
                "pertenece a esa categoría."
            )
        else:
            st.info("No hay dimensiones disponibles.")

    # ---------------------------------------------
    # TAB 2: CAUSAS RECURRENTES
    # ---------------------------------------------
    with tabs[1]:

        st.markdown("### ¿Qué problemas se repiten?")

        dimensiones_causas = [
            c for c in ["motivo_contacto", "subcategoria"]
            if c in datos.columns
        ]

        datos_det = datos[
            datos["tipo_nps"] == "Detractores"
        ].copy()

        if dimensiones_causas and not datos_det.empty:

            causa_col = st.selectbox(
                "Seleccionar dimensión de causa",
                dimensiones_causas,
                key="causa_col"
            )

            ranking = (
                datos_det.groupby(causa_col, dropna=False)
                .size()
                .reset_index(name="Cantidad")
                .rename(columns={causa_col: "Causa"})
                .sort_values("Cantidad", ascending=False)
            )

            ranking["Participación (%)"] = (
                ranking["Cantidad"] / len(datos_det) * 100
            )

            st.dataframe(
                ranking.head(15).round(2),
                use_container_width=True,
                hide_index=True
            )

            fig = px.bar(
                ranking.head(10).sort_values("Cantidad"),
                x="Cantidad",
                y="Causa",
                orientation="h",
                text="Cantidad",
                title="Principales causas entre detractores",
                color_discrete_sequence=[ROJO]
            )

            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

            if "comentario" in datos_det.columns:

                causa_elegida = st.selectbox(
                    "Consultar comentarios de una causa",
                    ranking["Causa"].tolist(),
                    key="causa_comentario"
                )

                comentarios = datos_det[
                    datos_det[causa_col].astype(str)
                    == str(causa_elegida)
                ]

                columnas_comentarios = [
                    c for c in [
                        "fecha", "región", "canal",
                        causa_col, "comentario"
                    ]
                    if c in comentarios.columns
                ]

                comentarios = comentarios[columnas_comentarios]

                st.dataframe(
                    comentarios.head(100),
                    use_container_width=True,
                    hide_index=True
                )

                st.download_button(
                    "Descargar comentarios de detractores",
                    data=comentarios.to_csv(
                        index=False
                    ).encode("utf-8-sig"),
                    file_name="HITSS_comentarios_detractores.csv",
                    mime="text/csv"
                )

        else:
            st.info(
                "No hay detractores o faltan las columnas de causas."
            )

    # ---------------------------------------------
    # TAB 3: CLIENTES PASIVOS
    # ---------------------------------------------
    with tabs[2]:

        st.markdown("### ¿Cómo mejorar la experiencia de los pasivos?")

        datos_pasivos = datos[
            datos["tipo_nps"] == "Pasivos"
        ].copy()

        dimensiones_pasivos = [
            c for c in [
                "motivo_contacto", "región", "canal",
                "subcategoria", "segmento"
            ]
            if c in datos_pasivos.columns
        ]

        if not datos_pasivos.empty and dimensiones_pasivos:

            dimension_pasivos = st.selectbox(
                "Analizar clientes pasivos por",
                dimensiones_pasivos,
                key="dim_pasivos"
            )

            ranking_pasivos = (
                datos_pasivos.groupby(
                    dimension_pasivos, dropna=False
                )
                .size()
                .reset_index(name="Cantidad")
                .rename(
                    columns={dimension_pasivos: "Categoría"}
                )
                .sort_values("Cantidad", ascending=False)
            )

            ranking_pasivos["Participación (%)"] = (
                ranking_pasivos["Cantidad"]
                / len(datos_pasivos) * 100
            )

            st.dataframe(
                ranking_pasivos.head(15).round(2),
                use_container_width=True,
                hide_index=True
            )

            fig = px.bar(
                ranking_pasivos.head(10).sort_values("Cantidad"),
                x="Cantidad",
                y="Categoría",
                orientation="h",
                text="Cantidad",
                title="Principales grupos de clientes pasivos",
                color_discrete_sequence=["#E5A000"]
            )

            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

            dimensiones_comp = [
                c for c in ["motivo_contacto", "canal", "región"]
                if c in datos.columns
            ]

            if dimensiones_comp:

                st.markdown("#### Comparación entre categorías NPS")

                dimension_comp = st.selectbox(
                    "Comparar por",
                    dimensiones_comp,
                    key="dim_comp_pasivos"
                )

                comparacion = pd.crosstab(
                    datos[dimension_comp],
                    datos["tipo_nps"],
                    normalize="index"
                ) * 100

                comparacion = comparacion.reindex(
                    columns=ORDEN_NPS,
                    fill_value=0
                ).reset_index()

                st.dataframe(
                    comparacion.round(2),
                    use_container_width=True,
                    hide_index=True
                )

            if "comentario" in datos_pasivos.columns:

                st.markdown("#### Comentarios de clientes pasivos")

                columnas = [
                    c for c in [
                        "fecha", "región", "canal",
                        "motivo_contacto", "subcategoria",
                        "comentario"
                    ]
                    if c in datos_pasivos.columns
                ]

                comentarios_pasivos = datos_pasivos[columnas]

                st.dataframe(
                    comentarios_pasivos.head(100),
                    use_container_width=True,
                    hide_index=True
                )

                st.download_button(
                    "Descargar comentarios de pasivos",
                    data=comentarios_pasivos.to_csv(
                        index=False
                    ).encode("utf-8-sig"),
                    file_name="HITSS_comentarios_pasivos.csv",
                    mime="text/csv"
                )

        else:
            st.info(
                "No se encontraron clientes pasivos o dimensiones disponibles."
            )

    # ---------------------------------------------
    # TAB 4: NUBE DE PALABRAS
    # ---------------------------------------------
    with tabs[3]:

        st.markdown("### Nube de palabras de los clientes")

        if not NUBE_DISPONIBLE:
            st.warning(
                "Instala las dependencias con: "
                "pip install wordcloud matplotlib"
            )

        elif "comentario" not in datos.columns:
            st.warning("No se encuentra la columna comentario.")

        else:

            categoria_nube = st.selectbox(
                "Selecciona el grupo de clientes",
                [
                    "Todos",
                    "Detractores",
                    "Pasivos",
                    "Promotores"
                ],
                key="nube_categoria"
            )

            texto_datos = datos.copy()

            if categoria_nube != "Todos":
                texto_datos = texto_datos[
                    texto_datos["tipo_nps"] == categoria_nube
                ]

            comentarios = (
                texto_datos["comentario"]
                .dropna()
                .astype(str)
                .str.strip()
            )

            comentarios = comentarios[comentarios.ne("")]

            if comentarios.empty:
                st.info(
                    "No hay comentarios para la categoría seleccionada."
                )

            else:

                texto = " ".join(comentarios.tolist())

                stopwords_es = set(STOPWORDS).union({
                    "para", "pero", "porque", "como", "cuando",
                    "donde", "desde", "hasta", "todo", "toda",
                    "todos", "todas", "muy", "más", "menos",
                    "hacer", "hace", "hacen", "tener", "tiene",
                    "tienen", "ser", "está", "están", "fue",
                    "son", "sin", "sobre", "entre", "cada",
                    "cliente", "clientes", "servicio", "servicios",
                    "bueno", "buena", "buen", "mala", "mal",
                    "bien", "así", "aún", "solo", "nada",
                    "llevo", "lleva", "tengo", "tiene", "hace"
                })

                nube = WordCloud(
                    width=1200,
                    height=600,
                    background_color="white",
                    colormap="Blues",
                    stopwords=stopwords_es,
                    collocations=False,
                    max_words=150,
                    min_font_size=10,
                    random_state=42
                ).generate(texto)

                fig, ax = plt.subplots(figsize=(14, 7))
                ax.imshow(nube, interpolation="bilinear")
                ax.axis("off")
                ax.set_title(
                    f"Comentarios: {categoria_nube}",
                    fontsize=16
                )

                st.pyplot(fig)
                plt.close(fig)

                st.caption(
                    f"Comentarios analizados: {len(comentarios):,}. "
                    "El tamaño de las palabras representa su frecuencia, "
                    "no necesariamente su importancia o sentimiento."
                )

                with st.expander("Consultar comentarios originales"):
                    st.dataframe(
                        comentarios.to_frame(name="Comentario"),
                        use_container_width=True,
                        hide_index=True
                    )

# =====================================================
# 7. COMPARATIVO
# =====================================================
elif seccion == "Comparativo":

    st.subheader("Comparativo de promotores y detractores")

    st.write(
        "Compara canales, segmentos, regiones y motivos para "
        "identificar dónde se concentran las mejores y peores "
        "experiencias y generar hipótesis de campañas."
    )

    datos_comp = obtener_datos_nps(df)

    dimensiones_comp = [
        c for c in [
            "canal", "segmento", "región",
            "motivo_contacto", "subcategoria"
        ]
        if c in datos_comp.columns
    ]

    if datos_comp.empty:
        st.warning("No hay respuestas NPS válidas.")
        st.stop()

    if not dimensiones_comp:
        st.warning("No hay dimensiones disponibles para comparar.")
        st.stop()

    c1, c2 = st.columns(2)

    with c1:
        dimension_comp = st.selectbox(
            "Dimensión de comparación",
            dimensiones_comp,
            key="comparativo_dimension"
        )

    with c2:
        minimo_respuestas = st.number_input(
            "Mínimo de respuestas por categoría",
            min_value=1,
            max_value=len(datos_comp),
            value=min(20, len(datos_comp)),
            step=1,
            key="comparativo_minimo"
        )

    # Tabla de frecuencias por categoría
    conteos_comp = pd.crosstab(
        datos_comp[dimension_comp],
        datos_comp["tipo_nps"]
    ).reindex(
        columns=ORDEN_NPS,
        fill_value=0
    )

    comparativo = conteos_comp.copy()
    comparativo["Total"] = comparativo.sum(axis=1)

    comparativo = comparativo[
        comparativo["Total"] >= minimo_respuestas
    ].copy()

    if comparativo.empty:
        st.info(
            "Ninguna categoría cumple el mínimo seleccionado. "
            "Reduce el umbral de respuestas."
        )
        st.stop()

    comparativo["Promotores (%)"] = (
        comparativo["Promotores"] / comparativo["Total"] * 100
    )

    comparativo["Pasivos (%)"] = (
        comparativo["Pasivos"] / comparativo["Total"] * 100
    )

    comparativo["Detractores (%)"] = (
        comparativo["Detractores"] / comparativo["Total"] * 100
    )

    comparativo["NPS"] = (
        comparativo["Promotores (%)"]
        - comparativo["Detractores (%)"]
    )

    comparativo = comparativo.sort_values(
        "NPS", ascending=False
    )

    st.markdown("### Indicadores por categoría")

    tabla_comp = comparativo.reset_index().rename(
        columns={dimension_comp: "Categoría"}
    )

    st.dataframe(
        tabla_comp.round(2),
        use_container_width=True,
        hide_index=True
    )

    # Mejores y peores categorías
    st.markdown("### Principales oportunidades")

    mejor = comparativo.iloc[0]
    peor = comparativo.iloc[-1]

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Mayor NPS")
        st.metric(
            str(mejor.name),
            f"{mejor['NPS']:.2f} puntos",
            f"{mejor['Promotores (%)']:.1f}% promotores"
        )
        st.write(f"Respuestas: {int(mejor['Total']):,}")

    with c2:
        st.markdown("#### Menor NPS")
        st.metric(
            str(peor.name),
            f"{peor['NPS']:.2f} puntos",
            f"{peor['Detractores (%)']:.1f}% detractores"
        )
        st.write(f"Respuestas: {int(peor['Total']):,}")

    # Composición porcentual
    st.markdown("### Composición por categoría")

    grafico_comp = (
        comparativo[
            ["Promotores (%)", "Pasivos (%)", "Detractores (%)"]
        ]
        .rename(columns={
            "Promotores (%)": "Promotores",
            "Pasivos (%)": "Pasivos",
            "Detractores (%)": "Detractores"
        })
        .reset_index()
        .melt(
            id_vars=dimension_comp,
            var_name="Clasificación",
            value_name="Porcentaje"
        )
    )

    fig = px.bar(
        grafico_comp,
        x=dimension_comp,
        y="Porcentaje",
        color="Clasificación",
        barmode="stack",
        category_orders={"Clasificación": ORDEN_NPS},
        color_discrete_map=COLORES_NPS,
        title=f"Composición NPS por {dimension_comp}"
    )

    fig.update_layout(
        template="plotly_white",
        yaxis_range=[0, 100],
        yaxis_title="Porcentaje (%)",
        xaxis_title=dimension_comp,
        xaxis_tickangle=-35
    )

    st.plotly_chart(fig, use_container_width=True)

    # Ranking de promotores
    st.markdown("### Ranking por proporción")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Mayor porcentaje de promotores")

        top_prom = comparativo.sort_values(
            ["Promotores (%)", "Total"],
            ascending=[False, False]
        ).head(10)

        st.dataframe(
            top_prom[
                ["Promotores (%)", "Detractores (%)", "NPS", "Total"]
            ].round(2),
            use_container_width=True
        )

    with c2:
        st.markdown("#### Mayor porcentaje de detractores")

        top_det = comparativo.sort_values(
            ["Detractores (%)", "Total"],
            ascending=[False, False]
        ).head(10)

        st.dataframe(
            top_det[
                ["Detractores (%)", "Promotores (%)", "NPS", "Total"]
            ].round(2),
            use_container_width=True
        )

    # Orientación para campañas
    st.markdown("### Orientación para campañas y actividades")

    st.write(
        f"**Categoría de referencia:** {mejor.name}. "
        "Investiga sus comentarios, motivos de contacto y prácticas "
        "operativas para encontrar posibles acciones replicables."
    )

    st.write(
        f"**Categoría prioritaria:** {peor.name}. "
        "Revisa sus causas recurrentes, comentarios y concentración "
        "de detractores antes de diseñar acciones correctivas."
    )

    st.info(
        "Un NPS más alto no demuestra que el canal o una campaña "
        "sea la causa del resultado. Valida las hipótesis con "
        "información operativa y mide el impacto mediante una "
        "prueba piloto."
    )

    st.download_button(
        "Descargar comparativo en CSV",
        data=tabla_comp.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name=f"HITSS_comparativo_{dimension_comp}.csv",
        mime="text/csv"
    )

# =====================================================
# PIE DE PÁGINA
# =====================================================
st.divider()

st.caption("HITSS | Dashboard Experiencia de Clientes | NPS y análisis de comentarios")
