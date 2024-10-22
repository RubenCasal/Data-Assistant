from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from typing import TypedDict, Annotated


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class Agent:
    def __init__(self, model,business_description, tools, data_extractor,system="", checkpointer=None):
        self.data_extractor = data_extractor
        print(business_description)
        self.business_description = business_description
        self.system = ''
        self.na_values = {}

     
        self.checkpointer = checkpointer
        print(checkpointer)
        ############ GRAPH ########
        graph = StateGraph(AgentState)
        graph.add_node("starting_point", self.start_point)
        graph.add_node("decide_if_data_range",self.decide_if_data_range)
        graph.add_node("user_input_data_range", self.user_input_data_range)
        graph.add_node("declare_data_range", self.declare_data_range)
        graph.add_node("user_input_declare_data_range", self.user_input_declare_data_range)
        graph.add_node("process_missing_values", self.process_missing_values)
        graph.add_node("clean_data",self.clean_data)

        graph.add_conditional_edges("starting_point",self.has_datetimes,{True:'decide_if_data_range',False:'clean_data'})
        graph.add_conditional_edges('user_input_data_range',self.has_intention_data_range,{True:'declare_data_range', False:'process_missing_values'})
        graph.add_edge("decide_if_data_range","user_input_data_range")
        graph.add_edge("declare_data_range", "user_input_declare_data_range")
        graph.add_conditional_edges('user_input_declare_data_range',self.has_missing_values,{True:'process_missing_values',False:'llm'})
       
        #graph.add_edge('user_input_declare_data_range','llm')
        graph.add_edge("clean_data", "llm")
        #graph.add_conditional_edges("detect_intention_data_range",)
        





        graph.add_node("llm", self.call_openai)
        #graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: END, False: END})
        #graph.add_edge("action", "llm")

        graph.set_entry_point("starting_point")
        self.graph = graph.compile(checkpointer=checkpointer, interrupt_before=['user_input_data_range','user_input_declare_data_range'], )

        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)
        self.model_no_tools = ChatOllama(model='llama3.1', temperature=0)


    def call_openai(self, state: AgentState):
        print('node_llm')
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def exists_action(self, state: AgentState):
        print('node_exists_action')
        result = state['messages'][-1]
      
        return len(result.tool_calls) > 0
        
    ##################### NODES ############################
    def start_point(self,state: AgentState):
        print("node_start_point")
        message =SystemMessage("Hi, I'm your personal data scientist assistant and I'm going to guide you to create a complete analysis of your data, First Let's check if you have datetimes columns")
        return {'messages': [message]}
        
    
    def decide_if_data_range(self, state: AgentState):
        print('node_decide_if_data_range')  
        message = SystemMessage("I've detected that your data contains datetime values, Would you like to work with a specific date range or leave it as it is?")
        return {'messages': [message]}  # Espera la respuesta del usuario

    def user_input_data_range(self,state: AgentState):
        print('node_user_input_data_range')
        pass
        
    def user_input_declare_data_range(self,state:AgentState):
        user_prompt = state['messages'][-1]
        instruction = """
You are a smart data assistant. When the user requests a date range, you must do the following:

1. If the user mentions "today", call `tool_current_date` to get the current date.
2. If the user mentions a relative time expression like "X years ago" or "in X years", call `tool_operation_date`, passing the current date and the operation.
3. Once you have both the start and end dates, call `tool_data_range`, passing the column name, start date, and end date.

Do not pass tool names as arguments directly. Always execute the tools first and use the returned values in the next tool call.
"""
        instruction = SystemMessage(content=instruction)
        model_response = self.model.invoke([instruction,user_prompt])
        print(model_response)
        message = self.extract_data_range(model_response)


        return {'messages': [message]} 
    
    def declare_data_range(self, state:AgentState):
        print("node_declare_data_range")
        date_columns_str = ', '.join(self.data_extractor.date_columns)
        message = SystemMessage(f"Please specify the column name and the date range you want to work with, preferably in the format %d-%m-%y. Important, your datetime columns are: {date_columns_str}")
        return {'messages': [message]}

    def process_missing_values(self, state:AgentState):
        print('node_process_missing_values')
        final_message = ''
       
        for column_name in self.na_values.keys():
            print(column_name)
            
            print(final_message)
            
            instruction = f"""
        You are an intelligent data preprocessing assistant. You are given a dataset that contains multiple columns with varying data types and percentages of missing values.
        Additionally, the user has provided a description of their problem and the dataset that may contain relevant information for making preprocessing decisions.
        
        Your task is to recommend the best strategy for handling missing values in each column, considering the description, data type, and missing value percentage.
        You **must** use one of the following methods to handle missing values, based on the column characteristics:
        
        1. Imputation with Mean or Median (for numerical data with low to moderate missing values).
        2. K-Nearest Neighbors (KNN) Imputation (for numerical data with moderate missing values).
        3. Interpolation (for sequential or time-series data).
        4. Mode Imputation (for categorical data with low to moderate missing values).
        5. Imputation with a Placeholder like 'Unknown' (for categorical data with moderate to high missing values).
        6. Forward or Backward Fill (for time-series data).
        8. Combining Columns (when two related columns have missing values and can be combined).
        
        You should decide which method to use for each column based on its data type, percentage of missing values, and any additional relevant context from the user's problem description.
        
        Description: {self.business_description}
        Column name: {column_name}
        Data info: {self.na_values[column_name]}
    """     
            previous_na_values = self.data_extractor.data[column_name].isna().sum()
            print(previous_na_values)
            print("antes del modelo")
            model_response = self.model.invoke([instruction])
            print('despues del modelo')
            if model_response.tool_calls:
                tool_calls = model_response.tool_calls
                for t in tool_calls:
                    tool_name = t['name']
                    print(tool_name)
                    tool_args = t['args']
                    tool = self.tools[tool_name]
                    result = tool.invoke(tool_args)
            print('despues de las herramientas')
            actual_na_values = self.data_extractor.data[column_name].isna().sum()
            print(column_name)
           # message = f"Column: {column_name}, method: {tool_name}, na/null values: {previous_na_values} ----> {actual_na_values} \n"
            message = f" method: {tool_name}, na/null values: {previous_na_values} ----> {actual_na_values}  \n"
            final_message += message

        final_message = SystemMessage(content=final_message)
        self.data_extractor.create_correlation_matrix()
        return {"messages": [final_message]}
    

    def clean_data(self, state:AgentState):
        pass
    
    ########################### CONDITIONAL EDGES #####################
    def has_intention_data_range(self, state:AgentState):
        print("edge_has_intention_data_range")
        last_message = state['messages'][-1]
        instruction = """
You are a helpful assistant. Based on the following message from the user, determine if they want to work with a specific date range. Do not invoke any tool or performs actions beyond providing a textual response.
For more context, the user is answering the next question: I've detected that your data contains datetime values, Would you like to work with a specific date range or leave it as it is?
If the user wants to work with a date range, respond with 'yes' 
If the user does not want to work with a date range, respond with 'no'
"""     
        instruction = SystemMessage(content=instruction)
        user_prompt = HumanMessage(content=last_message.content)

        model_response = self.model_no_tools.invoke([instruction,user_prompt])
        response_content = model_response.content.lower().strip()
       
        if 'yes' in response_content:
            return True
        
        return False
    


 
    def has_datetimes(self,state: AgentState):
        print("edge_has_datetimes")
        res = False
        datetime_columns = [col for col, info in self.data_extractor.columns.items() if info['dtype'] == 'datetime64[ns]']
        if datetime_columns:
            confirmation_message = SystemMessage("You've chosen to specify a date range. Let's proceed with that.")
            state['messages'].append(confirmation_message)
            res = True
        return res
    
    def has_missing_values(self, state: AgentState):
        print('edge_has_missing_values')
        total_len = self.data_extractor.data.shape[0]
        
        for column in self.data_extractor.columns.keys():
            na_count = self.data_extractor.columns[column]['na_count']
            
            if na_count>0:
              
                na_percentage = (na_count / total_len) * 100
                self.na_values[column] = {
                    'dtype': self.data_extractor.columns[column]['dtype'],
                    'na_percentage': na_percentage
                }
        if self.na_values:
            return True
        
        return False

    
   
    ############################# ADITIONAL TOOLS ####################
    def extract_data_range(self, model_response):
        tool_calls = model_response.tool_calls
        results = []

        for t in tool_calls:
            print(f"Calling: {t}")
            tool_name = t['name']
            tool_args = t['args']

            # Procesar argumentos si son llamadas a otras herramientas
            for arg, value in tool_args.items():
                if isinstance(value, str) and value.startswith('tool_'):
                    inner_tool_name = value
                    inner_tool_args = {}

                    # Si la herramienta es `tool_operation_date`, necesitamos la fecha actual
                    if inner_tool_name == 'tool_operation_date':
                        current_date = self.tools['tool_get_current_date'].invoke({})
                        inner_tool_args = {
                            'date_str': current_date,
                            'operation': tool_args.get('operation', 'subtract'),
                            'years': int(tool_args.get('years', 0))
                        }
                    
                    # Ejecutar la herramienta dependiente
                    tool_args[arg] = self.tools[inner_tool_name].invoke(inner_tool_args)

            # Llamar a la herramienta principal con los argumentos procesados
            result = self.tools[tool_name].invoke(tool_args)
            results.append(ToolMessage(tool_call_id=t['id'], name=tool_name, content=str(result)))

        print("Back to the model!")
       
        return results[0]