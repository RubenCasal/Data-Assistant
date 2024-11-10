import pandas as pd
import os
import dataframe_image as dfi
from typing import List
import os
import zipfile
import shutil

def dataframe_to_image(df: pd.DataFrame, file_name: str,user_id:str) -> str:
    # Path to store the image
    graphs_folder = f'./users_data/{user_id}/data_head'
    if not os.path.exists(graphs_folder):
        os.makedirs(graphs_folder)
    
    # Full path to the saved image
    image_path = os.path.join(graphs_folder, file_name)

    # Use dfi to export the DataFrame as an image and save it
    # You can modify this line if you want to add more styling or options
    styled_df = df.style.set_caption("Dataset Overview")
    dfi.export(styled_df, image_path)  # Export without extra table styles

    return image_path

def create_user_chart_zip(user_id: str) -> str:
    # Directory where user's images are stored
    user_image_folder = f'./users_data/{user_id}/charts'
    print(user_image_folder)
    # Check if the folder exists
    if not os.path.exists(user_image_folder):
        raise FileNotFoundError(f"No charts found for user {user_id}")

    # Path for the temporary ZIP file
    zip_filename = f'{user_id}_charts.zip'
    zip_filepath = os.path.join('./downloads', zip_filename)

    # Create the downloads folder if it doesn't exist
    os.makedirs('./downloads', exist_ok=True)

    # Create ZIP file
    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        for root, _, files in os.walk(user_image_folder):
            for file in files:
                file_path = os.path.join(root, file)
                # Add each file to the zip file
                zipf.write(file_path, arcname=os.path.relpath(file_path, user_image_folder))

    return zip_filepath

