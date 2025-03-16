# Main Streamlit dashboard app
import requests
import json
import sys
from pathlib import Path
BASE_DIR = Path(__file__).parents[1]
sys.path.append(str(BASE_DIR))
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from src.budget_analysis import plot_expense_by_category, get_actual_payday, assign_pay_period, transaction_pay_period, classify_income_expense, get_current_pay_period, load_misc_cash, save_misc_cash, load_retire_cash, save_retire_cash, format_currency, classify_savings, apply_category_overrides, apply_one_off_changes, map_needs_wants_savings, plot_fifty_thirty_twenty

# FastAPI Backend URL
FASTAPI_URL = "http://127.0.0.1:8000"

# Set up the page title
st.set_page_config(
    page_title="Personal Finance Dashboard",
    layout = "wide"
)

# Read in transaction data
reports_folder = Path(__file__).parents[1] / 'data/reports'
transaction_folder = Path(__file__).parents[1] / 'data/transactions'
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

# Get the current pay period metrics
current_pay_period = get_current_pay_period(transactions_df)[0]
current_income = get_current_pay_period(transactions_df)[1]
current_expense_amount = get_current_pay_period(transactions_df)[2]
current_savings = get_current_pay_period(transactions_df)[3]
remaining_balance = current_income - current_savings + current_expense_amount

current_pay_period = map_needs_wants_savings(current_pay_period)
current_pay_period_expenses = current_pay_period[current_pay_period['Transaction_Type'] != 'Income']

# Load in Chase bank balances
with open(reports_folder / "chase_balances.json", "r") as file:
    saved_balances = json.load(file)

chase_checkings_balance = saved_balances["chase_checkings_balance"]
chase_savings_balance = saved_balances["chase_savings_balance"]

# File path for saving misc cash value
MISC_CASH_FILE = reports_folder /"misc_cash.json"
RETIREMENT_CASH_FILE = reports_folder / "retirement.json"

# Initialize session state for cash values
if "misc_cash" not in st.session_state:
    st.session_state["misc_cash"] = load_misc_cash(MISC_CASH_FILE)

if "retire_cash" not in st.session_state:
    st.session_state["retire_cash"] = load_retire_cash(RETIREMENT_CASH_FILE)

# Initialize session state for showing input fields
if "show_inputs" not in st.session_state:
    st.session_state["show_inputs"] = False

# Button to toggle input fields
if st.button("Edit Balances"):
    st.session_state["show_inputs"] = not st.session_state["show_inputs"]

# Show input fields only if the button is clicked
if st.session_state["show_inputs"]:
    misc_cash = st.number_input(
        "Enter Miscellaneous Cash Amount:", 
        min_value=0.0, 
        value=st.session_state["misc_cash"], 
        step=1.0
    )

    retire_cash = st.number_input(
        "Enter Retirement Cash Amount:", 
        min_value=0.0, 
        value=st.session_state["retire_cash"], 
        step=1.0
    )

    # Save the values when they change
    if misc_cash != st.session_state["misc_cash"]:
        st.session_state["misc_cash"] = misc_cash
        save_misc_cash(MISC_CASH_FILE, misc_cash)

    if retire_cash != st.session_state["retire_cash"]:
        st.session_state["retire_cash"] = retire_cash
        save_retire_cash(RETIREMENT_CASH_FILE, retire_cash)

# Display stored values
# st.write(f"Saved Miscellaneous Cash: ${st.session_state['misc_cash']}")
# st.write(f"Saved Retirement Cash: ${st.session_state['retire_cash']}")

retirement_balance = load_retire_cash(RETIREMENT_CASH_FILE)
misc_cash_num = load_misc_cash(MISC_CASH_FILE)

# Create dataframe for expenses
expenses_df = transactions_df[transactions_df['Transaction_Type'] == 'Expense']

amex_transactions = transactions_df[transactions_df['Bank'] == 'AMEX']

total_cash = chase_checkings_balance + chase_savings_balance + misc_cash_num

total_car_lease = 14364
nss_total_amount = 8625

total_car_lease_paid = expenses_df[expenses_df['Description'].str.contains("CHRYSLER CAPITAL")]['Amount'].sum()
nss_total_paid = transactions_df[transactions_df['Description'].str.contains("NASHVILLE SOFTWARE")]['Amount'].sum()
car_lease_balance = round((total_car_lease + total_car_lease_paid),2)
credit_card_balance = round(amex_transactions['Amount'].sum(),2)
nss_school_balance = (nss_total_amount + nss_total_paid)

net_worth = (total_cash + retirement_balance - credit_card_balance - car_lease_balance - nss_school_balance)

if net_worth >= 0:
    net_worth_color = 'green'
else:
    net_worth_color = 'red'
