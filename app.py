import streamlit as st
import pandas as pd
from data_extractor import DataExtractor
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
#from agent_llm import Agent  
from new_agent_llm import Agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles
import requests
import io
from PIL import Image
import matplotlib.pyplot as plt
import os

# Inicializar session_state para el bot, extractor de datos y mensajes
if 'bot' not in st.session_state:
    st.session_state.bot = None
if 'data_extractor' not in st.session_state:
    st.session_state.data_extractor = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'checkpointer' not in st.session_state:
    st.session_state.checkpointer = MemorySaver()
if 'data_head' not in st.session_state:
    st.session_state.data_head = None


# Paso 1: Cargar CSV y descripción del negocio
st.title("Interacción con el Agente - Subir CSV y Descripción")

# Descripción del negocio
business_description = st.text_area("Describe el problema de tu negocio")

# Subida del archivo CSV
uploaded_file = st.file_uploader("Subir archivo CSV", type=["csv"])

# Botón para cargar el archivo y inicializar el agente
if st.button("Cargar archivo y descripción"):
    if uploaded_file is not None and business_description:
        try:
            # Inicialización del extractor de datos y el agente
            print(business_description)
            st.session_state.data_extractor = DataExtractor(uploaded_file, 'sales')  # Ajusta la columna objetivo si es necesario
          
            model = ChatOllama(model="llama3.1", temperature=0)
            st.session_state.bot = Agent(
                model=model,
                business_description=business_description, 
                data_extractor=st.session_state.data_extractor,
                data_modifications_tools= st.session_state.data_extractor.data_modifications_tools,
                process_na_value_tools= st.session_state.data_extractor.process_na_values_tools,
                data_analysis_tools= st.session_state.data_extractor.data_analysis_tools,
                data_graphics_tools= st.session_state.data_extractor.data_graphics_tools,
                system='',
                checkpointer=st.session_state.checkpointer)
            
            st.success("Archivo CSV y descripción cargados con éxito.")
            st.session_state.data_head = st.session_state.data_extractor.data.head()
         

            welcome_message = SystemMessage(content="Hi, I'm your data assistant. What can I do for you?")
            st.session_state.messages.append(welcome_message)
            
            
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
    else:
        st.error("Por favor, sube un archivo CSV y proporciona una descripción.")

if st.session_state.data_head is not None:
    st.write("Primeras filas del CSV:")
    st.write(st.session_state.data_extractor.data.head())

# Paso 2: Interacción conversacional con el agente
if st.session_state.bot:
    st.title("Chat con el Agente")

    thread = {"configurable": {"thread_id": "1"}}
    
    for message in st.session_state.messages:
        if isinstance(message, SystemMessage):
            role = "assistant"
            content = message.content
        elif isinstance(message, HumanMessage):
            role = "user"
            content = message.content
        else:
            continue  # Ignorar mensajes desconocidos

        with st.chat_message(role):
            st.markdown(content)

    # Entrada del usuario (chat)
    if user_message := st.chat_input("Escribe tu mensaje:"):
        # Agregar el mensaje del usuario al historial de mensajes
        human_message = HumanMessage(content=user_message)
        st.session_state.messages.append(human_message)
        st.session_state.bot.graph.update_state(thread,{"messages": [human_message]})

        # Mostrar mensaje del usuario en el chat
        with st.chat_message("user"):
            st.markdown(user_message)

        # Obtener respuesta del agente
        with st.chat_message("assistant"):
            try:
                thread = {"configurable": {"thread_id": "1"}}
               
                for event in st.session_state.bot.graph.stream({"messages": st.session_state.messages}, thread):
                    for v in event.values():
                        if v:
                            print(v)
                            print(v["messages"][0])
                  
                            response_content = v["messages"][0].content

                            if response_content.startswith("Figure:"):
                                # Extract the chart name from the message
                                chart_name = response_content.split("Figure: ")[1].strip()
                                chart_path = os.path.join('./graphs', chart_name)
                        
                                # Check if the file exists and display the image
                                if os.path.exists(chart_path):
                                    st.session_state.messages.append(SystemMessage(content="Graph generated"))
                                    image = Image.open(chart_path)
                                    st.image(image)
                                else:
                                    st.error(f"Graph '{chart_name}' not found.")
                            
                            else:
                                # It's a regular text message
                                st.session_state.messages.append(SystemMessage(content=response_content))
                                st.markdown(response_content)
                            
        
              
                # Agregar la respuesta al historial de mensajes
                
            except Exception as e:
                
                st.error(f"Error al procesar el mensaje: {e}")
