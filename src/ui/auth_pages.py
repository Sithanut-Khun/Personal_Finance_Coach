# src/ui/auth_pages.py
import streamlit as st
from src.auth import authenticate, create_user, reset_password
from src.utils import switch_page

def show_login_page(cookies):
    st.markdown("<h1 style='text-align: center;'>💰 Smart Expense Tracker</h1>", unsafe_allow_html=True)
    left, form_col, right = st.columns([1, 1.5, 1])
    with form_col:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
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

def show_signup_page():
    st.markdown("<h1 style='text-align: center;'>Create an Account</h1>", unsafe_allow_html=True)
    left, form_col, right = st.columns([1, 1.5, 1])
    with form_col:
        st.subheader("Sign Up")
        with st.form("signup_form"):
            email = st.text_input("Email", max_chars=40)
            password = st.text_input("Password", type="password", max_chars=40)
            confirm_password = st.text_input("Confirm Password", type="password", max_chars=40)
            username = st.text_input("What should we call you?", max_chars=30)
            if st.form_submit_button("Register"):
                if not all([email, password, confirm_password, username]):
                    st.error("Please fill all fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    if create_user(email, password, username):
                        st.success("Account created successfully! Please log in.")
                        switch_page("login")
                    else:
                        st.warning("An account with that email already exists.")
        if st.button("Back to Login", use_container_width=True):
            switch_page("login")

def show_reset_page():
    st.markdown("<h1 style='text-align: center;'>Reset Your Password</h1>", unsafe_allow_html=True)
    left, form_col, right = st.columns([1, 1.5, 1])
    with form_col:
        st.subheader("Reset Password")
        if 'reset_step' not in st.session_state:
            st.session_state.reset_step = 1
        with st.form("reset_form_step1"):
            st.markdown("##### Step 1: Enter New Password Details")
            st.text_input("Your Account Email", key="reset_email")
            st.text_input("New Password", type="password", key="new_password")
            st.text_input("Confirm New Password", type="password", key="confirm_password")
            if st.form_submit_button("Proceed to Confirmation"):
                if not all([st.session_state.reset_email, st.session_state.new_password, st.session_state.confirm_password]):
                    st.error("Please fill all fields.")
                elif st.session_state.new_password != st.session_state.confirm_password:
                    st.error("Passwords do not match.")
                else:
                    st.session_state.reset_step = 2
                    st.rerun()
        if st.session_state.reset_step == 2:
            st.markdown("---")
            with st.form("reset_form_step2"):
                st.markdown("##### Step 2: Confirm Your Identity")
                st.warning("To finalize, please enter your unique User ID.")
                user_id = st.text_input("User ID", key="reset_user_id_confirm")
                if st.form_submit_button("Confirm and Reset Password"):
                    if not user_id:
                        st.error("User ID is required to confirm.")
                    else:
                        success = reset_password(user_id, st.session_state.reset_email, st.session_state.new_password)
                        if success:
                            st.success("Password updated successfully! Please log in.")
                            for key in ['reset_step', 'reset_email', 'new_password', 'confirm_password']:
                                del st.session_state[key]
                            switch_page("login")
                        else:
                            st.error("Invalid User ID or Email. Please check your details and try again.")
        if st.button("Back to Login", use_container_width=True):
            for key in ['reset_step', 'reset_email', 'new_password', 'confirm_password']:
                if key in st.session_state:
                    del st.session_state[key]
            switch_page("login")