# Chatbot de Análisis de Datos con Llama 3.1 y LangGraph

Este proyecto es un chatbot de análisis de datos que permite a los usuarios interactuar con archivos `.csv` mediante lenguaje natural, eliminando la necesidad de conocimientos técnicos sobre manipulación de datos. El sistema, basado en el modelo Llama 3.1 y una arquitectura de LangGraph, ofrece una interfaz intuitiva y herramientas personalizadas (`tools`) para realizar operaciones complejas de datos de manera sencilla.

## Características Principales

- **Procesamiento de CSV a través de lenguaje natural**: permite realizar operaciones de limpieza, extracción, y transformación de datos sin necesidad de programación.
- **Generación de gráficas**: el chatbot genera visualizaciones de datos, facilitando el análisis y la comprensión de los patrones en los datos.
- **Backend con Lógica de Agente y Tools**: la lógica del chatbot está implementada con LangGraph y cuenta con un conjunto de herramientas personalizadas para manipular y visualizar datos.
- **Despliegue Docker**: el proyecto está estructurado en microservicios independientes para el modelo, el backend y el frontend, y todos se despliegan en contenedores Docker utilizando `docker-compose`.

## Estructura del Proyecto

- **Backend**: Implementado con FastAPI, contiene toda la lógica del agente y la implementación de `tools` que soportan las operaciones del chatbot.
- **Frontend**: Interfaz de usuario diseñada para una interacción intuitiva con el agente, donde el usuario puede cargar archivos `.csv`, visualizar resultados y recibir recomendaciones del chatbot.
- **Modelo Llama 3.1**: Modelo de lenguaje que entiende y responde a comandos en lenguaje natural, entrenado para entender consultas relacionadas con datos.
- **Despliegue en Docker**: Cada componente del proyecto está configurado en un contenedor Docker independiente con su respectivo `Dockerfile`, permitiendo un despliegue ágil y reproducible.

Este proyecto busca simplificar el análisis de datos para usuarios que necesitan realizar consultas y transformaciones de archivos `.csv` de manera eficiente y sin conocimientos técnicos de programación o manipulación de datos.
# Agente de Análisis de Datos Basado en Llama 3.1

Este proyecto es un agente de análisis de datos diseñado para interactuar con el usuario mediante lenguaje natural y realizar modificaciones, análisis, y visualizaciones en archivos de datos. Basado en el modelo Llama 3.1 y en una arquitectura de flujo de estados, este agente permite que los usuarios consulten y manipulen sus datos sin requerir conocimientos técnicos avanzados.

El agente es capaz de ejecutar múltiples herramientas en una sola consulta si la operación lo requiere, lo que le permite resolver operaciones complejas a partir de un único prompt del usuario. Cada modelo recibe una instrucción específica para guiar su comportamiento y garantizar que interprete el prompt correctamente, optimizando así la precisión de las respuestas y la experiencia del usuario.

![Diagrama del grafo de estados del agente](graph.png)

## Arquitectura del Agente

El agente utiliza una arquitectura basada en un grafo de estados (`StateGraph`) que dirige el flujo de la conversación según las intenciones y necesidades del usuario. Este grafo asegura que el agente siga un flujo lógico en cada interacción, ayudándole a identificar la intención principal y a guiar sus respuestas de manera precisa.

### Proceso de un Prompt a Través del Grafo

1. **Inicio del Grafo**: Todo comienza en el nodo `start_node`, donde el agente evalúa la intención general del prompt del usuario.
2. **Evaluación de Intención**: En el nodo `start_node`, el agente determina si la intención del usuario es:
   - Relacionada con datos (`data_related`): Lo cual inicia la navegación hacia operaciones sobre los datos.
   - Ayuda al usuario (`help_user`): Cuando el usuario necesita una guía sobre el agente.
   - No relacionada (`prompt_unrelated`): Cuando la solicitud no está relacionada con el análisis de datos.
3. **Selección de Operación**: Si la intención es `data_related`, el flujo se divide en diferentes nodos según el tipo de operación solicitada, como `data_modification`, `process_na_values`, `create_analysis`, o `create_graphics`.
4. **Ejecutar la Operación**: Cada nodo correspondiente a una operación dirige el flujo hacia herramientas específicas y genera los resultados en función de los datos y la solicitud del usuario.

## Modelos y Herramientas Especializadas

Para gestionar la variedad de herramientas disponibles, el agente utiliza cinco modelos distintos. Esto facilita la selección de la herramienta adecuada para cada tarea específica. Los modelos son los siguientes:

- **Modelo de Modificación de Datos** (`data_modification`): Se utiliza para operaciones de modificación de datos, como filtrar, eliminar columnas, o modificar valores.
- **Modelo para Procesar Valores Faltantes** (`process_na_values`): Este modelo es responsable de manejar valores faltantes mediante imputación o técnicas de reemplazo.
- **Modelo de Análisis de Datos** (`create_analysis`): Realiza análisis estadísticos, cálculos de correlación, y detección de valores atípicos, entre otras tareas.
- **Modelo para Visualización de Datos** (`create_graphics`): Encargado de generar gráficos y representaciones visuales basadas en los datos.
- **Modelo sin Herramientas** (`help_user`): Este modelo es especial porque no incluye herramientas, y se utiliza únicamente para ayudar al usuario. Debido a que Llama 3.1 tiende a forzar el uso de herramientas cuando están disponibles, este modelo se crea específicamente para responder preguntas sobre el agente sin intentar invocar herramientas.

