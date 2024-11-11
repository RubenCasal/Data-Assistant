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
