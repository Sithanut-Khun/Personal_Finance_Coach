# src/ui/profile_page.py
import streamlit as st
from src.auth import update_username
from src.database import get_connection

def _show_update_username_form(cookies):
    new_username = st.text_input("New Username", value=st.session_state.username, max_chars=30)
    if st.button("✅ Save Changes"):
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

def _show_user_details():
    st.markdown("---")
    st.subheader("My Details")
    if 'show_details' not in st.session_state:
        st.session_state.show_details = False

    if st.session_state.show_details:
        if 'created_at' not in st.session_state:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT created_at FROM users WHERE user_id = %s", (st.session_state.user_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            st.session_state.created_at = result[0].strftime("%d-%m-%Y") if result else "N/A"
        
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

def show_profile_page(cookies):
    """Main function to render the user profile page."""
    st.markdown("## 👤 User Profile Settings")
    
    if st.session_state.get("show_update_username_form", False):
        _show_update_username_form(cookies)
        if st.button("Cancel"):
            st.session_state.show_update_username_form = False
            st.rerun()
    else:
        st.button("✏️ Update Username", on_click=lambda: st.session_state.update({"show_update_username_form": True}))
    
    _show_user_details()