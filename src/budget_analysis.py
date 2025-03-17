# Analyze monthly spending vs budget
import os
import json
import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.express as px
import matplotlib.pyplot as plt
from pathlib import Path
from pandas.tseries.offsets import BDay
from dotenv import load_dotenv

def plot_expense_by_category(df):
    # Filter for expenses
    current_expenses = df[df['Transaction_Type'] == 'Expense'].copy()
    current_expenses['abs_amount'] = current_expenses['Amount'].abs()

    # Aggregate expenses by category
    expense_by_category = (
        current_expenses.groupby('Category')['abs_amount']
        .sum()
        .reset_index()
    )

    # Remove 'Savings' category
    expense_by_category = expense_by_category[expense_by_category['Category'] != 'Savings']

    # Sort values
    expense_by_category = expense_by_category.sort_values(by='abs_amount', ascending=True)

    # Create interactive bar chart
    fig = px.bar(
        expense_by_category,
        x="abs_amount",
        y="Category",
        orientation="h",
        title="Monthly Expenses by Category",
        text="abs_amount",
        labels={"abs_amount": "Expenses ($)", "Category": "Category"},
        color="abs_amount",  # Optional: color by value
        color_continuous_scale="Blues"  # Optional: Customize colors
    )

    # Update hover info and bar text formatting
    fig.update_traces(
        texttemplate="$%{x:,.2f}",  # Format text as currency
        textposition="outside",
        hoverinfo="text"
    )

    # Streamlit display
    st.plotly_chart(fig, use_container_width=True)


def get_actual_payday(year, month):
    """
    Determines the actual payday for a given month.
    - If the 26th is a weekend/holiday, shifts payday to the previous business day.
    
    Returns: Adjusted payday as a datetime object.
    """
    payday = pd.Timestamp(year, month, 26)
    
    # If payday falls on a weekend, shift to the previous business day
    if payday.weekday() >= 5:  # 5=Saturday, 6=Sunday
        payday -= BDay(1)  # Move to the previous business day

    return payday

def assign_pay_period(df, date_column="Date"):
    """
    Assigns transactions to the correct pay period based on the adjusted payday.
    """
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])  # Ensure datetime format

    # Determine pay periods
    df["PayPeriod"] = df[date_column].apply(
    lambda x: get_actual_payday(x.year - 1, 12).strftime('%Y-%m')
    if x.month == 1 else get_actual_payday(x.year, x.month - 1).strftime('%Y-%m')
    )

    return df

def transaction_pay_period(df):
    # Get the min and max date of the transactions dataframe
    min_date = df['Date'].min() - pd.offsets.MonthEnd(1)
    max_date = df['Date'].max() + pd.offsets.MonthEnd(1)

    # Get the monthly date range between min and max date
    date_range = pd.date_range(
        start = min_date,
        end = max_date,
        freq = 'ME'
    )

    # Initialize column to store pay period month
    df['Pay_Period'] = None

    # Get the pay period ranges for each month
    for x in date_range:
      
        current_paydate = get_actual_payday(x.year, x.month)
        if x.month == 12:
            next_paydate = get_actual_payday(x.year + 1, 1)
        else:
            next_paydate = get_actual_payday(x.year, x.month + 1)

        pay_period_range = pd.date_range(
            start = current_paydate,
            end = next_paydate,
            freq = 'D',
            inclusive = 'left'
        )

        # If the transaction falls within the pay period's date range, mark it as the correct month's pay period
        df['Pay_Period'] = df.apply(
            lambda x: (current_paydate + pd.DateOffset(months=1)).strftime('%B %Y') if x['Date'] in pay_period_range
            else x['Pay_Period'],
            axis=1
        )
        
    return df

def classify_income_expense(df, amount_column = 'Amount'):
    df['Transaction_Type'] = df[amount_column].apply(
        lambda x: 'Income' if x >= 0
        else 'Expense'
    )
    return df