# --------- LAYOUT ----------
# Create three main columns for the dashboard layout
col1, col2 = st.columns([1.5, 3.5])
# --------- COLUMN 1: NET WORTH SUMMARY ---------
with col1:
    # Net worth metric
    if net_worth_color == 'green':  
        st.markdown(
        f"""
        <style>
            .container-networth {{
                display: flex;
                flex-direction: column;
                align-items: center; /* Center horizontally */
                justify-content: center; /* Center vertically */
                text-align: center; /* Ensure text is centered */
                width: 100%; /* Ensure it spans full column width */
            }}
            .networth-text {{
                font-size: 50px !important;
                font-weight: bold !important;
            }}
            .networth-amount {{
                font-size: 32px !important;
                font-weight: bold;
                color: green;
                margin: 0;
            }}
        </style>

        <div class="container-networth">
            <p class="networth-text">Net Worth</p>
            <p class="networth-amount">${net_worth:,.2f}</p>
        </div>
        """,
        unsafe_allow_html=True
        )
    else:
        st.markdown(
        f"""
        <style>
            .container-networth {{
                display: flex;
                flex-direction: column;
                align-items: center; /* Center horizontally */
                justify-content: center; /* Center vertically */
                text-align: center; /* Ensure text is centered */
                width: 100%; /* Ensure it spans full column width */
            }}
            .networth-text {{
                font-size: 50px !important;
                font-weight: bold !important;
            }}
            .networth-amount {{
                font-size: 32px !important;
                font-weight: bold;
                color: red;
                margin: 0;
            }}
        </style>

        <div class="container-networth">
            <p class="networth-text">Net Worth</p>
            <p class="networth-amount">-${abs(net_worth):,.2f}</p>
        </div>
        """,
        unsafe_allow_html=True
        )       


    # Cash Balance
    st.markdown(
        f"""
        <div class="container">
            <img class="custom-image" src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTXaOITWqnf8fuuebyU26oku_Z1YGZh8fF_Q&s">
            <div class="text-content">
                <p class="title-text"> Total Cash: </p>
                <p class="amount-cash">${total_cash:,.2f}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Retirement Balance
    st.markdown(
            f"""
            <div class="container">
                <img class="custom-image" src="https://th.bing.com/th/id/OIP.7vgQcqe6k6V5nENsJOX0PQHaHa?w=199&h=199&c=7&r=0&o=5&pid=1.7">
                <div class="text-content">
                    <p class="title-text"> Retirement Balance: </p>
                    <p class="amount-cash">${retirement_balance:,.2f}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


    # Credit Card Balance
    st.markdown(
            f"""
            <div class="container">
                <img class="custom-image" src="https://cdn-icons-png.flaticon.com/512/4341/4341764.png">
                <div class="text-content">
                    <p class="title-text"> Credit Card Balance: </p>
                    <p class="amount-credit">-${credit_card_balance:,.2f}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # School Balance
    st.markdown(
            f"""
            <div class="container">
                <img class="custom-image" src="https://images.vexels.com/media/users/3/166342/isolated/preview/6a46b3eea1b8b9bb4cab9a0c26dc2a74-graduation-cap-icon-graduation-icons.png">
                <div class="text-content">
                    <p class="title-text"> School Balance: </p>
                    <p class="amount-school">-${nss_school_balance:,.2f}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Car Metric
    st.markdown(
        f"""
        <style>
            .container {{
                display:flex;
                align-items: center;
            }}
            .custom-image {{
                width: 150px;  /* Change width */
                height: auto;  /* Keep aspect ratio */
            }}
            .text-content {{
                display: flex;
                margin-left: 15px;
            }}
            .title-text {{
                font-size: 16px;
                font-weight: bold;
                margin: 0;
            }}
            .amount-credit {{
                font-size: 22px;
                font-weight: bold;
                color: red;
                margin: 0;
            }}
            .amount-cash {{
                font-size: 22px;
                font-weight: bold;
                color: green;
                margin: 0;
            }}
            .amount-school {{
                font-size: 22px;
                font-weight: bold;
                color: red;
                margin: 0;
            }}
            .amount-car {{
                font-size: 22px;
                font-weight: bold;
                color: red;
                margin: 0;
            }}
        </style>
        <div class="container">
            <img class="custom-image" src="data:image/png;base64,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">
            <div class="text-content">
                <p class="title-text"> Car Lease Balance: </p>
                <p class="amount-car">-${car_lease_balance:,.2f}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label='Pay Period Income',
            value=format_currency(current_income)
            )
    with col2:
        st.metric(
            label='Pay Period Expenses',
            value=format_currency(current_expense_amount)
        )
    with col3:
        st.metric(
            label='Pay Period Savings',
            value=format_currency(current_savings)
        )
    with col4:
        st.metric(
            label='Pay Period Remaining',
            value=format_currency(remaining_balance)
        )
    selected_month = transactions_df['Pay_Period'][0]
    filtered_df = transactions_df[transactions_df['Pay_Period'] == selected_month]
    pie_plot = plot_fifty_thirty_twenty(filtered_df)
    # st.dataframe(current_pay_period_expenses)
    # pie_plot = plot_fifty_thirty_twenty(current_pay_period_expenses)
    st.pyplot(pie_plot[0])

st.plotly_chart(plot_expense_by_category(current_pay_period))