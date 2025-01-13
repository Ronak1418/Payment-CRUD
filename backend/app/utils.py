import pandas as pd
from datetime import datetime
from config.db import payment_collection
import os

# Normalize CSV and load into MongoDB
async def load_csv_to_db(file_path):
    if not os.path.exists(file_path):
        print(f"CSV file not found: {file_path}")
        return

    df = pd.read_csv(file_path)
    # Fill missing values
    df.fillna({"discount_percent": 0.0, "tax_percent": 0.0, "payee_province_or_state": ""}, inplace=True)

    # Convert DataFrame to dictionary
    data = df.to_dict(orient="records")
    # Insert data into MongoDB
    await payment_collection.delete_many({})  # Clear existing data
    await payment_collection.insert_many(data)
    print(f"Loaded data from {file_path} into MongoDB.")