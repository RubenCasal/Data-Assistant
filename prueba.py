from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from agent_llm import Agent  # Asegúrate de que este importe esté correctamente configurado según la ubicación de tu script
from data_extractor import DataExtractor  # Asumiendo que esta es tu clase para manejar la carga de datos
import pandas as pd
# Configuración del modelo


data_extractor = DataExtractor(csv_file='sales_data.csv',target_column='sales')

print(data_extractor.columns)