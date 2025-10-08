import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from src.expense_manager import get_expenses_as_df

# Constants for currency conversion
KHR_TO_USD = 4100  # Update this rate as needed

def convert_to_currency(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return amount
    if from_currency == 'KHR' and to_currency == 'USD':
        return amount / KHR_TO_USD
    if from_currency == 'USD' and to_currency == 'KHR':
        return amount * KHR_TO_USD
    return amount

def show_dashboard_page():
    st.header("📈 Expense Dashboard")

    # --- Load Data ---
    # Load all data initially to find the date range for the selectors
    initial_start_date = datetime(2000, 1, 1).date()
    initial_end_date = datetime.now().date()
    
    all_df = get_expenses_as_df(st.session_state.user_id, initial_start_date, initial_end_date)
    
    if all_df.empty:
        st.warning("No expense data found. Add some expenses to see the dashboard.")
        return

    # Convert entry_date to just date objects for comparison
    all_df['entry_date'] = pd.to_datetime(all_df['entry_date']).dt.date
    
    earliest_date = all_df['entry_date'].min()
    latest_date = all_df['entry_date'].max()

    # --- Filters ---
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=earliest_date,
            min_value=earliest_date,
            max_value=latest_date,
            key="dashboard_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=latest_date,
            min_value=earliest_date,
            max_value=latest_date,
            key="dashboard_end_date"
        )
    with col3:
        display_currency = st.selectbox(
            "Currency",
            options=['USD', 'KHR'],
            key="currency_selector"
        )
    
    if start_date > end_date:
        st.error("Error: Start date cannot be after end date.")
        return

    # Filter data based on selected date range
    df = all_df[(all_df['entry_date'] >= start_date) & (all_df['entry_date'] <= end_date)]
    
    if df.empty:
        st.warning("No expense data available for the selected period.")
        return

    # --- Data Processing ---
    df['converted_amount'] = df.apply(
        lambda x: convert_to_currency(x['amount'], x['currency'], display_currency),
        axis=1
    )
    currency_symbol = "៛" if display_currency == "KHR" else "$"
    
    # Replace blank merchant names with 'Other'
    df['merchant_name'] = df['merchant_name'].str.strip().fillna('Other')
    df.loc[df['merchant_name'] == '', 'merchant_name'] = 'Other'


    # --- Display Metrics ---
    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    total_expenses = df['converted_amount'].sum()
    avg_daily = df.groupby('entry_date')['converted_amount'].sum().mean()
    top_category = df.groupby('category_label')['converted_amount'].sum().idxmax()
    
    m_col1.metric("Total Expenses", f"{currency_symbol}{total_expenses:,.2f}")
    m_col2.metric("Average Daily", f"{currency_symbol}{avg_daily:,.2f}")
    m_col3.metric("Transactions", len(df))
    m_col4.metric("Top Spend Category", top_category)
    # m_col4.metric("Categories", df['category_label'].nunique())
    st.markdown("---")

    st.subheader("Expense Trends Over Time")
    daily_expenses = df.groupby('entry_date')['converted_amount'].sum().reset_index()
    fig_line = px.area(
        daily_expenses,
        x='entry_date',
        y='converted_amount',
        title=f'Daily Expenses ({display_currency})',
        labels={
            "entry_date": "Date",
            "converted_amount": f"Amount ({display_currency})"
        }
    )
    fig_line.update_layout(
        yaxis_title=f"Amount ({display_currency})", 
        xaxis_title="Date",
        yaxis_tickformat = ',.0f' # This line prevents abbreviations like 'k'
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- Visualizations ---
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        st.subheader("Category Distribution")
        category_totals = df.groupby('category_label')['converted_amount'].sum()
        fig_pie = px.pie(
            values=category_totals.values,
            names=category_totals.index,
            title=f'Expenses by Category ({display_currency})',
            hole=.3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with v_col2:
        st.subheader("Top Merchants")
        merchant_totals = df.groupby('merchant_name')['converted_amount'].sum().nlargest(5).sort_values()
        fig_bar = px.bar(
            x=merchant_totals.values,
            y=merchant_totals.index,
            orientation='h',
            title=f'Top 5 Merchants by Spend ({display_currency})',
            labels={'x': f'Amount ({display_currency})', 'y': 'Merchant'}
        )
        fig_bar.update_layout(
            xaxis_tickformat = ',.0f' 
        )
        st.plotly_chart(fig_bar, use_container_width=True)