### Funcionamiento del Grafo de Estados

A continuación se detalla el flujo de estados del agente, representado visualmente en la imagen `graph.png`:
1. El prompt del usuario es evaluado y clasificado en `start_node`.
2. Dependiendo de la intención, el flujo se dirige a:
   - `data_modification`: Para operaciones de modificación de datos.
   - `process_na_values`: Para gestionar valores faltantes.
   - `create_analysis`: Para ejecutar análisis de datos.
   - `create_graphics`: Para crear visualizaciones.
   - `help_user`: Para guiar al usuario.
   - `prompt_unrelated`: Cuando la solicitud no está relacionada con los datos.

Esta estructura garantiza que el agente mantenga un flujo lógico y eficiente en sus interacciones, permitiéndole responder a consultas complejas de manera precisa y ordenada.

## Clase `DataExtractor`

La clase `DataExtractor` es responsable de extraer información esencial del archivo de datos (`CSV`) cargado por el usuario. Esta información es utilizada por el agente para tomar decisiones informadas durante el procesamiento y análisis de datos. `DataExtractor` realiza una evaluación inicial de los datos para identificar características importantes, como los nombres de las columnas, los tipos de datos, y la cantidad de valores faltantes (`NA`). También organiza y provee una serie de herramientas para realizar modificaciones, análisis, y visualizaciones de los datos, y para manejar valores faltantes.

### Funciones Principales de `DataExtractor`

1. **Extracción de Información**: `DataExtractor` extrae y almacena los nombres de las columnas, tipos de datos, y la cantidad de valores faltantes para cada columna en un diccionario llamado `columns`. Esto ayuda al agente a seleccionar las herramientas adecuadas basadas en el tipo de dato o en si existen valores faltantes.

2. **Procesamiento de Tipos de Datos**: La clase realiza conversiones automáticas de tipos de datos, como la identificación y conversión de fechas en formato de texto a tipos `datetime`.

3. **Herramientas Disponibles**: `DataExtractor` organiza las herramientas en cuatro módulos: `data_modifications_tools`, `process_na_values_tools`, `data_analysis_tools`, y `data_graphics_tools`. Cada módulo contiene herramientas específicas que se pueden invocar para realizar tareas concretas en los datos.

### Módulos y Herramientas de `DataExtractor`

#### Herramientas de Modificación de Datos (`data_modifications_tools`)

Estas herramientas permiten realizar transformaciones y filtrados en el conjunto de datos:

- **tool_data_range**: Filtra los datos en un rango de fechas específico.
- **tool_get_current_date**: Devuelve la fecha actual en formato `dd-mm-yyyy`.
- **tool_operation_date**: Suma o resta años a una fecha dada.
- **tool_filter_string**: Filtra filas en una columna en base a coincidencias de texto.
- **tool_filter_numeric**: Filtra filas en una columna numérica según un operador de comparación (`>`, `<`, `=`, `>=`, `<=`).
- **tool_filter_date**: Filtra filas en una columna de fecha en base al año, mes, o día.
- **tool_drop_column**: Elimina una columna específica del conjunto de datos.

#### Herramientas para Procesar Valores Faltantes (`process_na_values_tools`)

Estas herramientas permiten gestionar valores faltantes (`NA`) en el conjunto de datos:

- **tool_missing_values**: Muestra el porcentaje de valores faltantes en cada columna.
- **tool_impute_mean_median**: Imputa valores faltantes en una columna numérica utilizando la media o la mediana.
- **tool_knn_imputation**: Realiza imputación de valores faltantes mediante el método de K-Nearest Neighbors.
- **tool_interpolation**: Realiza interpolación lineal o polinómica en una columna de series temporales.
- **tool_impute_mode**: Imputa valores faltantes en una columna categórica utilizando el valor más frecuente.
- **tool_impute_placeholder**: Rellena valores faltantes en una columna categórica con un marcador de posición (por defecto, `"Unknown"`).
- **tool_forward_backward_fill**: Realiza una imputación hacia adelante o hacia atrás en una columna de fecha.

#### Herramientas de Análisis de Datos (`data_analysis_tools`)

Estas herramientas realizan análisis estadísticos y exploratorios en los datos:

- **tool_descriptive_statistics**: Proporciona estadísticas descriptivas básicas para una columna numérica.
- **tool_correlation_matrix**: Calcula y muestra la matriz de correlación para columnas numéricas, y destaca las 5 columnas más correlacionadas con la columna de interés.
- **tool_value_counts**: Proporciona la distribución de frecuencias de una columna.
- **tool_outlier_detection**: Detecta valores atípicos en una columna numérica usando el método IQR.
- **tool_trend_analysis**: Realiza un análisis de tendencia en una columna de series temporales mediante un promedio móvil.

