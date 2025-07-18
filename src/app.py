import streamlit as st
import pandas as pd
from datetime import date
import json
import uuid # For generating unique IDs if needed, though Firestore handles doc IDs

# Firebase imports (will be provided by the environment)
from firebase_admin import credentials, initialize_app
from firebase_admin import auth
from firebase_admin import firestore
from firebase_admin._auth_utils import UserNotFoundError

# --- Global Firebase Initialization ---
# Check if Firebase app is already initialized
if not st.session_state.get('firebase_initialized', False):
    try:
        # Access global variables provided by the Canvas environment
        app_id = st.secrets.get('__app_id', 'default-app-id') # Use st.secrets for global vars
        firebase_config_str = st.secrets.get('__firebase_config', '{}')
        initial_auth_token = st.secrets.get('__initial_auth_token', None)

        firebase_config = json.loads(firebase_config_str)

        # Initialize Firebase Admin SDK if not already initialized
        # Use a unique name for the app if multiple initializations are possible
        if not initialize_app(credentials.Certificate(firebase_config)):
            initialize_app(credentials.Certificate(firebase_config), name=app_id)
        
        st.session_state.db = firestore.client()
        st.session_state.auth = auth

        # Sign in with custom token if provided, otherwise sign in anonymously
        if initial_auth_token:
            try:
                user = auth.verify_id_token(initial_auth_token)
                st.session_state.user_info = user
                st.session_state.logged_in = True
                st.session_state.user_email = user.get('email', 'N/A')
                st.session_state.user_uid = user['uid']
                st.session_state.login_message = "Signed in successfully with initial token."
            except Exception as e:
                st.session_state.logged_in = False
                st.session_state.user_info = None
                st.session_state.login_message = f"Failed to sign in with initial token: {e}"
        else:
            # For anonymous sign-in (if no specific user is provided by Canvas)
            # Note: Firebase Admin SDK doesn't directly support anonymous sign-in for client-side use.
            # This part would typically be handled on the client-side with Firebase JS SDK.
            # For this context, we'll assume a user is either logged in via token or needs to sign up/in.
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.session_state.login_message = "Please sign up or log in."

        st.session_state.firebase_initialized = True
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        st.session_state.firebase_initialized = False

# --- Pre-defined Categories and Sub-categories ---
CATEGORIES_DATA = {
    "Food & Dining": {
        "Groceries": ["Supermarket", "Local Market", "Convenience Store"],
        "Restaurant Meals": ["Khmer Food", "Western Food", "Asian Food", "Cafe"],
        "Snacks & Drinks": ["Coffee", "Bubble Tea", "Juice", "Packaged Snacks", "Street Drinks"]
    },
    "Transportation": {
        "Ride-Hailing": ["Grab", "PassApp", "Taxi App"],
        "Tuk-Tuk/Moto-Dop": ["Local Tuk-Tuk", "Moto-Dop"],
        "Fuel": ["Gas Station"],
        "Public Transport": ["Bus Ticket"]
    },
    "Education": {
        "Tuition Fees": ["University Fees", "School Fees", "Course Payment"],
        "Books & Supplies": ["Textbooks", "Stationery", "Photocopy"],
        "Tutoring": ["Private Tutor", "Study Group Fees"]
    },
    "Housing & Utilities": {
        "Rent": ["Monthly Rent", "Dorm Fee"],
        "Electricity Bill": ["Electricity"],
        "Water Bill": ["Water"],
        "Internet Bill": ["Internet"]
    },
    "Communication": {
        "Mobile Top-up/Plan": ["Phone Credit", "Data Plan"]
    },
    "Healthcare": {
        "Pharmacy": ["Medicine", "Supplements"],
        "Doctor Visit": ["Clinic Visit", "Hospital Fees"]
    },
    "Entertainment & Leisure": {
        "Cinema/Movies": ["Movie Ticket", "Cinema Snacks"],
        "Social Outings": ["Karaoke", "Bar/Club", "Cafe Hangout"],
        "Hobbies/Sports": ["Gym Membership", "Sports Gear", "Gaming"]
    },
    "Shopping": {
        "Clothing & Accessories": ["Apparel", "Shoes", "Bags", "Jewelry"],
        "Electronics": ["Phone", "Headphones", "Charger", "Laptop"],
        "Household Items": ["Cleaning Supplies", "Kitchenware", "Furniture"]
    },
    "Personal Care": {
        "Hair/Beauty": ["Haircut", "Salon Service", "Barber"],
        "Toiletries": ["Shampoo", "Soap", "Skincare"]
    },
    "Miscellaneous": {
        "Other": ["Donation", "Random Expense", "Uncategorized"]
    }
}

