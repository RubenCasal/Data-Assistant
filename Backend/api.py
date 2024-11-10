from fastapi import FastAPI, UploadFile, File, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
from io import BytesIO, StringIO
import os
from langgraph.checkpoint.memory import MemorySaver
from new_agent_llm import Agent
from data_extractor import DataExtractor
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
import dataframe_image as dfi
from utils import dataframe_to_image, create_user_chart_zip
from uuid import uuid4  # To generate unique thread IDs

from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
app = FastAPI()

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change this in production for security)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Define the request body model
class PromptRequest(BaseModel):
    prompt: str

# In-memory session store for user-specific data
session_store = {}

# Function to get session for a specific user
def get_session(user_id: str):
    if user_id not in session_store:
        session_store[user_id] = {}
    return session_store[user_id]

# CSV upload and bot initialization endpoint
@app.post("/upload-csv/{user_id}")
async def upload_csv(user_id: str, file: UploadFile = File(...)):
    try:
        # Read the CSV file from the uploaded file
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))  # Load the CSV file into a pandas dataframe

        # Store the dataframe in the session for the user
        session = get_session(user_id)
        session['dataframe'] = df

        # Initialize the data extractor with the dataframe
        data_extractor = DataExtractor(df, user_id)  # Adjust 'sales' to your target column
 
        # Initialize the ChatOllama model and Agent
        model = ChatOllama(model='llama3.1:latest',base_url='http://ollama:11434', temperature=0)
        bot = Agent(
            model=model,
            business_description="business_description", 
            data_extractor=data_extractor,
            data_modifications_tools=data_extractor.data_modifications_tools,
            process_na_value_tools=data_extractor.process_na_values_tools,
            data_analysis_tools=data_extractor.data_analysis_tools,
            data_graphics_tools=data_extractor.data_graphics_tools,
            system='',
            checkpointer=MemorySaver()
        )
        
        # Generate and store a unique thread_id for the user
        thread_id = str(uuid4())  # Generate a unique thread ID
        session['bot'] = bot
        session['thread_id'] = thread_id  # Store the thread ID in the session

        return JSONResponse(content={"message": "CSV uploaded and bot initialized successfully."})
    
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

# Chat endpoint to send the prompt and get a response
@app.post("/chat/{user_id}")
async def chat_with_model(user_id: str, request: PromptRequest):
    try:
        # Fetch the user's session, which includes the bot, thread_id, and conversation history
        session = get_session(user_id)
        bot = session.get('bot')
        thread_id = session.get('thread_id')  # Retrieve the user-specific thread_id
        messages = session.get('messages', [])  # Retrieve or initialize the message history
        print(messages)

        if not bot:
            return JSONResponse(content={"error": "Bot not initialized. Upload CSV first."}, status_code=400)
        
        if not thread_id:
            return JSONResponse(content={"error": "Thread ID not found. Please reinitialize the bot."}, status_code=400)

        # Get the prompt from the request body and add it to the message history
        user_message = HumanMessage(content=request.prompt)
        messages.append(user_message)

        # Use the user-specific thread_id in the thread configuration
        thread = {"configurable": {"thread_id": thread_id}}
        
        # Stream responses from the bot and capture the response message
        response_message = None
        for event in bot.graph.stream({"messages": messages}, thread):
            for v in event.values():
                if v:
                    response_content = v["messages"][0].content

                    # Check if the response contains a chart (starts with "Figure:")
                    if response_content.startswith("Figure:"):
                        chart_name = response_content.split("Figure: ")[1].strip()
                        chart_path = os.path.join(f'./users_data/{user_id}/charts', chart_name)
               
                        if os.path.exists(chart_path):
                            # Save bot's response as a message and update memory
                            response_message = SystemMessage(content="Figure: " + chart_name)
                            messages.append(response_message)
                            session['messages'] = messages  # Save the updated history in session
                            return FileResponse(chart_path, media_type="image/png")

                        else:
                            return JSONResponse(content={"error": f"Graph '{chart_name}' not found."}, status_code=404)

                    # If it's a regular text message
                    else:
                        response_message = SystemMessage(content=response_content)
                        messages.append(response_message)  # Update message history

                        # Save the updated history in session
                        session['messages'] = messages
                        return JSONResponse(content={"response": response_content})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/download-charts/{user_id}")
async def download_user_charts(user_id: str):
    try:
        # Generate the ZIP file for the user's charts
        zip_filepath = create_user_chart_zip(user_id)
        
        # Return the ZIP file for download
        return FileResponse(zip_filepath, media_type="application/zip", filename=f"{user_id}_charts.zip")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No charts found for the user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {e}")




@app.get("/data-head-image/{user_id}")
async def get_data_head_image(user_id: str):
    # Fetch the user's session
    session = get_session(user_id)
    
    # Get the Bot object from the session
    bot = session.get('bot')
    if not bot:
        return JSONResponse(content={"error": "Bot not initialized. Upload CSV first."}, status_code=400)

    # Get the first few rows of the DataFrame
    data_head = bot.data_extractor.data.head()

    # Convert the DataFrame to an image and save it in the graphs folder
    image_path = dataframe_to_image(data_head, f"data_head.png",user_id)

    # Return the image as a FileResponse
    return FileResponse(image_path, media_type="image/png")

@app.get("/download-csv/{user_id}")
async def download_csv(user_id: str):
    # Get the modified DataFrame from the user's session
    session = get_session(user_id)
    modified_df = session.get("bot").data_extractor.data

    if modified_df is None:
        return Response(content="CSV file not found.", status_code=404)

    # Convert the DataFrame to CSV
    csv_buffer = StringIO()
    modified_df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()

    # Return the CSV as a downloadable file
    headers = {
        'Content-Disposition': f'attachment; filename="modified_data_{user_id}.csv"'
    }
    return Response(content=csv_content, media_type="text/csv", headers=headers)