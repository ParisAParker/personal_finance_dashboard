import streamlit as st
import numpy as np
import pandas as pd
import json
from pathlib import Path
from src.budget_analysis import transaction_filter

# Set page configuration
st.set_page_config(
    page_title='Transactions',
    layout='wide'
)

# Define directories, folders, and files
BASE_DIR = Path(__file__).parents[2]
data_folder = BASE_DIR / 'data'
transactions_folder = data_folder / 'transactions'
reports_folder = data_folder / 'reports'
transactions_df = pd.read_csv(transactions_folder / 'categorized_transactions.csv')
PERMANENT_OVERRIDES_FILE = reports_folder / 'category_dict.json'
ONE_OFF_CHANGES_FILE = reports_folder / 'category_one_off_changes.json'

# If category dictionaries don't exist, create them
for file_path in [PERMANENT_OVERRIDES_FILE, ONE_OFF_CHANGES_FILE]:
    if not file_path.exists():
        file_path.write_text(json.dumps({}))

if "category_overrides" not in st.session_state:
    with open(PERMANENT_OVERRIDES_FILE, 'r') as file:
        st.session_state.category_overrides = json.load(file)

if "one_off_change" not in st.session_state:
    with open(ONE_OFF_CHANGES_FILE, 'r') as file:
        st.session_state.one_off_changes = json.load(file)

def save_overrides():
    """Save the updated category overrides to the file."""
    with open(PERMANENT_OVERRIDES_FILE, 'w') as file:
        json.dump(st.session_state.category_overrides, file)

def save_oneoffs():
    with open(ONE_OFF_CHANGES_FILE, 'w') as file:
        json.dump(st.session_state.one_off_changes, file)

# Apply stored overrides (Runs FIRST but updates LATER when state changes)
def apply_category_overrides(df):
    df["Category"] = df["Description"].map(lambda desc: st.session_state.category_overrides.get(desc, df.loc[df["Description"] == desc, "Category"].values[0]))
    return df

def apply_one_off_changes(df):
    df["Category"] = df["Transaction_ID"].map(lambda id: st.session_state.one_off_changes.get(id, df.loc[df["Transaction_ID"] == id, "Category"].values[0]))
    return df

st.title("Re-Categorize Transactions")
transactions_df = apply_category_overrides(transactions_df)
transactions_df = apply_one_off_changes(transactions_df)

# Select transaction to edit
selected_index = st.selectbox("Select Transaction (Index):", transactions_df.index)
transaction_id = transactions_df.at[selected_index,"Transaction_ID"]
description = transactions_df.at[selected_index,"Description"]
st.write(f"Transaction Description: {description}")
current_category = transactions_df.at[selected_index,"Category"]

category_selections = transactions_df['Category'].unique().tolist()
category_selections.remove(current_category)

# Let user pick a new category
new_category = st.selectbox("Select New Category", category_selections)

# Allow user to choose between one row change or permanent description override
change_type = st.radio(
    "Apply Change To:",
    ("This Row Only", "All Transactions with this description")
)

if st.button("Update Category"):
    if change_type == "This Row Only":
        st.session_state.one_off_changes[str(transaction_id)] = new_category # Store change using the transaction id
        save_oneoffs()
        st.success(f"The {current_category} was applied to Transaction ID: {transaction_id}")
    elif change_type == "All Transactions with this description":
        st.session_state.category_overrides[description] = new_category # Store override for all transactions with this description
        save_overrides()
        st.success(f"Permanent category ({current_category}) was applied to {description}")

    transactions_df = apply_category_overrides(transactions_df)
    transactions_df = apply_one_off_changes(transactions_df)

# Search transactions    
search_query = st.text_input("Search Transactions:", key="search_query").lower()
filtered_df = transaction_filter(search_query, transactions_df)
st.dataframe(filtered_df)