# Análisis de Ventas Automatizado

Este repositorio contiene un script en Python diseñado para realizar un análisis de ventas exhaustivo basado en datos de clientes, productos y vendedores. A continuación, se detalla cómo usar el script, incluyendo la instalación de dependencias y la ejecución del análisis.

## Descripción del Proyecto

El script realiza un análisis de ventas utilizando el método ABC para clasificar clientes, productos y vendedores según su impacto en el total de ventas. Presenta visualizaciones gráficas y tablas estilizadas para facilitar la interpretación de los resultados.

## Requisitos

Para ejecutar el script, necesitas tener Python instalado en tu sistema. Además, se deben instalar las siguientes dependencias:

- **Pandas**: Para la manipulación y análisis de datos.
- **Matplotlib**: Para la creación de gráficos y visualizaciones.
- **Streamlit**: Para la creación de aplicaciones web interactivas y visualización de datos.

## Instalación

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/JUANCITOPENA/ANALISIS_DE_VENTAS_AUTOMATIZADO.git
   cd ANALISIS_DE_VENTAS_AUTOMATIZADO
Crea un entorno virtual (opcional pero recomendado):

bash
Copy code
python -m venv env
source env/bin/activate  # En Windows usa `env\Scripts\activate`
Instala las dependencias:

Asegúrate de tener pip actualizado:
bash
Copy code
pip install --upgrade pip
Instala las dependencias listadas en requirements.txt:
bash
Copy code
pip install -r requirements.txt
Contenido de requirements.txt:

Copy code
pandas
matplotlib
streamlit
Uso
Prepara tu archivo de datos:

Asegúrate de tener un archivo de Excel o CSV con los datos de ventas. El archivo debe tener columnas como Cliente, Total Vendido, Descripcion, Vendedor, etc.
Modifica el script si es necesario:

Asegúrate de que el script ANALISIS_DATOS.py apunte a la ubicación correcta de tu archivo de datos.
Ejecuta el script:

bash
Copy code
streamlit run ANALISIS_DATOS.py
Esto abrirá una aplicación web en tu navegador donde podrás interactuar con el análisis de ventas.

Descripción del Script
El script realiza las siguientes acciones:

Filtra los 30 principales clientes, productos y vendedores basándose en el total vendido.
Calcula el total acumulado y el porcentaje acumulado para cada elemento.
Clasifica los elementos en categorías A, B y C usando el análisis Pareto.
Genera gráficos de Pareto para clientes, productos y vendedores.
Aplica estilos a las tablas en Streamlit para resaltar la clasificación ABC.
Análisis de Clientes
Gráfico de Pareto: Muestra el total vendido y el porcentaje acumulado para los 30 mejores clientes.
Tabla Estilizada: Resalta la clasificación ABC de cada cliente.
Análisis de Productos
Gráfico de Pareto: Muestra el total vendido y el porcentaje acumulado para los 30 principales productos.
Tabla Estilizada: Resalta la clasificación ABC de cada producto.
Análisis de Vendedores
Gráfico de Pareto: Muestra el total vendido y el porcentaje acumulado para los 30 principales vendedores.
Tabla Estilizada: Resalta la clasificación ABC de cada vendedor.
Contribuciones
Si deseas contribuir a este proyecto, por favor realiza un fork del repositorio y envía tus pull requests. Asegúrate de seguir las buenas prácticas de codificación y de probar tus cambios antes de enviarlos.

Licencia
Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo LICENSE para obtener más detalles.

Contacto
Para cualquier consulta o soporte, puedes contactar a Juancito Peña.

