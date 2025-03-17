import streamlit as st
import numpy as np
import pandas as pd
import json
from pathlib import Path
from src.budget_analysis import assign_pay_period, transaction_pay_period, classify_income_expense, classify_savings, apply_category_overrides, apply_one_off_changes, plot_fifty_thirty_twenty, map_needs_wants_savings, format_currency, plot_largest_expenses, plot_category_over_time, plot_savings

# Set up the page title
st.set_page_config(
    page_title="Personal Finance Dashboard",
    layout = "wide"
)

# Read in transaction data
reports_folder = Path(__file__).parents[2] / 'data/reports'
transaction_folder = Path(__file__).parents[2] / 'data/transactions'
transactions_df = pd.read_csv(transaction_folder / 'categorized_transactions.csv')
transactions_df = assign_pay_period(transactions_df)
transactions_df = transaction_pay_period(transactions_df)
transactions_df = classify_income_expense(transactions_df)
transactions_df = classify_savings(transactions_df)
transactions_df = map_needs_wants_savings(transactions_df)
PERMANENT_OVERRIDES_FILE = reports_folder / 'category_dict.json'
ONE_OFF_CHANGES_FILE = reports_folder / 'category_one_off_changes.json'

if "category_overrides" not in st.session_state:
    with open(PERMANENT_OVERRIDES_FILE, 'r') as file:
        st.session_state.category_overrides = json.load(file)

if "one_off_change" not in st.session_state:
    with open(ONE_OFF_CHANGES_FILE, 'r') as file:
        st.session_state.one_off_changes = json.load(file)

transactions_df = apply_category_overrides(transactions_df)
transactions_df = apply_one_off_changes(transactions_df)

tab1, tab2, tab3 = st.tabs(["Monthly Breakdown", "Category Breakdown", "Savings Rate"])

with tab1:

    selected_month = st.selectbox("Select Pay Period Month:", transactions_df['Pay_Period'].unique())
    filtered_df = transactions_df[transactions_df['Pay_Period'] == selected_month]
    pie_plot = plot_fifty_thirty_twenty(filtered_df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label='Pay Period Income',
            value=format_currency(pie_plot[1])
            )
    with col2:
        st.metric(
            label='Pay Period Expenses',
            value=format_currency(pie_plot[2])
        )
    with col3:
        st.metric(
            label='Pay Period Savings',
            value=format_currency(pie_plot[3])
        )


    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(pie_plot[0])
    with col2:
        st.pyplot(plot_largest_expenses(filtered_df, selected_month))

with tab2:
    selected_category = st.selectbox("Choose Category:", transactions_df['Category'].unique())
    filtered_df = transactions_df[transactions_df['Category'] == selected_category]
    category_plot = plot_category_over_time(filtered_df, selected_category)
    st.pyplot(category_plot)

with tab3:
    savings_rate_plot = plot_savings(transactions_df)
    st.pyplot(savings_rate_plot)