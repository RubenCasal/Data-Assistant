from langchain_ollama import ChatOllama
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
def test_chat_ollama():
    try:
        # Initialize the model
        model = ChatOllama(model="llama3.1", temperature=0.7)
        user_prompt = HumanMessage(content="the column is called date. I want my data from 01-01-2014 to 01-01-2015")
        instruction = SystemMessage(content=f"You are an expert in data science. \
                    Your task is to understand the user's intention based on their prompt. \
                    Based on your expertise and the user's input, determine the user's intention and choose one of the following options:\
                    A: The user wants to modify or filter the data (e.g., filtering rows, changing values, modifying columns, select only a part of the data).\
                    B: The user wants to handle or process missing (NA) values in the dataset.\
                    C: The user wants to perform some kind of analysis on the data (e.g., statistical analysis, descriptive statistics, finding correlations).\
                    D: The user wants to create a graphical representation of the data (e.g., bar chart, histogram, line chart, scatter plot).\nOutput only the letter (A, B, C, or D) corresponding to the user's intention. Do not provide any additional explanation or output.\n\
                    ")

        model_response = model.invoke([instruction,user_prompt])
        print("AAAAAAAAAAAAAAAAAAAA")
        print(model_response)
    
    except Exception as e:
        print(f"Error occurred while testing ChatOllama: {e}")

if __name__ == "__main__":
    test_chat_ollama()