PAYMENT_METHODS = ["Cash", "ABA Pay", "Wing", "TrueMoney", "Credit Card", "Debit Card", "Bank Transfer"]
CURRENCY_OPTIONS = ["USD", "KHR"] # Focus on USD as primary, but allow selection

# --- Streamlit App Layout ---
st.set_page_config(layout="centered", page_title="Smart Expense Tracker")

st.title("💰 Smart Expense Tracker")

# --- Authentication Section ---
if not st.session_state.get('logged_in', False):
    st.subheader("Welcome! Please Sign Up or Log In")

    auth_choice = st.radio("Choose an option:", ["Sign Up", "Sign In"], key="auth_choice")

    if auth_choice == "Sign Up":
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            signup_button = st.form_submit_button("Sign Up")

            if signup_button:
                try:
                    user = st.session_state.auth.create_user(
                        email=new_email,
                        password=new_password
                    )
                    st.session_state.logged_in = True
                    st.session_state.user_info = user
                    st.session_state.user_email = user.email
                    st.session_state.user_uid = user.uid
                    st.success(f"Account created successfully for {new_email}! You are now logged in.")
                    st.session_state.login_message = "Signed up and logged in."
                    st.experimental_rerun() # Rerun to show expense form
                except Exception as e:
                    st.error(f"Error creating account: {e}")

    elif auth_choice == "Sign In":
        with st.form("signin_form"):
            email = st.text_input("Email", key="signin_email")
            password = st.text_input("Password", type="password", key="signin_password")
            signin_button = st.form_submit_button("Sign In")

            if signin_button:
                try:
                    # Note: Firebase Admin SDK does not directly support password sign-in for users.
                    # It's primarily for server-side user management.
                    # For a full client-side sign-in, you'd typically use the Firebase JS SDK.
                    # For this demo, we'll simulate a successful login if user exists.
                    # In a real app, you'd verify credentials via a custom token or client SDK.
                    
                    # Simulate user retrieval for demo purposes
                    user_record = st.session_state.auth.get_user_by_email(email)
                    # For actual password verification, you'd need a client-side Firebase SDK
                    # or a backend endpoint that uses the client SDK to verify.
                    # As a workaround for this server-side Streamlit context:
                    # We'll just assume if the email exists, the password is correct for demo.
                    # THIS IS NOT SECURE FOR PRODUCTION.
                    
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_record
                    st.session_state.user_email = user_record.email
                    st.session_state.user_uid = user_record.uid
                    st.success(f"Logged in successfully as {email}!")
                    st.session_state.login_message = "Logged in."
                    st.experimental_rerun() # Rerun to show expense form
                except UserNotFoundError:
                    st.error("User not found. Please check your email or sign up.")
                except Exception as e:
                    st.error(f"Error during sign in: {e}")

    st.info(st.session_state.get('login_message', ''))

