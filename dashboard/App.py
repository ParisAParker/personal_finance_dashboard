# Main Streamlit dashboard app
import streamlit as st
import pandas as pd

# Set up the page title
st.set_page_config(
    page_title="Personal Finance Dashboard",
    layout = "wide"
    )

st.title("💰 Personal Financial Dashboard")
st.write("Track and analyze your spending habits over time.")

st.sidebar.header("🔍 Navigation")