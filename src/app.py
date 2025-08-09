import streamlit as st
import uuid
import pandas as pd
import psycopg2
import hashlib
from datetime import datetime, date
import uuid
import random
import string
import toml
from streamlit_cookies_manager import EncryptedCookieManager
from sqlalchemy import create_engine

# Use the secret from the .toml file
cookie_secret = st.secrets["cookie"]["secret"]

cookies = EncryptedCookieManager(
    prefix="myapp_",
    password=cookie_secret
)
if not cookies.ready():
    st.stop()

# ----------------------------- LOAD DB CONFIG -----------------------------
DB_CONFIG = toml.load("src/.streamlit/secrets.toml")['database']

@st.cache_resource
def get_db_engine():
    db_uri = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return create_engine(db_uri)

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# ----------------------------- AUTHENTICATION -----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generate_user_id():
    timestamp = int(datetime.now().timestamp()) 
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"USR{timestamp}{suffix}"  

def create_user(email, password, username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        conn.close()
        return False
    user_id = generate_user_id()
    hashed_password = hash_password(password)
    cur.execute(
        "INSERT INTO users (user_id, email, password_hash, username) VALUES (%s, %s, %s, %s)",
        (user_id, email, hashed_password, username),
    )
    conn.commit()
    conn.close()
    return True

def authenticate(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = hash_password(password)
    cursor.execute("SELECT user_id, username FROM users WHERE email = %s AND password_hash = %s", (email, hashed))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result if result else None

def reset_password(user_id, email, new_password):
    """Resets the password only if the user_id and email match."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if the user_id and email combination is valid first
    cursor.execute("SELECT 1 FROM users WHERE user_id = %s AND email = %s", (user_id, email))
    if cursor.fetchone():
        hashed = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (hashed, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    else:
        # The user_id and email did not match any record
        cursor.close()
        conn.close()
        return False

def update_username(user_id, new_username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username = %s WHERE user_id = %s", (new_username, user_id))
    conn.commit()
    cursor.close()
    conn.close()

# ----------------------------- PAGE STATE NAVIGATION -----------------------------
def switch_page(page_name):
    st.session_state.auth_page = page_name
    st.rerun()

# ----------------------------- MAIN APP -----------------------------



def show_login():
    st.markdown("""
        <h1 style='text-align: center;'>💰 Smart Expense Tracker</h1>
        """, unsafe_allow_html=True)
    
    left_margin, form_col, right_margin = st.columns([1, 1.5, 1])
    
    with form_col:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    result = authenticate(email, password)
                    if result:
                        user_id, username = result
                        st.session_state.user_id = user_id
                        st.session_state.email = email
                        st.session_state.username = username
                        cookies["user_id"] = user_id
                        cookies["email"] = email
                        cookies["username"] = username
                        cookies.save()
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")

        if st.button("Sign Up", use_container_width=True):
            switch_page("signup")
        
        if st.button("Forgot Password?", type="tertiary"):
            switch_page("reset")


def show_reset():
    """A two-step form for resetting a password, confirming with User ID."""
    st.markdown("""
        <h1 style='text-align: center;'>Reset Your Password</h1>
        """, unsafe_allow_html=True)
    left_margin, form_col, right_margin = st.columns([1, 1.5, 1])

    with form_col:
        st.subheader("Reset Password")

        # Initialize state for the two-step process
        if 'reset_step' not in st.session_state:
            st.session_state.reset_step = 1
        
        # Step 1: Gather new password info
        with st.form("reset_form_step1"):
            st.markdown("##### Step 1: Enter New Password Details")
            st.text_input("Your Account Email", key="reset_email")
            st.text_input("New Password", type="password", key="new_password")
            st.text_input("Confirm New Password", type="password", key="confirm_password")
            
            submitted_step1 = st.form_submit_button("Proceed to Confirmation")

            if submitted_step1:
                if not all([st.session_state.reset_email, st.session_state.new_password, st.session_state.confirm_password]):
                    st.error("Please fill all fields.")
                elif st.session_state.new_password != st.session_state.confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # No need to reassign, just move to step 2 and the values persist
                    st.session_state.reset_step = 2
                    st.rerun()

        # Step 2: Confirmation with User ID
        if st.session_state.reset_step == 2:
            st.markdown("---")
            with st.form("reset_form_step2"):
                st.markdown("##### Step 2: Confirm Your Identity")
                st.warning("To finalize, please enter your unique User ID.")
                
                user_id = st.text_input("User ID", key="reset_user_id_confirm")
                submitted_step2 = st.form_submit_button("Confirm and Reset Password")

                if submitted_step2:
                    if not user_id:
                        st.error("User ID is required to confirm.")
                    else:
                        success = reset_password(
                            user_id, 
                            st.session_state.reset_email, 
                            st.session_state.new_password 
                        )
                        if success:
                            st.success("Password updated successfully! Please log in.")
                            # Clean up session state and switch to login
                            del st.session_state.reset_step
                            del st.session_state.reset_email
                            del st.session_state.new_password
                            del st.session_state.confirm_password
                            switch_page("login")
                        else:
                            st.error("Invalid User ID or Email. Please check your details and try again.")
        
        # "Back to Login" button should reset the flow
        if st.button("Back to Login", use_container_width=True):
            if 'reset_step' in st.session_state:
                del st.session_state.reset_step
            if 'reset_email' in st.session_state:
                del st.session_state.reset_email
            if 'new_password' in st.session_state:
                del st.session_state.new_password
            if 'confirm_password' in st.session_state:
                del st.session_state.confirm_password
            switch_page("login")

def show_signup():
    st.markdown("""
        <h1 style='text-align: center;'>Create an Account</h1>
        """, unsafe_allow_html=True)
    left_margin, form_col, right_margin = st.columns([1, 1.5, 1])

    with form_col:
        st.subheader("Sign Up")
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email", max_chars=40, help="Max 40 characters allowed")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
            username = st.text_input("What should we call you?", key="signup_username", max_chars=30, help="Max 30 characters allowed")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if not email or not username or not password or not confirm_password:
                    st.error("Please fill all fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success = create_user(email, password, username)
                    if success:
                        st.success("Account created successfully! Please log in.")
                        switch_page("login")
                    else:
                        st.warning("An account with that email already exists.")

        if st.button("Back to Login", use_container_width=True):
            switch_page("login")



def show_update_username():
    new_username = st.text_input("New Username", value=st.session_state.username, max_chars=30, help="Max 30 characters allowed")
    if st.button("✅ Save Changes", key="update_username_button"):
        if new_username.strip():
            update_username(st.session_state.user_id, new_username)
            st.session_state.username = new_username
            cookies["username"] = new_username
            cookies.save()
            st.session_state.show_update_username_form = False
            st.success("Username updated successfully!")
            st.rerun()
        else:
            st.warning("Username cannot be empty.")
            
            

def show_user_info():
    """Displays user ID, email, and register date, initially hidden behind a button."""
    st.markdown("---")
    st.subheader("My Details")
    
    if 'show_details' not in st.session_state:
        st.session_state.show_details = False

    if st.session_state.show_details:
        # Fetch created_at from DB if not already in session_state
        if 'created_at' not in st.session_state:
            
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT created_at FROM users WHERE user_id = %s", (st.session_state.user_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()

            if result:
                st.session_state.created_at = result[0].strftime("%d-%m-%Y")
            else:
                st.session_state.created_at = "N/A"

        st.text_input("User ID", value=st.session_state.user_id, disabled=True)
        st.text_input("Email", value=st.session_state.email, disabled=True)
        st.text_input("Register Date", value=st.session_state.created_at, disabled=True)

        if st.button("Hide My Details"):
            st.session_state.show_details = False
            st.rerun()
    else:
        if st.button("Show My Details"):
            st.session_state.show_details = True
            st.rerun()
 

# ----------------------------- EXPENSE TRACKER -----------------------------
CATEGORIES_DATA = {
    "Dining": ["Eatary Meals", "Restaurant Meals", "Snacks", "Drinks", "Fast Food"], 
    "Transportation": ["Ride-Hailing", "Tuk-Tuk/Moto-Dop", "Fuel", "Public Transport", "Parking Fees"], 
    "Education": ["Tuition Fees", "Books & Supplies", "Online Courses", "Workshops/Seminars"], 
    "Housing & Utilities": ["Rent", "Electricity Bill", "Water Bill", "Internet Bill", "Home Supplies"], 
    "Food & Groceries": ["Meat", "Vegetables", "Fruits", "Staples", "Snacks & Beverages", "Fish & Seafood","Condiments & Spices", "Dairy Products", "Canned & Packaged Foods"],
    "Communication": ["Mobile Top-up/Plan"], 
    "Healthcare": ["Pharmacy", "Doctor Visit", "Medical Bills", "Health Supplements"], 
    "Insurance": ["Health Insurance", "Vehicle Insurance", "Home Insurance"],
    "Entertainment & Leisure": ["Cinema/Movies", "Social Outings", "Hobbies/Sports", "Gaming", "Subscriptions"], 
    "Shopping": ["Clothing & Accessories", "Electronics", "Household Items"], 
    "Social & Charity": ["Donations", "Gifts", "Events/Parties"],
    "Personal Care": ["Hair/Beauty", "Gym/Fitness", "Skincare"], 
    "Maintenance & Repairs": ["Vehicle Maintenance", "Home Repairs", "Appliance Repairs"],
    "Travel & Vacation": ["Flights", "Accommodation", "Travel Insurance"],
    "Assets & Investments": ["Stocks/Mutual Funds", "Cryptocurrency", "Real Estate", "Retirement Savings", "Vehicles"],
    "Financial Services": ["Bank Fees", "Loan Payments", "Credit Card Payments"],
    "Taxes": ["Income Tax", "Property Tax", "Sales Tax", "Other Taxes"],
    "Miscellaneous": ["Other"]
}
PAYMENT_METHODS = ["Cash", "Mobile Pay","Credit Card", "Debit Card", "Other"]
CURRENCY_OPTIONS = ["USD", "KHR"]

def update_expense(item_id, entry_date, amount, currency, merchant_name, category_label, sub_category, payment_method, item_description_raw):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE expenses
            SET entry_date = %s, amount = %s, currency = %s, merchant_name = %s,
                category_label = %s, sub_category = %s, payment_method = %s,
                item_description_raw = %s
            WHERE item_id = %s AND user_id = %s
        """, (
            entry_date, amount, currency, merchant_name, category_label,
            sub_category, payment_method, item_description_raw, item_id, st.session_state.user_id
        ))
        conn.commit()
        st.success("✅ Expense updated successfully!")
        get_expenses_as_df.clear()
    except Exception as e:
        st.error(f"❌ Failed to update expense: {e}")
    finally:
        cursor.close()
        conn.close()


def delete_expense(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM expenses WHERE item_id = %s AND user_id = %s", (item_id, st.session_state.user_id))
        conn.commit()
        st.success("🗑️ Expense deleted successfully!")
        get_expenses_as_df.clear()
    except Exception as e:
        st.error(f"❌ Failed to delete expense: {e}")
    finally:
        cursor.close()
        conn.close()

def get_expense_by_id(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE item_id = %s AND user_id = %s", (item_id, st.session_state.user_id))
    colnames = [desc[0] for desc in cursor.description]
    expense_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if expense_data:
        return dict(zip(colnames, expense_data))
    return None


def show_expense_form(expense_data=None):
    is_edit_mode = expense_data is not None
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("📅 Date of Transaction", value=expense_data['entry_date'] if is_edit_mode else date.today())
            amount = st.number_input("💵 Amount", min_value=0.01, format="%.2f", value=float(expense_data['amount']) if is_edit_mode else 0.01)
            currency = st.selectbox("💱 Currency", options=CURRENCY_OPTIONS, index=CURRENCY_OPTIONS.index(expense_data['currency']) if is_edit_mode and expense_data['currency'] in CURRENCY_OPTIONS else 0)
        with col2:
            merchant_name = st.text_input("🏪 Merchant Name", value=expense_data['merchant_name'] if is_edit_mode else "", max_chars = 30, help="Max 30 characters allowed")
            all_categories = list(CATEGORIES_DATA.keys())
            category_index = all_categories.index(expense_data['category_label']) if is_edit_mode and expense_data['category_label'] in all_categories else 0
            selected_category = st.selectbox("📂 Category", all_categories, index=category_index)
            sub_categories = CATEGORIES_DATA[selected_category]
            sub_category_index = sub_categories.index(expense_data['sub_category']) if is_edit_mode and expense_data['sub_category'] in sub_categories else 0
            selected_sub_category = st.selectbox("📁 Sub-Category", sub_categories, index=sub_category_index)
        item_description_raw = st.text_area("📝 Item Description", value=expense_data['item_description_raw'] if is_edit_mode else "", max_chars = 70, help="Max 70 characters allowed")
        payment_method_index = PAYMENT_METHODS.index(expense_data['payment_method']) if is_edit_mode and expense_data['payment_method'] in PAYMENT_METHODS else 0
        payment_method = st.selectbox("💳 Payment Method", options=PAYMENT_METHODS, index=payment_method_index)
        if is_edit_mode:
            if st.button("💾 Update Expense"):
                update_expense(item_id=expense_data['item_id'], entry_date=entry_date, amount=amount, currency=currency, merchant_name=merchant_name, category_label=selected_category, sub_category=selected_sub_category, payment_method=payment_method, item_description_raw=item_description_raw)
                st.session_state.editing_expense_id = None
                st.rerun()
        else:
            if st.button("✅ Add Expense"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    item_id =  str(uuid.uuid4())  
                    cursor.execute("""
                        INSERT INTO expenses (item_id, user_id, entry_date, amount, currency, merchant_name, transaction_type, category_label, sub_category, payment_method, item_description_raw)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (item_id, st.session_state.user_id, entry_date, amount, currency, merchant_name, "Expense", selected_category, selected_sub_category, payment_method, item_description_raw))
                    conn.commit()
                    st.success("✅ Expense added successfully!")
                    get_expenses_as_df.clear()
                    st.session_state.show_add_form = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to save expense: {e}")
                finally:
                    if 'conn' in locals() and conn:
                        cursor.close()
                        conn.close()

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
    df = pd.read_sql_query(query, engine, params=params)
    return df


def show_expense_history(df):
    # --- STEP 1: Handle Delete Confirmation Pop-up (before rendering the table) ---
    deleting_item_id = st.session_state.get("deleting_expense_id")
    if deleting_item_id:
        expense_to_delete = get_expense_by_id(deleting_item_id)
        if expense_to_delete:
            st.warning("⚠️ Delete Record Confirmation")
            st.markdown(f"""
                <div style='
                    background-color: #000000; 
                    border-left: 5px solid #ffc107; 
                    padding: 10px; 
                    margin-bottom: 20px;
                    border-radius: 5px;
                '>
                    Are you sure you want to delete this expense record?
                    <br>
                    <b>Date:</b> {expense_to_delete['entry_date']}<br>
                    <b>Amount:</b> {expense_to_delete['amount']:.2f} {expense_to_delete['currency']}<br>
                    <b>Category:</b> {expense_to_delete['category_label']}<br>
                    <b>Sub-Category:</b> {expense_to_delete['sub_category']}<br>
                    <b>Merchant:</b> {expense_to_delete['merchant_name']}
                </div>
            """, unsafe_allow_html=True)
            
            # Use columns to place buttons side-by-side
            confirm_cols = st.columns(2)
            if confirm_cols[0].button("✔️ Yes, delete", key="confirm_delete_btn", use_container_width=True, type="primary"):
                delete_expense(deleting_item_id)
                st.session_state.deleting_expense_id = None
                st.rerun()
            if confirm_cols[1].button("❌ Cancel", key="cancel_delete_btn", use_container_width=True):
                st.session_state.deleting_expense_id = None
                st.rerun()
        else:
            st.error("Error: Could not find the record to delete.")
            st.session_state.deleting_expense_id = None
            st.rerun()
        return  # Stop execution here to not show the table while the pop-up is active

    # --- STEP 2: Render the expense history table (only if no deletion is pending) ---
    if df.empty:
        st.info("No expenses found for the selected date range.")
        return

    header_cols = st.columns([2, 2, 2, 2, 2, 3, 2, 1, 1])
    header_cols[0].markdown("**Date**")
    header_cols[1].markdown("**Amount**")
    header_cols[2].markdown("**Merchant**")
    header_cols[3].markdown("**Category**")
    header_cols[4].markdown("**Sub-Category**")
    header_cols[5].markdown("**Description**")
    header_cols[6].markdown("**Payment Method**")
    st.markdown("---")

    for index, row in df.iterrows():
        item_id = row["item_id"]
        cols = st.columns([2, 2, 2, 2, 2, 3, 2, 1, 1])

        cols[0].text(row["entry_date"].strftime("%Y-%m-%d"))
        cols[1].text(f"{row['amount']:.2f} {row['currency']}")
        cols[2].text(row["merchant_name"])
        cols[3].text(row["category_label"])
        cols[4].text(row["sub_category"])

        full_description = row["item_description_raw"] or ""
        max_len = 30
        display_text = (full_description[:max_len] + '...') if len(full_description) > max_len else full_description
        cols[5].text(display_text, help=full_description if full_description else "No description")

        cols[6].text(row["payment_method"])

        if cols[7].button("✏️", key=f"edit_{item_id}", help="Edit this expense"):
            st.session_state.editing_expense_id = item_id
            st.rerun()

        if cols[8].button("🗑️", key=f"delete_{item_id}", help="Delete this expense"):
            st.session_state.deleting_expense_id = item_id
            st.rerun()



# ----------------------------- PAGE ROUTER -----------------------------
def set_active_tab(tab_name):
    st.session_state.active_tab = tab_name


def main():
    st.set_page_config(page_title="Smart Expense Tracker", layout="wide")
    
    # --- Session state initialization ---
    if "auth_page" not in st.session_state: st.session_state.auth_page = "login"
    if "user_id" not in st.session_state: st.session_state.user_id = None
    if "show_update_username_form" not in st.session_state: st.session_state.show_update_username_form = False
    if "show_add_form" not in st.session_state: st.session_state.show_add_form = False
    if "editing_expense_id" not in st.session_state: st.session_state.editing_expense_id = None
    if "deleting_expense_id" not in st.session_state: st.session_state.deleting_expense_id = None
    if "active_tab" not in st.session_state: st.session_state.active_tab = "Expense"
    
    # --- Cookie-based authentication check ---
    if not st.session_state.user_id and cookies.get("user_id"):
        st.session_state.user_id = cookies.get("user_id")
        st.session_state.email = cookies.get("email")
        st.session_state.username = cookies.get("username")

    # --- Conditional rendering for auth pages vs. main app ---
    if not st.session_state.user_id:
        page_map = {"login": show_login, "signup": show_signup, "reset": show_reset}
        page_map[st.session_state.auth_page]()
        return

    # --- Logged-in view starts here ---
    st.title("💰 Smart Expense Tracker")

    # --- Sidebar content with modern buttons ---
    with st.sidebar:
        st.success(f"Welcome {st.session_state.username}!", icon="👋")
        st.markdown("---")


        st.button(
            "User Profile",
            use_container_width=True,
            type="primary" if st.session_state.active_tab == "User Profile" else "secondary",
            on_click=set_active_tab,
            args=("User Profile",)
        )

        st.button(
            "Expense",
            use_container_width=True,
            type="primary" if st.session_state.active_tab == "Expense" else "secondary",
            on_click=set_active_tab,
            args=("Expense",)
        )
        st.button(
            "Dashboard",
            use_container_width=True,
            type="primary" if st.session_state.active_tab == "Dashboard" else "secondary",
            on_click=set_active_tab,
            args=("Dashboard",)
        )
        
        
        st.button(
            "Chatbot",
            use_container_width=True,
            type="primary" if st.session_state.active_tab == "Chatbot" else "secondary",
            on_click=set_active_tab,
            args=("Chatbot",)
        )
           

        st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
        if st.button("Logout", key="sidebar_logout_button", use_container_width=True):
            # Set cookies to empty strings to effectively delete them
            cookies["user_id"] = ""
            cookies["email"] = ""
            cookies["username"] = ""
            cookies.save()

            # Manually reset session state keys to their initial values
            st.session_state.user_id = None
            st.session_state.username = ""
            st.session_state.email = ""
            st.session_state.auth_page = "login"
            st.session_state.active_tab = "Expense" # Reset to default tab
            st.session_state.editing_expense_id = None
            st.session_state.deleting_expense_id = None
            st.session_state.show_add_form = False
            st.session_state.show_update_username_form = False

            # Clear the data cache on logout
            get_expenses_as_df.clear()
            st.rerun()

    # --- Main content rendered based on the active tab ---
    if st.session_state.active_tab == "User Profile":
        st.markdown("## 👤 User Profile Settings")
        if st.session_state.show_update_username_form:
            show_update_username()
            if st.button("Cancel"):
                st.session_state.show_update_username_form = False
                st.rerun()
        else:
            st.button("✏️ Update Username", on_click=lambda: st.session_state.update({"show_update_username_form": True}))

        show_user_info()
        
    elif st.session_state.active_tab == "Expense":
        if st.session_state.editing_expense_id:
            st.markdown("### ✏️ Edit Expense")
            expense_to_edit = get_expense_by_id(st.session_state.editing_expense_id)
            if expense_to_edit:
                show_expense_form(expense_data=expense_to_edit)
                if st.button("❌ Cancel Edit"):
                    st.session_state.editing_expense_id = None
                    st.rerun()
            else:
                st.error("Could not find the expense to edit.")
                st.session_state.editing_expense_id = None
        
        elif st.session_state.show_add_form:
            st.markdown("### 📝 Add New Expense")
            show_expense_form()
            if st.button("❌ Close Form"):
                st.session_state.show_add_form = False
                st.rerun()
        else:
            if st.button("➕ Add New Expense"):
                st.session_state.show_add_form = True
                st.rerun()
            st.markdown("---")
            st.markdown("### 📊 Expense History")
            today = date.today()
            first_day_of_month = today.replace(day=1)
            filter_cols = st.columns(2)
            start_date_filter = filter_cols[0].date_input("🗓️ Start Date", value=first_day_of_month)
            end_date_filter = filter_cols[1].date_input("🗓️ End Date", value=today)
            if start_date_filter > end_date_filter:
                st.warning("Start date cannot be after end date.")
            else:
                df_expenses = get_expenses_as_df(st.session_state.user_id, start_date_filter, end_date_filter)
                df_download = df_expenses.rename(columns={'entry_date': 'Date', 'amount': 'Amount', 'currency': 'Currency', 'merchant_name': 'Merchant', 'category_label': 'Category', 'sub_category': 'Sub-Category', 'payment_method': 'Payment Method', 'item_description_raw': 'Description'}).drop(columns=['item_id'])
                csv = df_download.to_csv(index=False).encode('utf-8')
                _, col_btn = st.columns([5, 1])
                with col_btn:
                    st.download_button(label="📥 Download CSV", data=csv, file_name=f"expenses_{start_date_filter}_to_{end_date_filter}.csv", mime="text/csv", help="Download the filtered expense data as a CSV file")
                show_expense_history(df_expenses)

    elif st.session_state.active_tab == "Dashboard":
        st.markdown("## 📈 Dashboard (Coming Soon...)")
        st.info("This page will show analytics and trends in future updates.")
        
    elif st.session_state.active_tab == "Chatbot":
        st.markdown("## 🤖 Chatbot (Coming Soon...)")
        st.info("This page will feature a chatbot for financial advice in future updates.")
        

if __name__ == "__main__":
    main()