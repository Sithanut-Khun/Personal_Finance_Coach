# src/ui/expense_page.py
import streamlit as st
from datetime import date
from src.utils import CATEGORIES_DATA, PAYMENT_METHODS, CURRENCY_OPTIONS
from src.expense_manager import (
    add_expense,
    update_expense,
    delete_expense,
    get_expense_by_id,
    get_expenses_as_df
)

def _show_expense_form(expense_data=None):
    is_edit_mode = expense_data is not None
    
    col1, col2 = st.columns(2)
    with col1:
        entry_date = st.date_input("📅 Date", value=expense_data['entry_date'] if is_edit_mode else date.today())
        amount = st.number_input("💵 Amount", min_value=0.01, format="%.2f", value=float(expense_data['amount']) if is_edit_mode else 0.01)
        currency = st.selectbox("💱 Currency", CURRENCY_OPTIONS, index=CURRENCY_OPTIONS.index(expense_data['currency']) if is_edit_mode else 0)
    with col2:
        merchant_name = st.text_input("🏪 Merchant", value=expense_data['merchant_name'] if is_edit_mode else "", max_chars=30)
        all_categories = list(CATEGORIES_DATA.keys())
        cat_index = all_categories.index(expense_data['category_label']) if is_edit_mode else 0
        selected_category = st.selectbox("📂 Category", all_categories, index=cat_index)
        sub_categories = CATEGORIES_DATA[selected_category]
        sub_cat_index = sub_categories.index(expense_data['sub_category']) if is_edit_mode and expense_data['sub_category'] in sub_categories else 0
        selected_sub_category = st.selectbox("📁 Sub-Category", sub_categories, index=sub_cat_index)
    
    item_description = st.text_area("📝 Description", value=expense_data['item_description_raw'] if is_edit_mode else "", max_chars=70)
    pay_method_index = PAYMENT_METHODS.index(expense_data['payment_method']) if is_edit_mode and expense_data['payment_method'] in PAYMENT_METHODS else 0
    payment_method = st.selectbox("💳 Payment Method", PAYMENT_METHODS, index=pay_method_index)

    if is_edit_mode:
        if st.button("💾 Update Expense"):
            update_expense(expense_data['item_id'], st.session_state.user_id, entry_date, amount, currency, merchant_name, selected_category, selected_sub_category, payment_method, item_description)
            st.session_state.editing_expense_id = None
            st.rerun()
    else:
        if st.button("✅ Add Expense"):
            add_expense(st.session_state.user_id, entry_date, amount, currency, merchant_name, selected_category, selected_sub_category, payment_method, item_description)
            st.session_state.show_add_form = False
            st.rerun()

def _show_expense_history(df):
    if st.session_state.get("deleting_expense_id"):
        item_id = st.session_state.deleting_expense_id
        expense = get_expense_by_id(item_id, st.session_state.user_id)
        st.warning("⚠️ Delete Record Confirmation")
        st.markdown(f"Are you sure you want to delete the expense from **{expense['entry_date']}** for **{expense['amount']:.2f} {expense['currency']}**?")
        c1, c2 = st.columns(2)
        if c1.button("✔️ Yes, delete", use_container_width=True, type="primary"):
            delete_expense(item_id, st.session_state.user_id)
            st.session_state.deleting_expense_id = None
            st.rerun()
        if c2.button("❌ Cancel", use_container_width=True):
            st.session_state.deleting_expense_id = None
            st.rerun()
        return

    if df.empty:
        st.info("No expenses found for the selected date range.")
        return
    
    # Render table header and rows
    header_cols = st.columns([2, 2, 2, 2, 2, 3, 2, 1, 1])
    headers = ["Date", "Amount", "Merchant", "Category", "Sub-Category", "Description", "Payment", "Edit", "Del"]
    for col, header in zip(header_cols, headers):
        col.markdown(f"**{header}**")
    st.markdown("---")

    for _, row in df.iterrows():
        item_id = row["item_id"]
        cols = st.columns([2, 2, 2, 2, 2, 3, 2, 1, 1])
        cols[0].text(row["entry_date"].strftime("%Y-%m-%d"))
        cols[1].text(f"{row['amount']:.2f} {row['currency']}")
        cols[2].text(row["merchant_name"])
        cols[3].text(row["category_label"])
        cols[4].text(row["sub_category"])
        cols[5].text(row["item_description_raw"], help=row["item_description_raw"] or "No description")
        cols[6].text(row["payment_method"])
        if cols[7].button("✏️", key=f"edit_{item_id}", help="Edit"):
            st.session_state.editing_expense_id = item_id
            st.rerun()
        if cols[8].button("🗑️", key=f"delete_{item_id}", help="Delete"):
            st.session_state.deleting_expense_id = item_id
            st.rerun()

def show_expense_page():
    if st.session_state.get("editing_expense_id"):
        st.markdown("### ✏️ Edit Expense")
        expense_to_edit = get_expense_by_id(st.session_state.editing_expense_id, st.session_state.user_id)
        if expense_to_edit:
            _show_expense_form(expense_data=expense_to_edit)
            if st.button("❌ Cancel Edit"):
                st.session_state.editing_expense_id = None
                st.rerun()
    elif st.session_state.get("show_add_form"):
        st.markdown("### 📝 Add New Expense")
        _show_expense_form()
        if st.button("❌ Close Form"):
            st.session_state.show_add_form = False
            st.rerun()
    else:
        if st.button("➕ Add New Expense"):
            st.session_state.show_add_form = True
            st.rerun()
        st.markdown("---")
        st.markdown("### 📊 Expense History")
        
        c1, c2 = st.columns(2)
        start_date = c1.date_input("🗓️ Start Date", value=date.today().replace(day=1))
        end_date = c2.date_input("🗓️ End Date", value=date.today())

        if start_date > end_date:
            st.warning("Start date cannot be after end date.")
        else:
            df = get_expenses_as_df(st.session_state.user_id, start_date, end_date)
            # Add download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f'expenses_{start_date}_to_{end_date}.csv',
                mime='text/csv'
            )
            _show_expense_history(df)