def get_current_pay_period(df):   
    # Identify the current pay period
    current_pay_period = df[df['Pay_Period'] == 'March 2025']
    current_pay_period = current_pay_period[~((current_pay_period['Transaction_Type'] == 'Income') & (current_pay_period['Bank'] == 'AMEX'))]

    # Build helper columns for identifying refund transactions
    current_pay_period['abs_amount'] = current_pay_period['Amount'].abs()
    current_pay_period['is_refund_pair'] = False

    # Group transactions by absolute amount and check for charge-refund pairs
    matched_indices = set()
    for amount, group in current_pay_period.groupby('abs_amount'):
        charges = group[group['Amount'] < 0]
        refunds = group[group['Amount'] > 0]
        
        # Create empty list for storing paired indexes
        refund_exclude_list = []

        # Pair each charge with a refund within a close date range
        for charge_idx, charge_row in charges.iterrows():
            for refund_idx, refund_row in refunds.iterrows():
                if (abs((charge_row['Date'] - refund_row['Date']).days) <= 3) and refund_idx not in refund_exclude_list:  # Allow a 3-day window
                    current_pay_period.at[charge_idx, 'is_refund_pair'] = True
                    current_pay_period.at[refund_idx, 'is_refund_pair'] = True
                    refund_exclude_list.append(refund_idx)
                    break  # Move to next charge

    # Mark refund pairs as Ignored Transaction Type
    current_pay_period['Transaction_Type'] = current_pay_period.apply(
        lambda row: 'Ignored' if row['is_refund_pair'] == True
        else row['Transaction_Type'],
        axis=1
    )

    # Get the current pay period income
    current_pay_period_income = current_pay_period.groupby('Transaction_Type')['Amount'].sum()['Income']
    current_pay_period_expenses = current_pay_period.groupby('Transaction_Type')['Amount'].sum()['Expense']
    current_pay_period_savings = current_pay_period.groupby('Transaction_Type')['Amount'].sum()['Savings']

    return current_pay_period, current_pay_period_income, current_pay_period_expenses, current_pay_period_savings

# Define a function to format numbers as currency
def format_currency(value):
    return "${:,.2f}".format(value)

