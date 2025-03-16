import os
import time
import numpy as np
import pandas as pd
import concurrent.futures
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Load in transaction data
data_folder = Path(__file__).parents[1] / 'data'
transaction_folder = data_folder / 'transactions'
reports_folder = data_folder / 'reports'
transactions_df = pd.read_csv(transaction_folder / "merged_transactions.csv")

# Load in category dictionary, create if there is none
dictionary_file_path = reports_folder / 'category_dict.json'

# Check if the file path exists
if not dictionary_file_path.exists():
    category_dict = {}
    with open(dictionary_file_path, 'w') as file:
        json.dump(category_dict,file)
        print(f"Created category dictionary saved to {dictionary_file_path}")
else:
    with open(dictionary_file_path, 'r') as file:
        category_dict = json.load(file)

def process_chunk(chunk, api_key):
    chunk_counter = 1

    category_dict = {}
    # For each description in the chunk, get the category classification and store in dictionary 
    for element in chunk:
        start_time = time.time()
        print(f"Processing chunk number: {chunk_counter}...")
        description = str(element)
        category = classify_transaction(description, api_key)
        category_dict[description] = category
        print(f"Processed chunk number: {chunk_counter}")
        chunk_counter += 1 
        end_time = time.time()
        process_time = end_time - start_time
        print(f"Processing time for chunk {chunk_counter}: {process_time}")

    return category_dict

def classify_transaction(description, api_key):
    prompt = f"""
    Classify this description into a category:
    - Description: {description}
    - Categories: Rent/Mortgage, Transportation, Groceries, Dining Out, Bills/Utilities, Car Payment, Gas, Debt Payments, Savings, Shopping, Entertainment, Subscriptions, Personal Care/Grooming, Education/Project, Miscellaneous.

    Provide only the category name. No exceptions or explanations.
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
    time.sleep(15)

    return message_content
    
def create_category_column(description, category_dict):
    if description in category_dict:
        category = category_dict[description]
    else:
        category = None
    return category
    
# Apply categorization to each transaction
transactions_df['Category'] = transactions_df.apply(
    lambda row: create_category_column(
        description=row['Description'],
        category_dict=category_dict),
        axis=1
)

# Only get categories for new transactions
no_category_transactions = transactions_df[transactions_df['Category'].isna()]

# Split the unique transactions for multi-threading
unique_transaction_list = no_category_transactions['Description'].unique().tolist()
NUM_OF_THREADS = 100
df_chunks = np.array_split(unique_transaction_list, NUM_OF_THREADS)

# Kick off a thread for each chunk
with concurrent.futures.ThreadPoolExecutor(max_workers = NUM_OF_THREADS) as executor:
    futures = [executor.submit(process_chunk, chunk, OPENAI_API_KEY) for chunk in df_chunks]

for future in concurrent.futures.as_completed(futures):
    category_dict.update(future.result())


# Save new category dictionary to JSON file
with open(dictionary_file_path, 'w') as file:
    json.dump(category_dict, file)

# Apply categorization to each transaction
transactions_df['Category'] = transactions_df.apply(
    lambda row: create_category_column(
        description=row['Description'],
        category_dict=category_dict),
        axis=1
)

# Define file path to save categorized transactions
new_file_path = str(transaction_folder / 'categorized_transactions.csv')

# Save the updated file
transactions_df.to_csv(new_file_path, index = False)
print(f"Saved categorized transactions to {new_file_path}")