#### Herramientas de Visualización de Datos (`data_graphics_tools`)

Estas herramientas generan gráficos basados en los datos para proporcionar representaciones visuales:

- **tool_bar_chart**: Crea un gráfico de barras para una columna categórica.
- **tool_histogram**: Crea un histograma para una columna numérica o un gráfico de barras para una columna categórica.
- **tool_line_chart**: Crea un gráfico de líneas con el índice en el eje X y los valores de una columna numérica en el eje Y.
- **tool_scatter_plot**: Crea un gráfico de dispersión con el índice en el eje X y los valores de una columna numérica en el eje Y.

### Integración de Herramientas y Utilización

La clase `DataExtractor` almacena todas las herramientas en un diccionario llamado `tools`, donde cada herramienta está identificada por su nombre. Esto permite que el agente acceda a ellas de forma dinámica durante su funcionamiento, invocando la herramienta adecuada en función del prompt del usuario y la naturaleza de los datos en análisis.

# API de Manipulación y Análisis de Datos

Esta API permite a los usuarios cargar un archivo CSV, interactuar con un modelo de lenguaje para modificar y analizar los datos, y descargar gráficos y el archivo CSV modificado. 

## Endpoints y Funcionalidad

### 1. `http://backend/upload-csv/{user_id}` - Cargar CSV e Inicializar el Bot
- **Método**: `POST`
- **Funcionalidad**: Permite cargar un archivo CSV y configurar el bot con los datos del archivo para una sesión de usuario específica.
- **Parámetros**: 
  - `user_id` (path): Identificador único del usuario.
  - `file` (form-data): El archivo CSV a cargar.
- **Respuesta**: Confirma la carga del archivo y la inicialización del bot.

### 2. `http://backend/chat/{user_id}` - Interactuar con el Bot
- **Método**: `POST`
- **Funcionalidad**: Envía un mensaje al bot en lenguaje natural y recibe una respuesta, que puede ser texto o un gráfico.
- **Parámetros**:
  - `user_id` (path): Identificador único del usuario.
  - `prompt` (json): Mensaje o pregunta para el bot.
- **Respuesta**: Mensaje de texto o imagen generada según la solicitud.

### 3. `http://backend/download-charts/{user_id}` - Descargar Todos los Gráficos
- **Método**: `GET`
- **Funcionalidad**: Permite descargar un archivo ZIP con todos los gráficos generados durante la sesión de usuario.
- **Parámetros**:
  - `user_id` (path): Identificador único del usuario.
- **Respuesta**: Archivo ZIP con los gráficos generados.

### 4. `http://backend/data-head-image/{user_id}` - Ver Cabecera del DataFrame
- **Método**: `GET`
- **Funcionalidad**: Devuelve una imagen con las primeras filas del archivo CSV cargado, útil para previsualizar los datos.
- **Parámetros**:
  - `user_id` (path): Identificador único del usuario.
- **Respuesta**: Imagen en formato PNG con las primeras filas del DataFrame.

### 5. `http://backend/download-csv/{user_id}` - Descargar CSV Modificado
- **Método**: `GET`
- **Funcionalidad**: Permite descargar el archivo CSV con los datos modificados durante la sesión.
- **Parámetros**:
  - `user_id` (path): Identificador único del usuario.
- **Respuesta**: Archivo CSV con los datos actualizados y modificados.

## Docker

La aplicación está compuesta por tres contenedores Docker, definidos en el archivo `docker-compose.yaml`. Cada uno tiene un rol específico y se comunican entre ellos a través de una red de Docker llamada `app-network`.

### Contenedores

1. **frontend**:
   - Ejecuta la interfaz de usuario desarrollada en React.
   - Expone el puerto `3000` para que el usuario pueda acceder a la aplicación web.
   - Depende del servicio `backend`, por lo que no se inicia hasta que el backend esté disponible.
   - Se comunica con el backend a través de la red `app-network`.

2. **backend**:
   - Contiene la API de FastAPI que maneja la lógica del agente y las operaciones con el CSV.
   - Expone el puerto `8000` para aceptar solicitudes desde el `frontend`.
   - Depende del contenedor `ollama`, que se utiliza para la inferencia del modelo.
   - Se conecta a `ollama` y al `frontend` mediante `app-network`.

3. **ollama**:
   - Este contenedor es responsable de ejecutar el modelo Llama3.1 para responder a los prompts.
   - Requiere una GPU, por lo que utiliza `runtime: nvidia` y define `NVIDIA_VISIBLE_DEVICES=all`.
   - Expone el puerto `11434`, permitiendo que el `backend` envíe solicitudes para obtener respuestas del modelo.
   - Incluye un script `wait_for_ollama.sh` que espera a que el modelo esté disponible antes de aceptar conexiones.

### Ejecución

Para iniciar la aplicación, simplemente ejecuta el siguiente comando:

```bash
docker-compose up



