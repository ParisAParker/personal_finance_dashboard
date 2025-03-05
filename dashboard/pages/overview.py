# Dashboard homepage
import streamlit as st
import pandas as pd
from pathlib import Path

# Define data folder
transaction_folder = Path(__file__).parents[2] / 'data/transactions'
transactions_df = pd.read_csv(transaction_folder / 'categorized_transactions.csv')
amex_transactions = transactions_df[transactions_df['Bank'] == 'AMEX']

# Balances for different money categories
total_car_lease = 14364
nss_total_amount = 8625
total_car_lease_paid = transactions_df[transactions_df['Description'].str.contains("CHRYSLER CAPITAL")]['Amount'].sum()
nss_total_paid = transactions_df[transactions_df['Description'].str.contains("NASHVILLE SOFTWARE")]['Amount'].sum()

car_lease_balance = round((total_car_lease + total_car_lease_paid),2)
credit_card_balance = round(amex_transactions['Amount'].sum(),2)
nss_school_balance = (nss_total_amount + nss_total_paid)

# Create columns to display key metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="💳 Credit Card Balance", value=f"${credit_card_balance:,.2f}")

with col2:
    st.metric(label="🎓 Remaining School Balance", value=f"${nss_school_balance:,.2f}")

with col3:
    st.metric(label="🚗 Car Lease Balance", value=f"${car_lease_balance:,.2f}")