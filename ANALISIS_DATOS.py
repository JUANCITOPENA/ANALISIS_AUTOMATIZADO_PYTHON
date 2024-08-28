import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import base64
import openpyxl
from datetime import datetime
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Esto debe ser lo primero después de importar Streamlit
st.set_page_config(
    page_title="📊 Insights Automáticos",  # Título que aparecerá en la pestaña del navegador
    page_icon="📊"  # Emoji como favicon (puedes reemplazarlo con una ruta de archivo de imagen)
)


# Personalizar el estilo
st.markdown("""
    <style>
        .block-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stMetric {
            font-size: 18px;
            font-weight: bold;
        }
        .stDataFrame {
            font-size: 18px;
            color: #333;
        }
        .stBarChart {
            padding: 20px;
        }
        .stSelectbox {
            font-size: 14px;
        }
        .stDateInput {
            font-size: 14px;
        }
        .stWarning {
            color: red;
        }
        .stError {
            color: darkred;
        }
    </style>
""", unsafe_allow_html=True)

# Función para cargar el archivo de datos
@st.cache_data
def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        return pd.read_excel(file)
    else:
        st.error("Tipo de archivo no soportado. Por favor, carga un archivo CSV o XLSX.")
        return None


# Interfaz de usuario para cargar el archivo
st.title('📊 Reporte de Insights de Datos Por: 👨‍💻 Juancito Peña V')

