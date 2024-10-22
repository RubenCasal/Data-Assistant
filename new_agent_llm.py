from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from typing import TypedDict, Annotated


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class Agent:
    def __init__(self, model,business_description, data_extractor,data_modifications_tools,process_na_value_tools, data_analysis_tools,data_graphics_tools,system="", checkpointer=None):
        self.data_extractor = data_extractor
        print(business_description)
        self.business_description = business_description
        self.system = ''
        self.na_values = {}

     
        self.checkpointer = checkpointer
       
        ############ GRAPH ########
        graph = StateGraph(AgentState)
        graph.add_node('start_node',self.start_point)
        graph.add_conditional_edges('start_node', self.evaluate_user_intention,{
                                      'A': 'data_modification',
                                      'B': 'process_na_values',
                                      'C': 'create_analysis',
                                      'D': 'create_graphics' 
                                     }      
                                    )
        graph.add_node('data_modification', self.data_modification)
        graph.add_node('process_na_values',self.process_na_values)
        graph.add_node('create_analysis', self.create_data_analysis)
        graph.add_node('create_graphics', self.create_data_graphics)

        graph.add_edge('data_modification',END)
        graph.add_edge('process_na_values', END)
        graph.add_edge('create_analysis', END)
        graph.add_edge('create_graphics', END)
        


        graph.set_entry_point("start_node")
        self.graph = graph.compile(checkpointer=checkpointer )

        self.tools = self.data_extractor.tools
       
        
        self.data_modification_model = model.bind_tools(data_modifications_tools)
        self.process_na_value_tools_model = model.bind_tools(process_na_value_tools)
        self.data_analysis_tools_model = model.bind_tools(data_analysis_tools)
        self.data_graphics_tools_model = model.bind_tools(data_graphics_tools)

        self.model_no_tools = ChatOllama(model='llama3.1', temperature=0)

    

    def execute_tools(self,model_response):
      
        tool_calls = model_response.tool_calls
        for t in tool_calls:
            tool_name = t['name']
            print(tool_name)
            tool_args = t['args']
            tool = self.tools[tool_name]
            print("hasta aqui llega")
            result = tool.invoke(tool_args)
            print("hasta aqui no")
            print(result)
        return result

    ##################### NODES ############################

    def start_point(self,state: AgentState):
        print("node_start_point")
        #message =SystemMessage("Hi, I'm your personal data scientist assistant and I'm going to guide you to create a complete analysis of your data, First Let's check if you have datetimes columns")
        pass
    
    def data_modification(self, state: AgentState):
        print('node_data_modification')
        user_prompt = state['messages'][-1]
        user_prompt = HumanMessage(content=str(user_prompt))
        column_instruction = SystemMessage(content="Identify and return only the exact column name the user wants to modify from their input, with no extra text or quotes. Focus on phrases like 'column,' 'field,' or 'modify.'\n\n\
**Examples:**\n\
- User: 'In the column date, filter for 2020.'\n\
  - Output: date\n\
- User: 'Modify the sales column by removing low values.'\n\
  - Output: sales\n\n\
Respond with just the column name.")

        column_response = self.model_no_tools.invoke([column_instruction,user_prompt]).content.strip().split()[-1]
        print("modele column response")
        print(column_response)
        column_type = self.data_extractor.columns[column_response]['dtype']
    
        instruction = SystemMessage(content=f"You are now in the data modification phase. You have access to the column name and its data type (dtype) from the user's input, allowing you to choose the most appropriate tool and provide accurate arguments. The available tools are:\n\n\
1. tool_data_range(column_name: str, start_date: str, end_date: str): Extracts a date range in the dataframe. Use this if the dtype is 'datetime'.\n\
2. tool_get_current_date(): Returns the current date in dd-mm-yyyy format.\n\
3. tool_operation_date(date_str: str, operation: str, years: int): Adds or subtracts years from a date. Use this if the input is a specific date string.\n\
4. tool_filter_string(column_name: str, string_filter: str, include: bool): Filters rows based on whether a column value starts with or equals a given string. Use this if the dtype is 'string' or 'object'. 'include' determines if it includes or excludes the matching rows.\n\
5. tool_filter_numeric(column_name: str, comparison: str, value: float): Filters rows in a numeric column based on comparison operators ('>', '<', '=', '>=', '<='). Use this if the dtype is numeric.\n\
6. tool_drop_column(column_name: str): Drops a specified column from the dataframe.\n\
7. tool_filter_date(column_name: str, date_part: str, value: int): Filters rows by year, month, or day in a date column based on the specified value. Use this if the dtype is 'datetime'.\n\n\
Based on the column name, dtype, and the user’s prompt, choose the appropriate tool and provide only the function call with the correct arguments, without any additional explanation.\n\n\
The column name is : {column_response} and his dtype is: {column_type}")

      
        model_response = self.data_modification_model.invoke([instruction,user_prompt])
        print(model_response)
        
        if model_response.tool_calls:
           
            result = self.execute_tools(model_response)
        message = SystemMessage(content=str(result))
        return {'messages': [message]}

    
    def process_na_values(self, state: AgentState):
        print('node_process_na_values')
        user_prompt = HumanMessage(content=str(state['messages'][-1]))
        instruction = SystemMessage(content=f"You are now in the part of processing missing (NA) values. Your task is to choose the correct tool based on the user's input and pass the correct arguments. The available tools are:\n\n\
1. tool_impute_mean_median(column_name: str, strategy: str = 'mean'): Impute missing values in a numerical column using mean or median.\n\
2. tool_knn_imputation(columns: list[str], n_neighbors: int = 5): Perform K-Nearest Neighbors imputation for numerical columns.\n\
3. tool_interpolation(column_name: str, method: str = 'linear'): Perform linear or polynomial interpolation on a time-series column.\n\
4. tool_impute_mode(column_name: str): Impute missing values in a categorical column using the most frequent value (mode).\n\
5. tool_impute_placeholder(column_name: str, placeholder: str = 'Unknown'): Impute missing values in a categorical column with a placeholder value.\n\
6. tool_forward_backward_fill(column_name: str, direction: str = 'forward'): Perform forward or backward fill for a datetime column.\n\n\
7. tool_missing_values(): Reports the missing values of all columns in the dataset.\n\n\
Based on the user's prompt, you must choose the appropriate tool and provide the correct arguments. Output only the function call with the correct arguments, without any extra explanation.\n\
The information about the na values is: {self.data_extractor.columns}.\n\
USER MESSAGE: {user_prompt}")
        model_response = self.data_modification_model.invoke([instruction,user_prompt])
        print(model_response)
        
        if model_response.tool_calls:
           
            result = self.execute_tools(model_response)
        message = SystemMessage(content=str(result))
        return {'messages': [message]}

        
    def create_data_analysis(self, state: AgentState):
        print('node_create_data_analysis')
        user_prompt = state['messages'][-1]
        user_prompt = HumanMessage(content=str(user_prompt))
        instruction = SystemMessage(content=f"You are now in the part of data analysis. Your task is to choose the correct tool based on the user's input and pass the correct arguments. The available tools are:\n\n\
1. tool_descriptive_statistics(column_name: str): Provide basic descriptive statistics for a given numeric column.\n\
2. tool_correlation_matrix(column_name: str): Calculate and display the correlation matrix for numeric columns.\n\
3. tool_missing_values(): Analyze and report the percentage of missing values per column.\n\
4. tool_value_counts(column_name: str): Provide the frequency distribution of a given column.\n\
5. tool_outlier_detection(column_name: str): Detect outliers in a numeric column using the IQR method.\n\
6. tool_trend_analysis(column_name: str, window: int = 5): Calculate the moving average for trend analysis on a time-series column.\n\n\
Based on the user's prompt, you must choose the appropriate tool and provide the correct arguments. Output only the function call with the correct arguments, without any extra explanation.\n\
USER MESSAGE: {user_prompt}")

           
        model_response = self.data_modification_model.invoke([instruction,user_prompt])
        print(model_response)
        
        if model_response.tool_calls:
           
            result = self.execute_tools(model_response)
        message = SystemMessage(content=str(result))
        return {'messages': [message]}
    
    
    def create_data_graphics(self, state: AgentState):
        print('node_create_data_graphics')
        user_prompt = state['messages'][-1]
        user_prompt = HumanMessage(content=str(user_prompt))
        instruction = SystemMessage(content=f"You are now in the part of creating graphical visualizations. Your task is to choose the correct tool based on the user's input and pass the correct arguments. The available tools are:\n\n\
1. tool_bar_chart(column_name1: str, column_name2: str, color1: str = 'red', color2: str = 'blue'): Create a bar chart with column_name1 on the x-axis and column_name2 as the height of the bars.\n\
2. tool_histogram(column_name: str, color1: str = 'red'): Create a histogram for column_name.\n\
3. tool_line_chart(column_name1: str, column_name2: str, color1: str = 'red', color2: str = 'blue'): Create a line chart with column_name1 on the x-axis and column_name2 on the y-axis.\n\
4. tool_scatter_plot(column_name1: str, column_name2: str, color1: str = 'red', color2: str = 'blue'): Create a scatter plot with column_name1 on the x-axis and column_name2 on the y-axis.\n\n\
Based on the user's prompt, you must choose the appropriate tool and provide the correct arguments. Output only the function call with the correct arguments, without any extra explanation.")
        model_response = self.data_modification_model.invoke([instruction,user_prompt])
        print(model_response)
    
        if model_response.tool_calls:
           
            result = self.execute_tools(model_response)
        message = SystemMessage(content=result)
        
        
        return {'messages': [message]}
        
        

      
    
  ###################### EDGES #########################

    def evaluate_user_intention(self,state: AgentState):
        print('edge_evaluate_user_intention')
        user_prompt = state['messages'][-1]
        user_prompt = HumanMessage(content=str(user_prompt))
        instruction = SystemMessage(content=f"You are an expert in data science. \
                    Your task is to understand the user's intention based on their prompt. \
                    Based on your expertise and the user's input, determine the user's intention and choose one of the following options:\
                    A: The user wants to modify or filter the data (e.g., filtering rows, changing values, modifying columns).\
                    B: The user wants to handle or process missing (NA) values in the dataset.\
                    C: The user wants to perform some kind of analysis on the data (e.g., statistical analysis, descriptive statistics, finding correlations).\
                    D: The user wants to create a graphical representation of the data (e.g., bar chart, histogram, line chart, scatter plot).\nOutput only the letter (A, B, C, or D) corresponding to the user's intention. Do not provide any additional explanation or output.\n\
                    ")

        model_response = self.model_no_tools.invoke([instruction,user_prompt]).content
       
        print(model_response)
        if model_response == 'A':
            return 'A'
        elif model_response == 'B':
            return 'B'
        elif model_response == 'C':
            return 'C'
        elif model_response == 'D':
            return 'D'
        else:
            return 'default'