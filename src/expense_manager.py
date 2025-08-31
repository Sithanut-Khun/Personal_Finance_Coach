# src/expense_manager.py
import streamlit as st
import pandas as pd
import uuid
from datetime import date
from src.database import get_connection, get_db_engine

def add_expense(user_id, entry_date, amount, currency, merchant_name, category, sub_category, payment_method, description):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        item_id = uuid.uuid4()
        cursor.execute("""
            INSERT INTO expenses (item_id, user_id, entry_date, amount, currency, merchant_name, transaction_type, category_label, sub_category, payment_method, item_description_raw)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (item_id, user_id, entry_date, amount, currency, merchant_name, "Expense", category, sub_category, payment_method, description))
        conn.commit()
        st.success("✅ Expense added successfully!")
        get_expenses_as_df.clear() # Clear cache
    except Exception as e:
        st.error(f"❌ Failed to save expense: {e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def update_expense(item_id, user_id, entry_date, amount, currency, merchant_name, category_label, sub_category, payment_method, item_description_raw):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE expenses
            SET entry_date = %s, amount = %s, currency = %s, merchant_name = %s,
                category_label = %s, sub_category = %s, payment_method = %s,
                item_description_raw = %s
            WHERE item_id = %s AND user_id = %s
        """, (entry_date, amount, currency, merchant_name, category_label, sub_category, payment_method, item_description_raw, item_id, user_id))
        conn.commit()
        st.success("✅ Expense updated successfully!")
        get_expenses_as_df.clear()
    except Exception as e:
        st.error(f"❌ Failed to update expense: {e}")
    finally:
        cursor.close()
        conn.close()

def delete_expense(item_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM expenses WHERE item_id = %s AND user_id = %s", (item_id, user_id))
        conn.commit()
        st.success("🗑️ Expense deleted successfully!")
        get_expenses_as_df.clear()
    except Exception as e:
        st.error(f"❌ Failed to delete expense: {e}")
    finally:
        cursor.close()
        conn.close()

def get_expense_by_id(item_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE item_id = %s AND user_id = %s", (item_id, user_id))
    colnames = [desc[0] for desc in cursor.description]
    expense_data = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(zip(colnames, expense_data)) if expense_data else None

@st.cache_data
def get_expenses_as_df(user_id, start_date, end_date):
    engine = get_db_engine()
    query = """
        SELECT item_id, entry_date, amount, currency, merchant_name,
               category_label, sub_category, payment_method, item_description_raw
        FROM expenses
        WHERE user_id = %(user_id)s AND entry_date BETWEEN %(start_date)s AND %(end_date)s
        ORDER BY entry_date DESC
    """
    params = {"user_id": user_id, "start_date": start_date, "end_date": end_date}
    return pd.read_sql_query(query, engine, params=params)