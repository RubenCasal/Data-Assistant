from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from typing import TypedDict, Annotated


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class Agent:
    def __init__(self, model, tools, column_info,system="", checkpointer=None):
        self.column_info = column_info
        self.system = system
        print(checkpointer)
        ############ GRAPH ########
        graph = StateGraph(AgentState)
        graph.add_node("starting_point", self.start_point)
        graph.add_node("decide_if_data_range",self.decide_if_data_range)
        graph.add_node("user_decision", self.user_decision)
        graph.add_node("declare_data_range", self.declare_data_range)
        graph.add_node("clean_data",self.clean_data)

        graph.add_conditional_edges("starting_point",self.has_datetimes,{True:'decide_if_data_range',False:'clean_data'})
        graph.add_conditional_edges('user_decision',self.has_intention_data_range,{True:'declare_data_range', False:'clean_data'})
        graph.add_edge("decide_if_data_range","user_decision")
        graph.add_edge("declare_data_range", "llm")
        graph.add_edge("clean_data", "llm")
        #graph.add_conditional_edges("detect_intention_data_range",)
        





        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: "action", False: END})
        graph.add_edge("action", "llm")

        graph.set_entry_point("starting_point")
        self.graph = graph.compile(checkpointer=checkpointer, interrupt_before=['user_decision'])

        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def exists_action(self, state: AgentState):
        
        result = state['messages'][-1]
      
        return len(result.tool_calls) > 0
    ##################### NODES ############################
    def start_point(self,state: AgentState):
        print("node_start_point")
        message =SystemMessage("Hi, I'm your personal data scientist assistant and I'm going to guide you to create a proper analysis of your data, First Let's check if you have datetimes columns")
        return {'messages': [message]}
    
    def decide_if_data_range(self, state: AgentState):
        print('node_decide_if_data_range')  
        message = SystemMessage("I've detected that your data contains datetime values. Would you like to work with a specific date range or leave it as it is?")
        return {'messages': [message]}  # Espera la respuesta del usuario

    def user_decision(self,state: AgentState):
        messages = state['messages'][-1]
        print(messages)
        pass

    
    def declare_data_range(self, state:AgentState):
        print("node_declare_data_range")
        pass

    def clean_data(self, state:AgentState):
        pass
    
    ########################### CONDITIONAL EDGES #####################
    def has_intention_data_range(self, state:AgentState):
        print("edge_has_intention_data_range")
        last_message = state['messages'][-1]
        print(last_message)
        instruction = """
        You are a helpful assistant. Based on the following message from the user, determine if they want to work with a specific date range. 
        If the user wants to work with a date range, respond with 'yes'. 
        If the user does not want to work with a date range, respond with 'no'.
        Message: {}
        """.format(last_message)
        model_response = self.model.invoke([SystemMessage(content=instruction)])
        response_content = model_response.content.lower().strip()
    
        if 'yes' in response_content:
            return True
        
        return False
    


 
    def has_datetimes(self,state: AgentState):
        print("edge_has_datetimes")
        res = False
        datetime_columns = [col for col, info in self.column_info.items() if info['dtype'] == 'datetime64[ns]']
        if datetime_columns:
            confirmation_message = SystemMessage("You've chosen to specify a date range. Let's proceed with that.")
            state['messages'].append(confirmation_message)
            res = True
        return res
    '''
    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        print(tool_calls)
        for t in tool_calls:
            print(f"Calling: {t}")
            print('##############################')
            print(t['args'])
            result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}
    '''
    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
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
        return {'messages': results}