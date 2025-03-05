# Data cleaning script
from pathlib import Path
import numpy as np
import pandas as pd

# Define data folder
data_folder = Path.cwd().parent / 'data'

# Load Chase transactions
chase_df = pd.read_csv(data_folder / "transactions/chase_transactions.csv", index_col = False)

# Load AMEX transactions
amex_df = pd.read_csv(data_folder / "transactions/amex_transactions.csv")

# Rename columns for chase
chase_df = chase_df.rename(columns={"Posting Date":"Date"})

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