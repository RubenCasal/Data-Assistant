from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage

class Agent:
    def __init__(self, model, tools, system=""):
        self.system = system
        graph = StateGraph(AgentState)

        # Nodo 1: Analizar la data
        graph.add_node("analyze_data", self.analyze_data)
        
        # Nodo 2: Detectar intención del usuario
        graph.add_node("detect_intent", self.detect_intent)

        # Nodo 3: Preguntar por las fechas si la información no es correcta
        graph.add_node("ask_dates", self.ask_dates)
        
        # Nodo 4: Realizar el recorte de datos (take_action)
        graph.add_node("take_action", self.take_action)
        
        # Nodo 5: Visualizar resultados
        graph.add_node("visualize_results", self.visualize_results)
        
        # Definir las transiciones entre nodos
        graph.add_edge("analyze_data", "detect_intent")
        graph.add_conditional_edges("detect_intent", self.is_cut_intent, {True: "ask_dates", False: "visualize_results"})
        graph.add_conditional_edges("ask_dates", self.are_dates_correct, {True: "take_action", False: "ask_dates"})
        graph.add_edge("take_action", "visualize_results")
        
        # Punto de entrada
        graph.set_entry_point("analyze_data")
        self.graph = graph.compile()

        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def analyze_data(self, state: AgentState):
        """Nodo inicial: Analiza la data para encontrar columnas de tipo datetime."""
        if self.system:
            state['messages'].append(SystemMessage(content="Analyzing data..."))
        
        # Lógica de análisis para detectar columnas datetime
        has_datetime = any(col['dtype'] == 'datetime64' for col in self.data_extractor.columns.values())
        
        return {'has_datetime': has_datetime}
    
    def detect_intent(self, state: AgentState):
        """Utiliza el modelo LLM para detectar la intención del usuario."""
        # Último mensaje del usuario
        user_message = state['messages'][-1].content
        print(f"Detectando intención en el mensaje: {user_message}")
        
        # Instrucción personalizada para el modelo
        instruction = """
        You are a smart assistant. Analyze the user's message and classify the intention into one of these categories:
        - "cut_data" if the user wants to cut the data based on dates
        - "visualize_data" if the user wants to visualize the data without cutting
        - "unknown" if the intention is unclear
        """
        
        # Enviar el mensaje al modelo para detectar la intención
        model_input = [SystemMessage(content=instruction), HumanMessage(content=user_message)]
        response = self.model.invoke(model_input)
        
        # Extraer la intención del resultado del modelo
        intent = response.content.lower()
        print(f"Intención detectada: {intent}")
        
        return {'intent': intent}
    
    def is_cut_intent(self, state: AgentState):
        """Transición: Verifica si la intención del usuario es recortar los datos."""
        intent = state.get('intent', 'unknown')
        return intent == 'cut_data'

    def ask_dates(self, state: AgentState):
        """Nodo donde se le pide al usuario que ingrese las fechas si no fueron proporcionadas correctamente."""
        state['messages'].append(HumanMessage(content="Please provide valid start and end dates in the format dd/MM/yyyy."))
        return state

    def are_dates_correct(self, state: AgentState):
        """Transición: Verifica si las fechas proporcionadas son correctas."""
        last_message = state['messages'][-1].content
        try:
            # Intentar convertir las fechas
            start_date, end_date = last_message.split("to")
            pd.to_datetime(start_date.strip(), format='%d/%m/%Y')
            pd.to_datetime(end_date.strip(), format='%d/%m/%Y')
            return True
        except Exception as e:
            return False

    def take_action(self, state: AgentState):
        """Ejecuta el recorte de la data basado en las fechas proporcionadas."""
        last_message = state['messages'][-1].content
        start_date, end_date = last_message.split("to")
        result = self.tools['tool_data_range'].invoke({'column_name': 'date', 'start_date': start_date.strip(), 'end_date': end_date.strip()})
        state['messages'].append(ToolMessage(content=str(result)))
        return state

    def visualize_results(self, state: AgentState):
        """Genera una visualización de los resultados."""
        state['messages'].append(HumanMessage(content="Generating visualizations for the data..."))
        result = self.tools['tool_generate_graph'].invoke({})
        state['messages'].append(ToolMessage(content=str(result)))
        return state
