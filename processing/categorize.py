# Transaction categorization logic
import os
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Load in transaction data
data_folder = Path.cwd().parent / 'data'
transaction_folder = data_folder / 'transactions'
transactions_df = pd.read_csv(transaction_folder / "merged_transactions.csv")

def classify_transaction(description, amount, api_key):
    prompt = f"""
    Classify this transaction into a category:
    - Description: {description}
    - Amount ${amount}
    - Categories: Food, Entertainment, Shopping, Transportation, Bills, Rent, Groceries, Subscriptions, Investment, Miscellaneous.

    Provide only the category name
    """

    client = OpenAI(
    api_key=OPENAI_API_KEY
    )

    response = client.chat.completions.create(
    model = "gpt-4o-mini",
    messages =[
        {"role": "system", "content": "You are an expert finance assistant"},
        {"role": "user", "content": prompt}
    ]
    )

    message_content = response.choices[0].message.content

    return message_content

# Apply categorization to each transaction

transactions_df["Category"] = transactions_df.apply(lambda row:
    classify_transaction(
    description=row["Description"],
    amount=row["Amount"],
    api_key=OPENAI_API_KEY
), axis=1
)

# Define file path to save categorized transactions
new_file_path = str(transaction_folder / 'categorized_transactions.csv')

# Save the updated file
transactions_df.to_csv(new_file_path, index = False)