uploaded_file = st.sidebar.file_uploader("Carga tu archivo de ventas", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Cargar los datos
    df = load_data(uploaded_file)
    
    if df is not None:
        # Convertir la columna 'FechaPedidoServerN' a formato datetime
        if 'FechaPedidoServerN' in df.columns:
            df['FechaPedidoServerN'] = pd.to_datetime(df['FechaPedidoServerN'], format='%d/%m/%Y')

            # Filtros de fecha en la barra lateral
            st.sidebar.header("Filtros")
            fecha_inicio = st.sidebar.date_input('Fecha de Inicio', df['FechaPedidoServerN'].min().date())
            fecha_fin = st.sidebar.date_input('Fecha de Fin', df['FechaPedidoServerN'].max().date())

            # Convertir las fechas seleccionadas a datetime para la comparación
            fecha_inicio = pd.Timestamp(fecha_inicio)
            fecha_fin = pd.Timestamp(fecha_fin)

            if fecha_inicio > fecha_fin:
                st.error('La fecha de inicio debe ser anterior a la fecha de fin.')
            else:
                # Filtrar los datos por el rango de fechas
                df_filtrado = df[(df['FechaPedidoServerN'] >= fecha_inicio) & (df['FechaPedidoServerN'] <= fecha_fin)]

                # Filtrar por localidad
                if 'Localidad Nombre' in df.columns:
                    venta_por_localidad = df.groupby('Localidad Nombre').agg(
                        cantidad_vendida=pd.NamedAgg(column='Cantidad', aggfunc='sum'),
                        total_vendido=pd.NamedAgg(column='Total Vendido', aggfunc='sum')
                    ).reset_index().sort_values('total_vendido', ascending=False)
                    
                    localidades = df['Localidad Nombre'].unique()
                    localidad_seleccionada = st.sidebar.selectbox('Selecciona una Localidad', ['Todas'] + list(localidades))
                    
                    if localidad_seleccionada != 'Todas':
                        df_filtrado = df_filtrado[df_filtrado['Localidad Nombre'] == localidad_seleccionada]
                else:
                    st.warning("La columna 'Localidad' no se encuentra en el archivo.")
                    venta_por_localidad = pd.DataFrame()


                # Cálculo de KPIs con datos filtrados
                num_vendedores = df_filtrado['Vendedor'].nunique()
                num_pedidos = df_filtrado['NoPedidoStr'].nunique()
                num_clientes = df_filtrado['Cliente'].nunique()
                num_productos = df_filtrado['Descripcion'].nunique()
                total_cantidad = df_filtrado['Cantidad'].sum()
                total_monto_vendido = df_filtrado['Total Vendido'].sum()

                # Crear un DataFrame con los KPIs en una fila, aplicando estilos a los números
                kpi_data = {
                    '📊 Número de Vendedores': [f"<div style='text-align:center; font-size:20px;'>{num_vendedores}</div>"],
                    '📦 Número de Pedidos': [f"<div style='text-align:center; font-size:20px;'>{num_pedidos}</div>"],
                    '👥 Número de Clientes': [f"<div style='text-align:center; font-size:20px;'>{num_clientes}</div>"],
                    '🛍️ Número de Productos': [f"<div style='text-align:center; font-size:20px;'>{num_productos}</div>"],
                    '📉 Total Cantidad Vendida': [f"<div style='text-align:center; font-size:20px;'>{total_cantidad}</div>"],
                    '💰 Total Monto Vendido': [f"<div style='text-align:center; font-size:20px;'>${total_monto_vendido:,.2f}</div>"]
                }

                # Definir el DataFrame df_kpis
                df_kpis = pd.DataFrame(kpi_data)

                # Mostrar la tabla de KPIs en Streamlit con estilos aplicados
                st.write('**Resumen de KPIs**')

                # Mostrar la tabla de KPIs con HTML para aplicar estilos personalizados
                st.markdown(df_kpis.to_html(escape=False, index=False), unsafe_allow_html=True)


                st.subheader('Tablas de Resumen')
                st.write('Ventas por Cliente')
                st.dataframe(df_filtrado.groupby('Cliente')['Total Vendido'].sum().reset_index().sort_values('Total Vendido', ascending=False), use_container_width=True)
                st.write('Ventas por Vendedor')
                st.dataframe(df_filtrado.groupby('Vendedor')['Total Vendido'].sum().reset_index().sort_values('Total Vendido', ascending=False), use_container_width=True)
                st.write('Ventas por Producto')
                st.dataframe(df_filtrado.groupby('Descripcion').agg(
                    cantidad_vendida=pd.NamedAgg(column='Cantidad', aggfunc='sum'),
                    total_vendido=pd.NamedAgg(column='Total Vendido', aggfunc='sum')
                ).reset_index().sort_values('total_vendido', ascending=False), use_container_width=True)

                if not venta_por_localidad.empty:
                    st.write('Ventas por Localidad')
                    st.dataframe(venta_por_localidad, use_container_width=True)

                    # Gráfico de pastel para Ventas por Localidad
                    fig_localidad, ax_localidad = plt.subplots(figsize=(10, 7))
                    ax_localidad.pie(
                        venta_por_localidad['total_vendido'],
                        labels=venta_por_localidad['Localidad Nombre'],
                        autopct='%1.1f%%',
                        colors=sns.color_palette('Set2', n_colors=len(venta_por_localidad)),
                        startangle=140
                    )
                    ax_localidad.set_title('Distribución de Ventas por Localidad')
                    st.pyplot(fig_localidad)

                # Asegúrate de que el DataFrame tenga la columna 'Total Vendido' después de las agregaciones
                if 'Total Vendido' not in df_filtrado.columns:
                    st.error("La columna 'Total Vendido' no está en el DataFrame. Verifica las agregaciones.")
                else:
                    # Crear los gráficos solo si la columna existe
                    st.subheader('Gráficos')

                    # Gráfico de Ventas por Cliente
                    fig_clientes, ax_clientes = plt.subplots(figsize=(12, 6))
                    df_clientes = df_filtrado.groupby('Cliente')['Total Vendido'].sum().reset_index().sort_values('Total Vendido', ascending=False).head(10)
                    sns.barplot(x='Cliente', y='Total Vendido', data=df_clientes, ax=ax_clientes, palette="husl")
                    ax_clientes.set_title('Top 10 Clientes por Ventas Totales')
                    ax_clientes.set_xlabel('Cliente')
                    ax_clientes.set_ylabel('Total Vendido')
                    ax_clientes.tick_params(axis='x', rotation=45)

                    # Añadir etiquetas de monto en cada barra
                    for p in ax_clientes.patches:
                        ax_clientes.annotate(f'${p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                                            ha='center', va='center', fontsize=10, color='black', xytext=(0, 10),
                                            textcoords='offset points')
                    st.pyplot(fig_clientes)

                    # Gráfico de Ventas por Vendedor
                    fig_vendedores, ax_vendedores = plt.subplots(figsize=(12, 6))
                    df_vendedores = df_filtrado.groupby('Vendedor')['Total Vendido'].sum().reset_index().sort_values('Total Vendido', ascending=False).head(10)
                    sns.barplot(x='Vendedor', y='Total Vendido', data=df_vendedores, ax=ax_vendedores, palette="Set2")
                    ax_vendedores.set_title('Top 10 Vendedores por Ventas Totales')
                    ax_vendedores.set_xlabel('Vendedor')
                    ax_vendedores.set_ylabel('Total Vendido')
                    ax_vendedores.tick_params(axis='x', rotation=45)

                    # Añadir etiquetas de monto en cada barra
                    for p in ax_vendedores.patches:
                        ax_vendedores.annotate(f'${p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                                            ha='center', va='center', fontsize=10, color='black', xytext=(0, 10),
                                            textcoords='offset points')
                    st.pyplot(fig_vendedores)

                    # Gráfico de Ventas por Producto
                    fig_productos, ax_productos = plt.subplots(figsize=(12, 6))
                    df_productos = df_filtrado.groupby('Descripcion').agg(
                        cantidad_vendida=pd.NamedAgg(column='Cantidad', aggfunc='sum'),
                        total_vendido=pd.NamedAgg(column='Total Vendido', aggfunc='sum')
                    ).reset_index().sort_values('total_vendido', ascending=False).head(10)
                    sns.barplot(x='Descripcion', y='total_vendido', data=df_productos, ax=ax_productos, palette="magma")
                    ax_productos.set_title('Top 10 Productos por Ventas Totales')
                    ax_productos.set_xlabel('Producto')
                    ax_productos.set_ylabel('Total Vendido')
                    ax_productos.tick_params(axis='x', rotation=45)

                    # Añadir etiquetas de monto en cada barra
                    for p in ax_productos.patches:
                        ax_productos.annotate(f'${p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                                            ha='center', va='center', fontsize=10, color='black', xytext=(0, 10),
                                            textcoords='offset points')
                    st.pyplot(fig_productos)

                    # Crear una columna para el mes
                    df['Mes'] = df['FechaPedidoServerN'].dt.to_period('M').astype(str)

                    # Obtener la lista de meses disponibles
                    meses_disponibles = df['Mes'].unique()
                    meses_disponibles = sorted(meses_disponibles)

                    # Establecer el mes actual como el valor predeterminado
                    mes_actual = pd.Timestamp.now().to_period('M').strftime('%Y-%m')  # Usa strftime para convertir a string
                    mes_seleccionado = st.sidebar.selectbox('Selecciona el Mes', options=meses_disponibles, index=meses_disponibles.index(mes_actual))

                    # Filtrar los datos por el mes seleccionado
                    df_filtrado = df[df['Mes'] == mes_seleccionado]

                    # Agrupar las ventas por fecha
                    df_fecha = df_filtrado.groupby('FechaPedidoServerN')['Total Vendido'].sum().reset_index()

                    # Crear el gráfico de líneas para ventas totales por fecha
                    fig_fecha, ax_fecha = plt.subplots(figsize=(12, 6))
                    sns.lineplot(x='FechaPedidoServerN', y='Total Vendido', data=df_fecha, ax=ax_fecha, marker='o')

                    # Configurar títulos y etiquetas con ajustes de tamaño
                    ax_fecha.set_title('Ventas Totales por Fecha', pad=30, fontsize=16)  # Aumentar el espacio superior del título y ajustar el tamaño de fuente
                    ax_fecha.set_xlabel('Fecha', labelpad=10, fontsize=12)  # Ajustar el tamaño de fuente y el espacio para la etiqueta del eje X
                    ax_fecha.set_ylabel('Total Vendido', labelpad=10, fontsize=12)  # Ajustar el tamaño de fuente y el espacio para la etiqueta del eje Y
                    ax_fecha.tick_params(axis='x', rotation=45, labelsize=10)  # Ajustar el tamaño de fuente de las etiquetas del eje X
                    ax_fecha.tick_params(axis='y', labelsize=10)  # Ajustar el tamaño de fuente de las etiquetas del eje Y

                   # Añadir etiquetas de monto en cada punto
                    for x, y in zip(df_fecha['FechaPedidoServerN'], df_fecha['Total Vendido']):
                        ax_fecha.annotate(f'${y:,.0f}', (x, y), textcoords="offset points", xytext=(0, 7), ha='center', fontsize=9)  # Ajustar el tamaño de fuente y la posición de las etiquetas

                    # Mostrar el gráfico
                    st.pyplot(fig_fecha)




                    # Supongamos que df es el DataFrame original
                    # Convertir la columna 'FechaPedidoServerN' a formato datetime
                    df['FechaPedidoServerN'] = pd.to_datetime(df['FechaPedidoServerN'], format='%d/%m/%Y')

                    # Crear una columna para el mes y año
                    df['Mes'] = df['FechaPedidoServerN'].dt.to_period('M').astype(str)

                    # Crear una lista de meses únicos disponibles para el segmentador
                    meses_disponibles = sorted(df['Mes'].unique())

                    # Obtener el mes actual para usar como valor predeterminado
                    mes_actual = pd.Timestamp.now().to_period('M').strftime('%Y-%m')

                    # Crear el selector de mes en la barra lateral con el mes actual como valor predeterminado
                    mes_seleccionado = st.sidebar.selectbox('Selecciona el mes', options=meses_disponibles, index=meses_disponibles.index(mes_actual), key='selector_mes_unico')

                    # Filtrar los datos según el mes seleccionado
                    df_filtrado = df[df['Mes'] == mes_seleccionado]

                    # Gráfico de Ventas Diarias con barras destacadas para mayores y menores ventas
                    fig, ax = plt.subplots(figsize=(12, 6))

                    # Calcular ventas diarias
                    df_diarias = df_filtrado.groupby('FechaPedidoServerN')['Total Vendido'].sum().reset_index()

                    # Identificar el máximo y mínimo de ventas diarias
                    max_venta = df_diarias['Total Vendido'].max()
                    min_venta = df_diarias['Total Vendido'].min()

                    # Crear una columna para el color de las barras
                    df_diarias['Color'] = df_diarias['Total Vendido'].apply(lambda x: 'green' if x == max_venta else ('red' if x == min_venta else 'grey'))

                    # Crear el gráfico de barras
                    sns.barplot(x='FechaPedidoServerN', y='Total Vendido', data=df_diarias, ax=ax, palette=df_diarias['Color'].values)

                    # Añadir etiquetas de monto en cada barra
                    for p in ax.patches:
                        ax.annotate(f'${p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()), 
                                    ha='center', va='center', fontsize=10, color='black', xytext=(0, 10),
                                    textcoords='offset points')

                    # Configurar títulos y etiquetas con un margen superior ajustado
                    ax.set_title(f'Ventas Diarias para {mes_seleccionado} con Días de Mayor y Menor Venta Destacados', pad=20)  # Ajusta el espacio superior del título con pad

                    # Ajustar el espacio entre las etiquetas de los ejes y el gráfico
                    ax.set_xlabel('Fecha', labelpad=15)  # Incrementa el espacio para la etiqueta del eje X
                    ax.set_ylabel('Total Vendido', labelpad=15)  # Incrementa el espacio para la etiqueta del eje Y
                    ax.tick_params(axis='x', rotation=45)

                    # Mostrar el gráfico
                    st.pyplot(fig)

                    # Suponiendo que 'FechaPedidoServerN' es una columna de tipo datetime y 'Localidad Nombre' es el nombre correcto de la columna con nombres de localidades.

                    # Obtener el mes actual
                    mes_actual = datetime.now().strftime('%Y-%m')

                    # Generar una lista de meses desde enero de 2020 hasta el mes actual
                    fechas_disponibles = pd.date_range(start='2020-01-01', end=datetime.now(), freq='M').strftime('%Y-%m').tolist()

                    # Asegurarse de que el mes actual esté incluido en la lista
                    if mes_actual not in fechas_disponibles:
                        fechas_disponibles.append(mes_actual)

                    # Selector de mes (ya está en la barra lateral)
                    mes_seleccionado = st.sidebar.selectbox(
                        "Seleccionar Mes",
                        fechas_disponibles,
                        index=fechas_disponibles.index(mes_actual),
                        key='selector_mes_kpis'
                    )

                    # Verificar si la columna 'Localidad Nombre' existe
                    if 'Localidad Nombre' in df_filtrado.columns:
                        # Filtro por localidad (ya está en la barra lateral)
                        localidades = df_filtrado['Localidad Nombre'].unique()
                        localidad_seleccionada = st.sidebar.selectbox("Seleccionar Localidad", ['Todas'] + list(localidades), key='selector_localidad_kpis')
                        
                        # Filtrar datos por mes y localidad
                        df_filtrado_mes = df_filtrado[df_filtrado['FechaPedidoServerN'].dt.strftime('%Y-%m') == mes_seleccionado]
                        
                        if localidad_seleccionada != 'Todas':
                            df_filtrado_final = df_filtrado_mes[df_filtrado_mes['Localidad Nombre'] == localidad_seleccionada]
                        else:
                            df_filtrado_final = df_filtrado_mes
                    else:
                        st.warning("La columna 'Localidad Nombre' no se encuentra en el archivo.")
                        df_filtrado_final = pd.DataFrame()  # Crear un DataFrame vacío si la columna no existe

                    # Verificar si el DataFrame filtrado no está vacío
                    if not df_filtrado_final.empty:
                        # Calcular el total vendido por los top 10 clientes
                        top_clientes = df_filtrado_final.groupby('Cliente')['Total Vendido'].sum().nlargest(10).sum()

                        # Calcular el total vendido por los top 10 vendedores
                        top_vendedores = df_filtrado_final.groupby('Vendedor')['Total Vendido'].sum().nlargest(10).sum()

                        # Mostrar los KPIs con espacio entre ellos
                        st.metric("Ventas Totales - Top 10 Clientes", f"${top_clientes:,.2f}")
                        st.write("")  # Añadir espacio
                        st.metric("Ventas Totales - Top 10 Vendedores", f"${top_vendedores:,.2f}")

                        # Filtrar los 10 días con ventas más altas y bajas
                        mejores_dias = df_filtrado_final.groupby('FechaPedidoServerN')['Total Vendido'].sum().nlargest(10)
                        peores_dias = df_filtrado_final.groupby('FechaPedidoServerN')['Total Vendido'].sum().nsmallest(10)

                        # Crear gráficos separados para mejores y peores días
                        fig, ax = plt.subplots(1, 2, figsize=(16, 6))

                        # Graficar los mejores días en verde
                        mejores_dias.plot(kind='bar', color='green', edgecolor='black', ax=ax[0])
                        ax[0].set_title('Top 10 Mejores Días por Ventas Totales')
                        ax[0].set_xlabel('Fecha')
                        ax[0].set_ylabel('Total Vendido')
                        ax[0].tick_params(axis='x', rotation=45)
                        for i, (fecha, total) in enumerate(zip(mejores_dias.index, mejores_dias.values)):
                            ax[0].text(i, total + 0.05 * total, f"${total:,.2f}", ha='center', va='bottom', fontsize=8, color='green')

                        # Graficar los peores días en rojo
                        peores_dias.plot(kind='bar', color='red', edgecolor='black', ax=ax[1])
                        ax[1].set_title('Top 10 Peores Días por Ventas Totales')
                        ax[1].set_xlabel('Fecha')
                        ax[1].set_ylabel('Total Vendido')
                        ax[1].tick_params(axis='x', rotation=45)
                        for i, (fecha, total) in enumerate(zip(peores_dias.index, peores_dias.values)):
                            ax[1].text(i, total + 0.05 * total, f"${total:,.2f}", ha='center', va='bottom', fontsize=8, color='red')

                        # Mostrar los gráficos en Streamlit
                        st.pyplot(fig)
                    else:
                        st.warning("No hay datos disponibles para el mes y la localidad seleccionados.")
                        
                    # Gráfico de dispersión de ventas por fecha
                    fig_dispersion, ax_dispersion = plt.subplots(figsize=(12, 6))
                    sns.scatterplot(x='FechaPedidoServerN', y='Total Vendido', data=df_filtrado, ax=ax_dispersion)

                    # Configurar títulos y etiquetas
                    ax_dispersion.set_title('Ventas Totales por Fecha (Dispersión)')
                    ax_dispersion.set_xlabel('Fecha')
                    ax_dispersion.set_ylabel('Total Vendido')
                    ax_dispersion.tick_params(axis='x', rotation=45)

                    # Mostrar el gráfico
                    st.pyplot(fig_dispersion)

                    # Calcular las ventas totales por cliente
                    ventas_por_cliente = df_filtrado.groupby('Cliente')['Total Vendido'].sum().nlargest(20).reset_index()

                    # Crear el gráfico de embudo para los clientes
                    fig_embudo_cliente = go.Figure(go.Funnel(
                        y = ventas_por_cliente['Cliente'],
                        x = ventas_por_cliente['Total Vendido'],
                        textinfo = "value+percent initial"
                    ))

                    fig_embudo_cliente.update_layout(title_text='Embudo de Ventas por Cliente (Top 20)')
                    st.plotly_chart(fig_embudo_cliente, use_container_width=True)

                    # Calcular las ventas totales por vendedor
                    ventas_por_vendedor = df_filtrado.groupby('Vendedor')['Total Vendido'].sum().nlargest(20).reset_index()

                    # Crear el gráfico de embudo para los vendedores
                    fig_embudo_vendedor = go.Figure(go.Funnel(
                        y = ventas_por_vendedor['Vendedor'],
                        x = ventas_por_vendedor['Total Vendido'],
                        textinfo = "value+percent initial"
                    ))

                    fig_embudo_vendedor.update_layout(title_text='Embudo de Ventas por Vendedor (Top 20)')
                    st.plotly_chart(fig_embudo_vendedor, use_container_width=True)

                    # Calcular las ventas totales por producto
                    ventas_por_producto = df_filtrado.groupby('Descripcion')['Total Vendido'].sum().nlargest(20).reset_index()

                    # Crear el gráfico de embudo para los productos
                    fig_embudo_producto = go.Figure(go.Funnel(
                        y = ventas_por_producto['Descripcion'],
                        x = ventas_por_producto['Total Vendido'],
                        textinfo = "value+percent initial"
                    ))

                    fig_embudo_producto.update_layout(title_text='Embudo de Ventas por Producto (Top 20)')
                    st.plotly_chart(fig_embudo_producto, use_container_width=True)
                    
                    
                    
                    # Filtrar por Condición de Pago
                    if 'Condicion Pago' in df.columns:
                        condiciones_pago = df['Condicion Pago'].unique()
                        condicion_pago_seleccionada = st.sidebar.selectbox('Selecciona Condición de Pago', ['Todas'] + list(condiciones_pago))
                    else:
                        st.warning("La columna 'Condicion Pago' no se encuentra en el archivo.")
                        condicion_pago_seleccionada = 'Todas'

                    # Filtrar por Cliente
                    if 'Cliente' in df.columns:
                        clientes = df['Cliente'].unique()
                        cliente_seleccionado = st.sidebar.selectbox('Selecciona un Cliente', ['Todos'] + list(clientes))
                    else:
                        st.warning("La columna 'Cliente' no se encuentra en el archivo.")
                        cliente_seleccionado = 'Todos'

                    # Filtrar por Vendedor
                    if 'Vendedor' in df.columns:
                        vendedores = df['Vendedor'].unique()
                        vendedor_seleccionado = st.sidebar.selectbox('Selecciona un Vendedor', ['Todos'] + list(vendedores))
                    else:
                        st.warning("La columna 'Vendedor' no se encuentra en el archivo.")
                        vendedor_seleccionado = 'Todos'

                    # Aplicar filtros
                    if condicion_pago_seleccionada != 'Todas':
                        df_filtrado = df_filtrado[df_filtrado['Condicion Pago'] == condicion_pago_seleccionada]

                    if cliente_seleccionado != 'Todos':
                        df_filtrado = df_filtrado[df_filtrado['Cliente'] == cliente_seleccionado]

                    if vendedor_seleccionado != 'Todos':
                        df_filtrado = df_filtrado[df_filtrado['Vendedor'] == vendedor_seleccionado]
                        
                        
                    # Gráfico de Ventas por Condición de Pago
                    fig_condicion_pago, ax_condicion_pago = plt.subplots(figsize=(12, 6))
                    df_condicion_pago = df_filtrado.groupby('Condicion Pago')['Total Vendido'].sum().reset_index().sort_values('Total Vendido', ascending=False)
                    sns.barplot(x='Condicion Pago', y='Total Vendido', data=df_condicion_pago, ax=ax_condicion_pago, palette="coolwarm")
                    ax_condicion_pago.set_title('Ventas Totales por Condición de Pago')
                    ax_condicion_pago.set_xlabel('Condición de Pago')
                    ax_condicion_pago.set_ylabel('Total Vendido')
                    for p in ax_condicion_pago.patches:
                        ax_condicion_pago.annotate(f'${p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                                                ha='center', va='center', fontsize=10, color='black', xytext=(0, 10),
                                                textcoords='offset points')
                    st.pyplot(fig_condicion_pago)
                    
  
  


                    # Verificar que las columnas necesarias están presentes
                    required_columns = ['Descripcion', 'FechaPedidoServerN', 'Cantidad']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    if missing_columns:
                        raise ValueError(f"Faltan las siguientes columnas en el archivo CSV: {', '.join(missing_columns)}")

                    # Convertir 'FechaPedidoServerN' a datetime si no lo es ya
                    df['FechaPedidoServerN'] = pd.to_datetime(df['FechaPedidoServerN'], errors='coerce')

                    # Eliminar filas con fechas nulas después de la conversión
                    df = df.dropna(subset=['FechaPedidoServerN'])

                    # Crear una columna para el mes y año
                    df['Mes'] = df['FechaPedidoServerN'].dt.to_period('M')

                    # Crear una tabla pivote de productos y cantidades por mes
                    tabla_pivote = df.pivot_table(index='Descripcion', columns='Mes', values='Cantidad', aggfunc='sum', fill_value=0)

                    # Proyección de ventas futuras utilizando una media móvil simple de 3 meses
                    ventas_mes = df.groupby('Mes')['Cantidad'].sum()
                    proyeccion = ventas_mes.rolling(window=3).mean().shift(-1)

                    # Rellenar la proyección para los meses faltantes hasta el 31 de diciembre
                    meses_futuros = pd.date_range(start=df['FechaPedidoServerN'].max(), end='2024-12-31', freq='M').to_period('M')
                    for mes in meses_futuros:
                        if mes not in proyeccion.index:
                            proyeccion.loc[mes] = proyeccion.iloc[-1]  # Utilizar la última proyección conocida para los meses futuros

                    # Crear un gráfico de la proyección de ventas
                    plt.figure(figsize=(12, 6))
                    plt.plot(ventas_mes.index.astype(str), ventas_mes.values, label='Ventas Históricas', marker='o')
                    plt.plot(proyeccion.index.astype(str), proyeccion.values, label='Proyección de Ventas', linestyle='--', marker='x')
                    plt.title('Proyección de Ventas Mensuales')
                    plt.xlabel('Mes')
                    plt.ylabel('Cantidad Vendida')
                    plt.legend()
                    plt.grid(True)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.show()

                    # Añadir la proyección a la tabla pivote
                    tabla_pivote = tabla_pivote.join(proyeccion.rename('Proyección'), how='outer')

                    # Mostrar la tabla pivote
                    print(tabla_pivote)
                   
  
  
  
  
  
  
  
                    # --- Análisis ABC de los 30 Mejores Clientes ---

                    # Filtrar los 30 mejores clientes basados en Total Vendido
                    top_30_clientes = df_filtrado.groupby('Cliente')['Total Vendido'].sum().nlargest(30).reset_index()

                    # Calcular el total acumulado y el porcentaje acumulado
                    top_30_clientes['Total Acumulado'] = top_30_clientes['Total Vendido'].cumsum()
                    top_30_clientes['Porcentaje Acumulado'] = 100 * top_30_clientes['Total Acumulado'] / top_30_clientes['Total Vendido'].sum()

                    # Clasificar en A, B, C según el análisis Pareto (80/20)
                    def clasificar_abc(porcentaje_acumulado):
                        if porcentaje_acumulado <= 80:
                            return 'A'
                        elif porcentaje_acumulado <= 95:
                            return 'B'
                        else:
                            return 'C'

                    top_30_clientes['Clasificación ABC'] = top_30_clientes['Porcentaje Acumulado'].apply(clasificar_abc)

                    # Funciones de color basadas en la clasificación ABC
                    def color_abc(val):
                        color = ''
                        text_color = ''
                        if val == 'A':
                            color = 'background-color: #00FF00;'  # Verde para categoría A
                            text_color = 'color: #000000;'  # Negro para contraste
                        elif val == 'B':
                            color = 'background-color: #FFFF00;'  # Amarillo para categoría B
                            text_color = 'color: #000000;'  # Negro para contraste
                        elif val == 'C':
                            color = 'background-color: #FF0000;'  # Rojo para categoría C
                            text_color = 'color: #FFFFFF;'  # Blanco para contraste
                        return f'{color} {text_color}'

                    # Aplicar estilo a la tabla
                    styled_df = top_30_clientes.style.applymap(color_abc, subset=['Clasificación ABC'])

                    # Mostrar la tabla en Streamlit
                    st.write("Análisis ABC de los 30 Mejores Clientes")
                    st.dataframe(styled_df)

                    

  
  
  
                    # --- Análisis ABC de los Productos ---

                    # Filtrar los productos con mayores ventas basadas en Total Vendido
                    top_productos = df_filtrado.groupby('Descripcion')['Total Vendido'].sum().nlargest(30).reset_index()

                    # Calcular el total acumulado y el porcentaje acumulado
                    top_productos['Total Acumulado'] = top_productos['Total Vendido'].cumsum()
                    top_productos['Porcentaje Acumulado'] = 100 * top_productos['Total Acumulado'] / top_productos['Total Vendido'].sum()

                    # Clasificar en A, B, C según el análisis Pareto (80/20)
                    def clasificar_abc(porcentaje_acumulado):
                        if porcentaje_acumulado <= 80:
                            return 'A'
                        elif porcentaje_acumulado <= 95:
                            return 'B'
                        else:
                            return 'C'

                    top_productos['Clasificación ABC'] = top_productos['Porcentaje Acumulado'].apply(clasificar_abc)

                    # Funciones de color basadas en la clasificación ABC
                    def color_abc(val):
                        color = ''
                        text_color = ''
                        if val == 'A':
                            color = 'background-color: #00FF00;'  # Verde para categoría A
                            text_color = 'color: #000000;'  # Negro para contraste
                        elif val == 'B':
                            color = 'background-color: #FFFF00;'  # Amarillo para categoría B
                            text_color = 'color: #000000;'  # Negro para contraste
                        elif val == 'C':
                            color = 'background-color: #FF0000;'  # Rojo para categoría C
                            text_color = 'color: #FFFFFF;'  # Blanco para contraste
                        return f'{color} {text_color}'

                    # Aplicar estilo a la tabla
                    styled_df_productos = top_productos.style.applymap(color_abc, subset=['Clasificación ABC'])

                    # Mostrar la tabla en Streamlit
                    st.write("Análisis ABC de los Productos")
                    st.dataframe(styled_df_productos)

  
  
  
  
  
                    
                  
                  # --- Análisis ABC de los Vendedores ---

                    # Filtrar los vendedores con mayores ventas basadas en Total Vendido
                    top_vendedores = df_filtrado.groupby('Vendedor')['Total Vendido'].sum().nlargest(30).reset_index()

                    # Calcular el total acumulado y el porcentaje acumulado
                    top_vendedores['Total Acumulado'] = top_vendedores['Total Vendido'].cumsum()
                    top_vendedores['Porcentaje Acumulado'] = 100 * top_vendedores['Total Acumulado'] / top_vendedores['Total Vendido'].sum()

                    # Clasificar en A, B, C según el análisis Pareto (80/20)
                    def clasificar_abc(porcentaje_acumulado):
                        if porcentaje_acumulado <= 80:
                            return 'A'
                        elif porcentaje_acumulado <= 95:
                            return 'B'
                        else:
                            return 'C'

                    top_vendedores['Clasificación ABC'] = top_vendedores['Porcentaje Acumulado'].apply(clasificar_abc)

                    # Funciones de color basadas en la clasificación ABC
                    def color_abc(val):
                        color = ''
                        text_color = ''
                        if val == 'A':
                            color = 'background-color: #00FF00;'  # Verde para categoría A
                            text_color = 'color: #000000;'  # Negro para contraste
                        elif val == 'B':
                            color = 'background-color: #FFFF00;'  # Amarillo para categoría B
                            text_color = 'color: #000000;'  # Negro para contraste
                        elif val == 'C':
                            color = 'background-color: #FF0000;'  # Rojo para categoría C
                            text_color = 'color: #FFFFFF;'  # Blanco para contraste
                        return f'{color} {text_color}'

                    # Aplicar estilo a la tabla
                    styled_df_vendedores = top_vendedores.style.applymap(color_abc, subset=['Clasificación ABC'])

                    # Mostrar la tabla en Streamlit
                    st.write("Análisis ABC de los Vendedores")
                    st.dataframe(styled_df_vendedores)



                    # Filtrar los 30 mejores clientes basados en Total Vendido
                    top_30_clientes = df_filtrado.groupby('Cliente')['Total Vendido'].sum().nlargest(30).reset_index()

                    # Calcular el total acumulado y el porcentaje acumulado
                    top_30_clientes['Total Acumulado'] = top_30_clientes['Total Vendido'].cumsum()
                    top_30_clientes['Porcentaje Acumulado'] = 100 * top_30_clientes['Total Acumulado'] / top_30_clientes['Total Vendido'].sum()

                    # Clasificar en A, B, C según el análisis Pareto (80/20)
                    def clasificar_abc(porcentaje_acumulado):
                        if porcentaje_acumulado <= 80:
                            return 'A'
                        elif porcentaje_acumulado <= 95:
                            return 'B'
                        else:
                            return 'C'

                    top_30_clientes['Clasificación ABC'] = top_30_clientes['Porcentaje Acumulado'].apply(clasificar_abc)

                    # Funciones de color basadas en la clasificación ABC
                    def color_abc(val):
                        color = ''
                        text_color = ''
                        if val == 'A':
                            color = 'background-color: #00FF00;'  # Verde para categoría A
                            text_color = 'color: #000000;'  # Negro para contraste
                        elif val == 'B':
                            color = 'background-color: #FFFF00;'  # Amarillo para categoría B
                            text_color = 'color: #000000;'  # Negro para contraste
                        elif val == 'C':
                            color = 'background-color: #FF0000;'  # Rojo para categoría C
                            text_color = 'color: #FFFFFF;'  # Blanco para contraste
                        return f'{color} {text_color}'

                    # Crear gráfico de Pareto
                    fig, ax1 = plt.subplots(figsize=(12, 6))

                    # Colores de las barras basados en la clasificación ABC
                    colors = top_30_clientes['Clasificación ABC'].map({
                        'A': '#00FF00',  # Verde
                        'B': '#FFFF00',  # Amarillo
                        'C': '#FF0000'   # Rojo
                    })

                    ax1.bar(top_30_clientes['Cliente'], top_30_clientes['Total Vendido'], color=colors, label='Total Vendido')
                    ax1.set_xlabel('Cliente', fontsize=10)
                    ax1.set_ylabel('Total Vendido', color='blue', fontsize=10)
                    ax1.tick_params(axis='y', labelcolor='blue')
                    ax1.set_title('Análisis ABC de los 30 Mejores Clientes', fontsize=12)
                    ax1.tick_params(axis='x', rotation=90, labelsize=8)  # Rotar etiquetas x para mejor legibilidad

                    ax2 = ax1.twinx()
                    ax2.plot(top_30_clientes['Cliente'], top_30_clientes['Porcentaje Acumulado'], color='red', marker='o', label='Porcentaje Acumulado')
                    ax2.set_ylabel('Porcentaje Acumulado (%)', color='red', fontsize=10)
                    ax2.tick_params(axis='y', labelcolor='red')

                    fig.tight_layout()
                    st.pyplot(fig)

                    # Aplicar estilo a la tabla
                    styled_df = top_30_clientes.style.applymap(color_abc, subset=['Clasificación ABC'])

                    # Mostrar la tabla en Streamlit
                    st.write("Análisis ABC de los 30 Mejores Clientes")
                    st.dataframe(styled_df)

                    # --- Análisis ABC de los Productos ---

                    # Filtrar los productos con mayores ventas basadas en Total Vendido
                    top_productos = df_filtrado.groupby('Descripcion')['Total Vendido'].sum().nlargest(30).reset_index()

                    # Calcular el total acumulado y el porcentaje acumulado
                    top_productos['Total Acumulado'] = top_productos['Total Vendido'].cumsum()
                    top_productos['Porcentaje Acumulado'] = 100 * top_productos['Total Acumulado'] / top_productos['Total Vendido'].sum()

                    # Clasificar en A, B, C según el análisis Pareto (80/20)
                    top_productos['Clasificación ABC'] = top_productos['Porcentaje Acumulado'].apply(clasificar_abc)

                    # Crear gráfico de Pareto
                    fig, ax1 = plt.subplots(figsize=(12, 6))

                    # Colores de las barras basados en la clasificación ABC
                    colors = top_productos['Clasificación ABC'].map({
                        'A': '#00FF00',  # Verde
                        'B': '#FFFF00',  # Amarillo
                        'C': '#FF0000'   # Rojo
                    })

                    ax1.bar(top_productos['Descripcion'], top_productos['Total Vendido'], color=colors, label='Total Vendido')
                    ax1.set_xlabel('Producto', fontsize=10)
                    ax1.set_ylabel('Total Vendido', color='blue', fontsize=10)
                    ax1.tick_params(axis='y', labelcolor='blue')
                    ax1.set_title('Análisis ABC de los Productos', fontsize=12)
                    ax1.tick_params(axis='x', rotation=90, labelsize=8)  # Rotar etiquetas x para mejor legibilidad

                    ax2 = ax1.twinx()
                    ax2.plot(top_productos['Descripcion'], top_productos['Porcentaje Acumulado'], color='red', marker='o', label='Porcentaje Acumulado')
                    ax2.set_ylabel('Porcentaje Acumulado (%)', color='red', fontsize=10)
                    ax2.tick_params(axis='y', labelcolor='red')

                    fig.tight_layout()
                    st.pyplot(fig)

                    # Aplicar estilo a la tabla
                    styled_df_productos = top_productos.style.applymap(color_abc, subset=['Clasificación ABC'])

                    # Mostrar la tabla en Streamlit
                    st.write("Análisis ABC de los Productos")
                    st.dataframe(styled_df_productos)

                    # --- Análisis ABC de los Vendedores ---

                    # Filtrar los vendedores con mayores ventas basadas en Total Vendido
                    top_vendedores = df_filtrado.groupby('Vendedor')['Total Vendido'].sum().nlargest(30).reset_index()

                    # Calcular el total acumulado y el porcentaje acumulado
                    top_vendedores['Total Acumulado'] = top_vendedores['Total Vendido'].cumsum()
                    top_vendedores['Porcentaje Acumulado'] = 100 * top_vendedores['Total Acumulado'] / top_vendedores['Total Vendido'].sum()

                    # Clasificar en A, B, C según el análisis Pareto (80/20)
                    top_vendedores['Clasificación ABC'] = top_vendedores['Porcentaje Acumulado'].apply(clasificar_abc)

                    # Crear gráfico de Pareto
                    fig, ax1 = plt.subplots(figsize=(12, 6))

                    # Colores de las barras basados en la clasificación ABC
                    colors = top_vendedores['Clasificación ABC'].map({
                        'A': '#00FF00',  # Verde
                        'B': '#FFFF00',  # Amarillo
                        'C': '#FF0000'   # Rojo
                    })

                    ax1.bar(top_vendedores['Vendedor'], top_vendedores['Total Vendido'], color=colors, label='Total Vendido')
                    ax1.set_xlabel('Vendedor', fontsize=10)
                    ax1.set_ylabel('Total Vendido', color='blue', fontsize=10)
                    ax1.tick_params(axis='y', labelcolor='blue')
                    ax1.set_title('Análisis ABC de los Vendedores', fontsize=12)
                    ax1.tick_params(axis='x', rotation=90, labelsize=8)  # Rotar etiquetas x para mejor legibilidad

                    ax2 = ax1.twinx()
                    ax2.plot(top_vendedores['Vendedor'], top_vendedores['Porcentaje Acumulado'], color='red', marker='o', label='Porcentaje Acumulado')
                    ax2.set_ylabel('Porcentaje Acumulado (%)', color='red', fontsize=10)
                    ax2.tick_params(axis='y', labelcolor='red')

                    fig.tight_layout()
                    st.pyplot(fig)

                    # Aplicar estilo a la tabla
                    styled_df_vendedores = top_vendedores.style.applymap(color_abc, subset=['Clasificación ABC'])

                    # Mostrar la tabla en Streamlit
                    st.write("Análisis ABC de los Vendedores")
                    st.dataframe(styled_df_vendedores)

                  
                      
                     # Verificar si la columna 'FechaPedidoServerN' está en el DataFrame
                    if 'FechaPedidoServerN' in df.columns:
                        # Asegurarse de que la columna 'FechaPedidoServerN' es de tipo datetime
                        df['FechaPedidoServerN'] = pd.to_datetime(df['FechaPedidoServerN'])
                        
                        # Crear columna de mes
                        df['Mes'] = df['FechaPedidoServerN'].dt.month_name()

                        # Agrupar ventas por mes
                        df_mes = df.groupby('Mes')['Total Vendido'].sum().reset_index().sort_values('Total Vendido', ascending=False)

                        st.subheader('Ventas Estacionales por Mes')
                        st.dataframe(df_mes, use_container_width=True)

                        # Gráfico de barras para ventas por mes
                        fig_mes, ax_mes = plt.subplots(figsize=(12, 6))
                        sns.barplot(x='Mes', y='Total Vendido', data=df_mes, ax=ax_mes, palette="summer")
                        ax_mes.set_title('Ventas Totales por Mes')
                        ax_mes.set_xlabel('Mes')
                        ax_mes.set_ylabel('Total Vendido')
                        ax_mes.tick_params(axis='x', rotation=45)

                        # Añadir etiquetas de monto en cada barra
                        for p in ax_mes.patches:
                            ax_mes.annotate(f'${p.get_height():,.0f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                                            ha='center', va='center', fontsize=10, color='black', xytext=(0, 10),
                                            textcoords='offset points')
                        st.pyplot(fig_mes)
                    else:
                        st.warning("La columna 'FechaPedidoServerN' no se encuentra en el archivo.")

                    # Configuración global para ajustar el tamaño de las etiquetas y los títulos
                    plt.rc('axes', titlesize=8)   # Tamaño del título de los gráficos
                    plt.rc('axes', labelsize=8)   # Tamaño de las etiquetas de los ejes
                    plt.rc('xtick', labelsize=8)  # Tamaño de las etiquetas de los ticks en el eje x
                    plt.rc('ytick', labelsize=8)  # Tamaño de las etiquetas de los ticks en el eje y
                    plt.rc('legend', fontsize=8)  # Tamaño de la leyenda
                    plt.rc('font', size=8)        # Tamaño de la fuente general

                    # 1. Ventas Mensuales por Vendedor (Heatmap)
                    df_filtrado['FechaPedidoServerN'] = pd.to_datetime(df_filtrado['FechaPedidoServerN'])
                    df_filtrado['Mes'] = df_filtrado['FechaPedidoServerN'].dt.to_period('M')

                    ventas_mensuales_vendedor = df_filtrado.groupby(['Vendedor', 'Mes'])['Total Vendido'].sum().unstack(fill_value=0)

                    fig, ax = plt.subplots(figsize=(8, 8))
                    sns.heatmap(ventas_mensuales_vendedor, cmap='YlGnBu', annot=True, fmt=".0f", linewidths=0.5, ax=ax)
                    ax.set_title('Ventas Mensuales por Vendedor', pad=20)
                    ax.set_xlabel('Mes', labelpad=15)
                    ax.set_ylabel('Vendedor', labelpad=15)
                    plt.xticks(rotation=45, ha='right')
                    plt.yticks(rotation=0)
                    plt.tight_layout()
                    st.pyplot(fig)

                    # 2. Participación de Mercado por Cliente (Pie Chart)
                    ventas_por_cliente = df_filtrado.groupby('Cliente')['Total Vendido'].sum().reset_index()
                    ventas_por_cliente = ventas_por_cliente.sort_values(by='Total Vendido', ascending=False).head(10)  # Top 10 Clientes

                    fig_cliente, ax_cliente = plt.subplots(figsize=(8, 6))
                    ax_cliente.pie(ventas_por_cliente['Total Vendido'], labels=ventas_por_cliente['Cliente'], autopct='%1.1f%%', startangle=140)
                    ax_cliente.axis('equal')  # Para que el gráfico sea circular
                    ax_cliente.set_title('Participación de Mercado - Top 10 Clientes', pad=20)
                    plt.tight_layout()
                    st.pyplot(fig_cliente)

                    # 3. Distribución de Ventas por Vendedor (Violin Plot)
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sns.violinplot(x='Vendedor', y='Total Vendido', data=df_filtrado, palette="muted", ax=ax)
                    ax.set_title('Distribución de Ventas por Vendedor', pad=20)
                    ax.set_xlabel('Vendedor', labelpad=15)
                    ax.set_ylabel('Total Vendido', labelpad=15)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)

                    # 4. KPI - Promedio de Ventas por Cliente
                    promedio_ventas_cliente = df_filtrado.groupby('Cliente')['Total Vendido'].sum().mean()

                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=promedio_ventas_cliente,
                        title={'text': "Promedio de Ventas por Cliente", 'font': {'size': 14}},
                        gauge={'axis': {'range': [None, df_filtrado['Total Vendido'].max()]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, promedio_ventas_cliente/2], 'color': "lightgray"},
                                {'range': [promedio_ventas_cliente/2, promedio_ventas_cliente], 'color': "gray"}],
                            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': promedio_ventas_cliente}}))

                    st.plotly_chart(fig_gauge)

                    # 5. Análisis de Descuentos (Boxplot)
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sns.boxplot(x='Vendedor', y='Descuento', data=df_filtrado, palette="Blues", ax=ax)
                    ax.set_title('Distribución de Descuentos por Vendedor', pad=20)
                    ax.set_xlabel('Vendedor', labelpad=15)
                    ax.set_ylabel('Descuento', labelpad=15)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)

                    # 6. Scatter Plot de Ventas por Unidad vs Precio
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sns.scatterplot(x='Cantidad', y='Precio', size='Total Vendido', data=df_filtrado, hue='Cliente', palette='viridis', sizes=(20, 200), ax=ax)
                    ax.set_title('Relación entre Cantidad Vendida y Precio', pad=20)
                    ax.set_xlabel('Cantidad', labelpad=15)
                    ax.set_ylabel('Precio', labelpad=15)
                    ax.legend(bbox_to_anchor=(1, 1), loc='upper left')
                    plt.tight_layout()
                    st.pyplot(fig)

                    # 7. Histograma de Frecuencia de Pedidos por Fecha
                    fig, ax = plt.subplots(figsize=(8, 6))
                    df_filtrado['FechaPedidoServerN'] = pd.to_datetime(df_filtrado['FechaPedidoServerN'])
                    df_filtrado['Fecha'] = df_filtrado['FechaPedidoServerN'].dt.date

                    sns.histplot(df_filtrado['Fecha'], bins=20, kde=False, color='blue', ax=ax)
                    ax.set_title('Frecuencia de Pedidos por Fecha', pad=20)
                    ax.set_xlabel('Fecha', labelpad=15)
                    ax.set_ylabel('Número de Pedidos', labelpad=15)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)

                    # 8. Bubble Chart de Ventas por Localidad
                    df_localidad = df_filtrado.groupby('Localidad Nombre').agg({'Total Vendido':'sum', 'Cantidad':'sum'}).reset_index()

                    fig, ax = plt.subplots(figsize=(8, 6))
                    sns.scatterplot(x='Cantidad', y='Total Vendido', size='Total Vendido', data=df_localidad, hue='Localidad Nombre', palette='coolwarm', sizes=(50, 500), ax=ax)
                    ax.set_title('Ventas por Localidad', pad=20)
                    ax.set_xlabel('Cantidad Vendida', labelpad=15)
                    ax.set_ylabel('Total Vendido', labelpad=15)
                    ax.legend(bbox_to_anchor=(1, 1), loc='upper left')
                    plt.tight_layout()
                    st.pyplot(fig)  
                    

               # Convertir la columna 'FechaPedidoServerN' a formato datetime
                df['FechaPedidoServerN'] = pd.to_datetime(df['FechaPedidoServerN'], format='%d/%m/%Y')

                # Crear una columna para el mes y año
                df['Mes'] = df['FechaPedidoServerN'].dt.to_period('M')

                # Mostrar una lista de productos y clientes disponibles en el sidebar
                productos_disponibles = df['Descripcion'].unique()
                clientes_disponibles = df['Cliente'].unique()

                # Selección de producto y cliente
                producto = st.sidebar.selectbox('Selecciona el Producto', options=productos_disponibles)
                cliente = st.sidebar.selectbox('Selecciona el Cliente', options=clientes_disponibles)

                # Análisis para el producto seleccionado
                def analizar_producto(producto):
                    # Agrupar por mes y producto, y sumar las ventas
                    df_producto_mensual = df.groupby(['Descripcion', 'Mes'])['Total Vendido'].sum().reset_index()

                    # Filtrar datos para el producto seleccionado
                    df_producto = df_producto_mensual[df_producto_mensual['Descripcion'] == producto]

                    # Verifica si hay suficientes datos
                    if df_producto.shape[0] >= 12:  # Necesitamos al menos 12 meses de datos
                        # Establecer 'Mes' como el índice
                        df_producto.set_index('Mes', inplace=True)
                        df_producto.index = df_producto.index.to_timestamp()
                        
                        # Verifica si hay suficientes datos para estacionalidad
                        if len(df_producto) >= 24:
                            # Usar estacionalidad solo si hay suficientes datos
                            model = ExponentialSmoothing(df_producto['Total Vendido'], seasonal='add', seasonal_periods=12)
                        else:
                            # Usar un modelo sin estacionalidad si hay menos de 24 meses
                            model = ExponentialSmoothing(df_producto['Total Vendido'], trend='add', seasonal=None)
                        
                        model_fit = model.fit()
                        
                        # Pronóstico
                        forecast_steps = 12  # Proyección para los próximos 12 meses
                        forecast_index = pd.date_range(start=df_producto.index[-1] + pd.DateOffset(months=1), periods=forecast_steps, freq='M')
                        forecast = model_fit.forecast(steps=forecast_steps)
                        
                        # Crear una tabla pivotante
                        df_pivot = df_producto.copy()
                        df_pivot = df_pivot.reset_index()
                        df_pivot = df_pivot.rename(columns={'Total Vendido': 'Ventas Actuales'})
                        
                        # Añadir proyección al DataFrame
                        df_forecast = pd.DataFrame({'Mes': forecast_index, 'Proyección': forecast})
                        df_pivot = pd.concat([df_pivot, df_forecast], ignore_index=True)
                        df_pivot.set_index('Mes', inplace=True)
                        
                        # Mostrar la tabla pivotante en Streamlit
                        st.write('**Proyecciones de Ventas por Mes**')
                        st.dataframe(df_pivot, use_container_width=True)

                        # Gráfico de las ventas actuales y la proyección
                        fig, ax = plt.subplots(figsize=(12, 6))
                        ax.plot(df_producto.index, df_producto['Total Vendido'], label='Ventas Actuales', marker='o')
                        ax.plot(forecast_index, forecast, label='Proyección', marker='o', linestyle='--')
                        ax.set_title(f'Proyección de Ventas para {producto}', fontsize=16)
                        ax.set_xlabel('Fecha', fontsize=12)
                        ax.set_ylabel('Total Vendido', fontsize=12)
                        ax.legend()
                        ax.grid(True)
                        
                        # Mostrar el gráfico en Streamlit
                        st.pyplot(fig)
                    else:
                        st.error(f"No hay suficientes datos para el producto {producto} para realizar la proyección.")

                # Análisis para el cliente seleccionado
                def analizar_cliente(cliente):
                    # Agrupar por mes y cliente, y sumar las ventas
                    df_cliente_mensual = df.groupby(['Cliente', 'Mes'])['Total Vendido'].sum().reset_index()

                    # Filtrar datos para el cliente seleccionado
                    df_cliente = df_cliente_mensual[df_cliente_mensual['Cliente'] == cliente]

                    # Verifica si hay suficientes datos
                    if df_cliente.shape[0] >= 12:  # Necesitamos al menos 12 meses de datos
                        # Establecer 'Mes' como el índice
                        df_cliente.set_index('Mes', inplace=True)
                        df_cliente.index = df_cliente.index.to_timestamp()
                        
                        # Verifica si hay suficientes datos para estacionalidad
                        if len(df_cliente) >= 24:
                            # Usar estacionalidad solo si hay suficientes datos
                            model = ExponentialSmoothing(df_cliente['Total Vendido'], seasonal='add', seasonal_periods=12)
                        else:
                            # Usar un modelo sin estacionalidad si hay menos de 24 meses
                            model = ExponentialSmoothing(df_cliente['Total Vendido'], trend='add', seasonal=None)
                        
                        model_fit = model.fit()
                        
                        # Pronóstico
                        forecast_steps = 12  # Proyección para los próximos 12 meses
                        forecast_index = pd.date_range(start=df_cliente.index[-1] + pd.DateOffset(months=1), periods=forecast_steps, freq='M')
                        forecast = model_fit.forecast(steps=forecast_steps)
                        
                        # Crear una tabla pivotante
                        df_pivot = df_cliente.copy()
                        df_pivot = df_pivot.reset_index()
                        df_pivot = df_pivot.rename(columns={'Total Vendido': 'Ventas Actuales'})
                        
                        # Añadir proyección al DataFrame
                        df_forecast = pd.DataFrame({'Mes': forecast_index, 'Proyección': forecast})
                        df_pivot = pd.concat([df_pivot, df_forecast], ignore_index=True)
                        df_pivot.set_index('Mes', inplace=True)
                        
                        # Mostrar la tabla pivotante en Streamlit
                        st.write('**Proyecciones de Ventas por Cliente**')
                        st.dataframe(df_pivot, use_container_width=True)

                        # Gráfico de las ventas actuales y la proyección
                        fig, ax = plt.subplots(figsize=(12, 6))
                        ax.plot(df_cliente.index, df_cliente['Total Vendido'], label='Ventas Actuales', marker='o')
                        ax.plot(forecast_index, forecast, label='Proyección', marker='o', linestyle='--')
                        ax.set_title(f'Proyección de Ventas para el Cliente {cliente}', fontsize=16)
                        ax.set_xlabel('Fecha', fontsize=12)
                        ax.set_ylabel('Total Vendido', fontsize=12)
                        ax.legend()
                        ax.grid(True)
                        
                        # Mostrar el gráfico en Streamlit
                        st.pyplot(fig)
                    else:
                        st.error(f"No hay suficientes datos para el cliente {cliente} para realizar la proyección.")

                # Llamar a las funciones de análisis
                analizar_producto(producto)
                analizar_cliente(cliente)            
                                            


                

       

                # Cargar FontAwesome
                st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">', unsafe_allow_html=True)

               

                # Título para la sección final
                st.markdown("<h1 style='text-align: center; color: #fffa65;'>QUIÉN SOY?</h1>", unsafe_allow_html=True)


                # Mostrar la foto centrada
                st.markdown("""
                    <div style="text-align: center;">
                        <img src="https://raw.githubusercontent.com/JUANCITOPENA/ANALISIS_AUTOMATIZADO_PYTHON/main/JuancitoFoto.png" 
                            alt="Foto de Juancito Peña" 
                            style="width: 200px; height: auto; border-radius: 50%;">
                    </div>
                """, unsafe_allow_html=True)
                
               # Texto de presentación con estilo personalizado
                st.markdown("""
                   <p style='font-size: 25px; color: #ecf0f1; text-align: justify;'>
                    Mi nombre es <strong>Juancito Peña V</strong>, soy <strong>ingeniero en Sistemas y Computación</strong> 💻, con una Especialidad en <strong>Desarrollo de Software</strong> 🖥️, y una Maestría en <strong>Sistemas Mención Gerencial</strong> 🎓. 
                    Actualmente estoy cursando una Maestría en <strong>Ciencia de Datos para Negocios</strong> 📊 (Big Data & Business Analytics). 
                    He realizado varios cursos y certificaciones, soy un amante de la <strong>Tecnología</strong> 🚀, de los <strong>Datos</strong> 📈 y de la <strong>Programación</strong> 👨‍💻. 
                    Creo en el poder de la tecnología para aportar valor a las personas, a las empresas y a la educación 🎓.
                    </p>
                    <p style='font-size: 25px; color: #ecf0f1; text-align: justify;'>
                    Mis Habilidades van desde Uso con en <strong>SQL</strong> 💾, <strong>Power BI</strong> 📊 y <strong>Python</strong> 🐍 | <strong>Desarrollo de Software</strong> (HTML, CSS, JS, REACT, PHP, C#) 💻, SQL | <strong>Soy Instructor de Grado Universitario</strong> 👨‍🏫, <strong>Padre</strong> 👨‍👩‍👧‍👦 y <strong>Amigo</strong> 🤝.
                   </p>
                </p>
                """, unsafe_allow_html=True)



               # Iconos de redes sociales en línea horizontal
                st.markdown("""
                <div style="text-align: center;">
                    <a href="https://www.linkedin.com/in/tu-perfil" target="_blank" style="text-decoration: none; color: #fff200; margin: 0 10px;">
                        <i class="fab fa-linkedin" style="font-size: 48px;"></i>
                    </a>
                    <a href="https://www.youtube.com/channel/tu-canal" target="_blank" style="text-decoration: none; color: #fff200; margin: 0 10px;">
                        <i class="fab fa-youtube" style="font-size: 48px;"></i>
                    </a>
                    <a href="https://github.com/tu-perfil" target="_blank" style="text-decoration: none; color: #fff200; margin: 0 10px;">
                        <i class="fab fa-github" style="font-size: 48px;"></i>
                    </a>
                    <a href="https://twitter.com/tu-perfil" target="_blank" style="text-decoration: none; color: #fff200; margin: 0 10px;">
                        <i class="fab fa-twitter" style="font-size: 48px;"></i>
                    </a>
                    <a href="https://www.facebook.com/tu-perfil" target="_blank" style="text-decoration: none; color: #fff200; margin: 0 10px;">
                        <i class="fab fa-facebook" style="font-size: 48px;"></i>
                    </a>
                    <a href="https://www.instagram.com/tu-perfil" target="_blank" style="text-decoration: none; color: #fff200; margin: 0 10px;">
                        <i class="fab fa-instagram" style="font-size: 48px;"></i>
                    </a>
                </div>
                """, unsafe_allow_html=True)


               # Mensaje de contacto con estilo personalizado
                st.markdown("""
                    <p style='font-size: 25px; color: #ecf0f1; text-align: center; margin-top: 20px;'>
                    Si te interesa este Reporte y tenerlo en tus proyectos, contáctame al: 
                    <a href="mailto:juancito.pena@gmail.com" style='color: #1f77b4;'>juancito.pena@gmail.com</a>. Acordemos un precio.
                    </p>
                """, unsafe_allow_html=True)
