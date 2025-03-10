import numpy as np
import pandas as pd
import json
from pathlib import Path

# Define data folder
data_folder = Path.cwd().parent / 'data'

# Load Chase checking transactions
chase_df = pd.read_csv(data_folder / "transactions/chase_checkings_transactions.csv", index_col = False)

# Load Chase savings transactions
chase_savings = pd.read_csv(data_folder / "transactions/chase_savings_transactions.csv", index_col=False)

# Load AMEX transactions
amex_df = pd.read_csv(data_folder / "transactions/amex_transactions.csv")

# Rename columns for chase
chase_df = chase_df.rename(columns={"Posting Date":"Date"})

# Get the current checking and saving balance
no_balance_transactions = chase_df[chase_df['Balance'].str.strip() == '']
process_amount = no_balance_transactions['Amount'].sum()
most_recent_balance = float(chase_df[~(chase_df['Balance'].str.strip() == '')].iloc[0].Balance)
checking_balance = round(most_recent_balance + process_amount,2)
savings_balance = chase_savings.iloc[0].Balance

# Keep only relevant columns in Chase
chase_df = chase_df[["Date", "Description", "Amount"]]

# Convert date column to proper format
chase_df['Date'] = pd.to_datetime(chase_df['Date'])
amex_df['Date'] = pd.to_datetime(amex_df['Date'])

# Add bank identifier
chase_df['Bank'] = 'Chase'
amex_df['Bank'] = 'AMEX'

# Multiply amount by -1 so debits are negative
amex_df['Amount'] = amex_df['Amount'] * -1

# Combine both DataFrames
transactions_df = pd.concat([chase_df,amex_df])

# Save merged data to csv file
transactions_df.to_csv(data_folder / "transactions/merged_transactions.csv", index = False)

# Save balances to a JSON file
balances = {
    "chase_checkings_balance": checking_balance,
    "chase_savings_balance": savings_balance 
}

with open(data_folder / "reports/chase_balances.json", "w") as file:
    json.dump(balances, file)