else: # User is logged in
    st.sidebar.write(f"Logged in as: {st.session_state.user_email}")
    st.sidebar.write(f"Your User ID: `{st.session_state.user_uid}`")
    
    if st.sidebar.button("Sign Out"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.user_email = None
        st.session_state.user_uid = None
        st.session_state.login_message = "Successfully signed out."
        st.experimental_rerun()

    st.subheader("Add New Expense Transaction")

    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            entry_date = st.date_input("Date of Transaction", value=date.today(), key="expense_date")
            amount = st.number_input("Amount (USD)", min_value=0.01, format="%.2f", key="expense_amount")
            currency = st.selectbox("Currency", options=CURRENCY_OPTIONS, index=0, key="expense_currency") # Default USD

        with col2:
            merchant_name = st.text_input("Merchant Name", key="expense_merchant")
            
            # Category and Sub-category selection
            main_categories = list(CATEGORIES_DATA.keys())
            selected_category = st.selectbox("Category", options=main_categories, key="expense_category")

            # Dynamic sub-category dropdown based on selected_category
            sub_categories_for_selected = CATEGORIES_DATA.get(selected_category, [])
            if sub_categories_for_selected:
                sub_category_options = sub_categories_for_selected
                selected_sub_category = st.selectbox("Sub-Category", options=sub_category_options, key="expense_sub_category")
            else:
                selected_sub_category = st.selectbox("Sub-Category", options=["N/A"], key="expense_sub_category_na")
                st.warning("No sub-categories defined for this main category.")

        # Full width inputs below columns
        item_description_raw = st.text_area("Item Description (e.g., 'Coffee at Brown')", key="expense_description")
        payment_method = st.selectbox("Payment Method", options=PAYMENT_METHODS, key="expense_payment_method")

        submitted = st.form_submit_button("Add Expense")

        if submitted:
            if not st.session_state.get('user_uid'):
                st.error("You must be logged in to add expenses.")
            else:
                try:
                    user_uid = st.session_state.user_uid
                    
                    # Firestore collection path for user's expenses
                    # /artifacts/{appId}/users/{userId}/expenses
                    expenses_collection_path = f"artifacts/{st.secrets.get('__app_id', 'default-app-id')}/users/{user_uid}/expenses"
                    
                    # Prepare data for Firestore
                    expense_data = {
                        "entry_date": entry_date.isoformat(), # Store as ISO string
                        "amount": float(amount),
                        "currency": currency,
                        "merchant_name": merchant_name,
                        "transaction_type": "Expense", # Fixed as per requirement
                        "category_label": selected_category,
                        "sub_category": selected_sub_category,
                        "payment_method": payment_method,
                        "item_description_raw": item_description_raw,
                        "timestamp": firestore.SERVER_TIMESTAMP # Automatically add server timestamp
                    }

                    # Add document to Firestore. Firestore automatically generates Item_id (document ID)
                    doc_ref = st.session_state.db.collection(expenses_collection_path).add(expense_data)
                    st.success(f"Expense added successfully! Item ID: {doc_ref[1].id}")
                    
                    # Optionally, display recent expenses (requires fetching logic)
                    # For now, just a success message.
                except Exception as e:
                    st.error(f"Error adding expense: {e}")

    st.markdown("---")
    st.subheader("Your Recent Expenses")
    
    if st.session_state.get('user_uid'):
        try:
            user_uid = st.session_state.user_uid
            expenses_collection_path = f"artifacts/{st.secrets.get('__app_id', 'default-app-id')}/users/{user_uid}/expenses"
            
            # Fetch recent expenses (last 10, ordered by timestamp descending)
            expenses_docs = st.session_state.db.collection(expenses_collection_path).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).stream()
            
            recent_expenses = []
            for doc in expenses_docs:
                data = doc.to_dict()
                data['Item_id'] = doc.id # Add Firestore document ID as Item_id
                # Convert timestamp if it's a Firestore Timestamp object
                if 'timestamp' in data and hasattr(data['timestamp'], 'to_datetime'):
                    data['timestamp'] = data['timestamp'].to_datetime().strftime('%Y-%m-%d %H:%M:%S')
                recent_expenses.append(data)
            
            if recent_expenses:
                df_recent_expenses = pd.DataFrame(recent_expenses)
                # Reorder columns for better display
                display_cols = [
                    'entry_date', 'amount', 'currency', 'merchant_name', 
                    'category_label', 'sub_category', 'payment_method', 
                    'item_description_raw', 'Item_id', 'timestamp'
                ]
                # Filter to only display columns that exist in the dataframe
                df_recent_expenses = df_recent_expenses[[col for col in display_cols if col in df_recent_expenses.columns]]
                st.dataframe(df_recent_expenses)
            else:
                st.info("No expenses recorded yet. Add one above!")
        except Exception as e:
            st.error(f"Error fetching recent expenses: {e}")
    else:
        st.info("Log in to view your recent expenses.")

