import pandas as pd
from data_extractor import DataExtractor
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM, ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from Agent import Agent

business_description = "In this competition, you will predict sales for the thousands of product families sold at Favorita stores located in Ecuador. \
The training data includes dates, store and product information, whether that item was being promoted, as well as the sales numbers. \
Additional files include supplementary information that may be useful in building your models. \
The training data, comprising time series of features store_nbr, family, and onpromotion as well as the target sales. \
store_nbr identifies the store at which the products are sold. \
family identifies the type of product sold. \
sales gives the total sales for a product family at a particular store at a given date. Fractional values are possible since products can be sold in fractional units (1.5 kg of cheese, for instance, as opposed to 1 bag of chips). \
onpromotion gives the total number of items in a product family that were being promoted at a store at a given date. \
Store metadata, including city, state, type, and cluster. \
cluster is a grouping of similar stores. \
Daily oil price. Includes values during both the train and test data timeframes. (Ecuador is an oil-dependent country and its economic health is highly vulnerable to shocks in oil prices.) \
Holidays and Events, with metadata."

instruction = """
You are a smart data assistant. When you receive a request to filter data by a date range, 
you must **call the tool** `tool_data_range` directly, passing the column name, start date, and end date.
Do not explain the code or provide an example. You must invoke the tool with the provided arguments.
"""

memory = SqliteSaver.from_conn_string(":memory:")
model = ChatOllama(model="llama3.1", temperature=0)

data_extractor = DataExtractor("sales_data.csv",'sales')



bot = Agent(model,data_extractor.tools,system=instruction, checkpointer=None)
print(bot.tools)
messages = [HumanMessage(content="I want my data since the 2-06-2014 to 3-07-2015, in the column called date")]
thread= {"configurable": {"thread_id":"1"}}
for event in bot.graph.stream({"messages":messages},thread):
    for v in event.values():
        
        print(v["messages"])

print(data_extractor.data.head())
# Hacer una consulta al modelo
#prompt = str(instruction) + str(business_description) + str(data_extractor.columns) + str(data_extractor.na_sums)
#print(prompt)
#print("-------------GENERANDO RESPUESTA-----------------")
# Ejecutar el modelo para generar una respuesta
#response = model.invoke(input=prompt)
#print(response)