# Function to load the saved value from JSON
def load_misc_cash(MISC_CASH_FILE):
    try:
        with open(MISC_CASH_FILE, "r") as f:
            return json.load(f).get("misc_cash", 0.0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0.0  # Default value if file is missing or corrupted

# Function to save the input value to JSON
def save_misc_cash(MISC_CASH_FILE, value):
    with open(MISC_CASH_FILE, "w") as f:
        json.dump({"misc_cash": value}, f)

# Function to load the saved value from JSON
def load_retire_cash(RETIREMENT_CASH_FILE):
    try:
        with open(RETIREMENT_CASH_FILE, "r") as f:
            return json.load(f).get("retire_cash", 0.0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0.0  # Default value if file is missing or corrupted

# Function to save the input value to JSON
def save_retire_cash(RETIREMENT_CASH_FILE, value):
    with open(RETIREMENT_CASH_FILE, "w") as f:
        json.dump({"retire_cash": value}, f)

def classify_savings(df, description_column='Description', type_column='Transaction_Type'):
    df.loc[df['Description'].str.lower().str.contains('6031'),'Transaction_Type'] = 'Savings'
    df.loc[df['Transaction_Type'] == 'Savings','Amount'] *=-1

    return df

def transaction_filter(search_query, df):
    for column in df.columns:
        df[column] = df[column].astype(str)

    match_indices = set()
    
    search_query = search_query.lower()

    for column in df.columns:
        list_of_indexes = df[df[column].str.lower().str.contains(search_query, na=False)].index
        match_indices.update(list_of_indexes)

    list_of_indexes = list(match_indices)

    df = df.iloc[list_of_indexes].sort_values(by='Date', ascending=False)

    return df

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

def map_needs_wants_savings(df):
    new_df = df.copy()
    needs_wants_savings_mapping = {
        "Rent/Mortgage": "Needs",
        "Transportation": "Needs",
        "Gas": "Needs",
        "Car Payment":"Needs",
        "Personal Care/Grooming": "Wants",
        "Insurance": "Needs",
        "Groceries": "Needs",
        "Dining Out": "Wants",
        "Bills/Utilities": "Needs",
        "Debt Payments": "Savings",
        "Savings": "Savings",
        "Shopping": "Wants",
        "Entertainment": "Wants",
        "Subscriptions": "Wants",
        "Personal Care": "Needs",
        "Education/Project": "Needs",
        "Miscellaneous": "Wants"}

    new_df['Needs_Wants_Savings'] = new_df['Category'].map(needs_wants_savings_mapping)

    return new_df

def plot_fifty_thirty_twenty(original_df):
    df = original_df.copy()
    income = df[(df['Transaction_Type'] == 'Income') & (df['Category'] != 'Savings') & (df['Bank'] != 'AMEX')]['Amount'].sum()
    expenses = df[(df['Transaction_Type'] != 'Income') & (df['Transaction_Type'] != 'Savings')]
    expense_amount = expenses['Amount'].sum()
    savings = round(income + expense_amount, 2)
    main_category_totals = expenses.groupby("Needs_Wants_Savings")['Amount'].sum()
    main_category_totals = main_category_totals.abs()
    main_category_totals['Savings'] = savings

    # Define custom colors
    colors = ["#E57373", "#81C784", "#64B5F6"]  # Add more colors as needed

    # Plot Pie Chart
    fig, ax = plt.subplots(figsize=(8,8))
    ax.pie(main_category_totals, labels=main_category_totals.index, autopct="%1.1f%%", startangle=140, colors=colors)

    return fig, income, expense_amount, savings

def plot_largest_expenses(original_df, selected_month):
    df = original_df.copy()
    expenses = df[df['Transaction_Type'] == 'Expense']
    expenses['abs_amount'] = expenses['Amount'].abs()
    expenses = expenses.sort_values(
        by='abs_amount',
        ascending=False
    )

    ten_largest_expenses = expenses[0:10].sort_values(
        by='abs_amount',
        ascending=True)

    fig, ax = plt.subplots(figsize=(8,8))

    categories = ten_largest_expenses['Description']
    values = ten_largest_expenses['abs_amount']

    ax.barh(categories, values)

    ax.set_label("Amount ($)")
    ax.set_ylabel("Description")
    ax.set_title(f"Largest Expenses for {selected_month}")
    return fig

def plot_category_over_time(original_df, selected_category):
    df = original_df.copy()
    filtered_df = df[df['Category'] == selected_category]
    filtered_df['Pay_Period_DT'] = pd.to_datetime(filtered_df['Pay_Period'])
    filtered_df['abs_amount'] = filtered_df['Amount'].abs()
    
    monthly_category = filtered_df.groupby('Pay_Period_DT')['abs_amount'].sum().reset_index()
    monthly_category['Pay_Period_Month_Year'] = monthly_category['Pay_Period_DT'].dt.strftime("%B-%Y")
    months = monthly_category['Pay_Period_Month_Year']
    expenses = round(monthly_category['abs_amount'],2)

    fig, ax = plt.subplots(figsize=(8,8))

    # ax.plot(months, expenses)
    bars = ax.barh(months, expenses)

    # Add values to bars
    for bar in bars:
        xval = bar.get_width()
        ax.text(xval,
                bar.get_y() + bar.get_height()/2,
                f"{xval}",
                va="center", ha="left", fontsize=10
                )

    ax.set_title(f"{selected_category} Expenses Over Time")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # ax.tick_params(axis='x', rotation=90)
    # ax.set_xticks(months)

    return fig

def plot_savings(original_df, _type='savings'):
    df = original_df.copy()

    aggregate_by_pay_period = df.groupby(['Pay_Period','Transaction_Type','Category','Bank'])['Amount'].sum().reset_index()

    income = aggregate_by_pay_period[(aggregate_by_pay_period['Transaction_Type'] == 'Income') & (aggregate_by_pay_period['Category'] != 'Savings') & (aggregate_by_pay_period['Bank'] != 'AMEX')]
    expenses = aggregate_by_pay_period[(aggregate_by_pay_period['Transaction_Type'] != 'Income') & (aggregate_by_pay_period['Transaction_Type'] != 'Savings')]
    income_by_month = income.groupby('Pay_Period')['Amount'].sum().reset_index().rename(columns={'Amount':'Income'})
    expenses['abs_amount'] = expenses['Amount'].abs()
    expenses_by_month = expenses.groupby('Pay_Period')['abs_amount'].sum().reset_index().rename(columns={'abs_amount':'Expenses'})

    cash_flow_by_month = income_by_month.merge(
        right=expenses_by_month
    )
    cash_flow_by_month['savings'] = cash_flow_by_month['Income'] - cash_flow_by_month['Expenses']
    cash_flow_by_month['saving_pct'] = round((cash_flow_by_month['savings'] / cash_flow_by_month['Income']) * 100,1)
    cash_flow_by_month['Pay_Period_DT'] = pd.to_datetime(cash_flow_by_month['Pay_Period'])

    savings_by_month = cash_flow_by_month.sort_values(
        by='Pay_Period_DT',
        ascending=False
    ).reset_index(drop=True)

    savings_series = savings_by_month['savings']
    saving_pct_series = savings_by_month['saving_pct']
    pay_period = savings_by_month['Pay_Period']

    fig, ax = plt.subplots(figsize=(8,8))
    if _type == 'savings':
        ax.barh(pay_period, savings_series)
    elif _type =='savings_pct':
        ax.barh(pay_period, saving_pct_series)
        

    return fig