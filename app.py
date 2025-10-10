# app.py
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

# Import UI pages
from src.ui.auth_pages import show_login_page, show_signup_page, show_reset_page
from src.ui.profile_page import show_profile_page
from src.ui.expense_page import show_expense_page
from src.expense_manager import get_expenses_as_df
from src.ui.dashboard_page import show_dashboard_page
from src.ui.chatbot_page import show_chatbot_page

# --- COOKIE SETUP ---
cookie_secret = st.secrets["cookie"]["secret"]
cookies = EncryptedCookieManager(prefix="myapp_", password=cookie_secret)
if not cookies.ready():
    st.stop()

# --- PAGE ROUTER & MAIN APP ---
def set_active_tab(tab_name):
    st.session_state.active_tab = tab_name

def main():
    st.set_page_config(page_title="Smart Expense Tracker", layout="wide")
    
    # Initialize session state
    if "auth_page" not in st.session_state: st.session_state.auth_page = "login"
    if "user_id" not in st.session_state: st.session_state.user_id = None
    if "active_tab" not in st.session_state: st.session_state.active_tab = "Expense"

    # Restore session from cookies if needed
    if not st.session_state.user_id and cookies.get("user_id"):
        st.session_state.user_id = cookies.get("user_id")
        st.session_state.email = cookies.get("email")
        st.session_state.username = cookies.get("username")

    # --- AUTHENTICATION FLOW ---
    if not st.session_state.user_id:
        page_map = {
            "login": lambda: show_login_page(cookies),
            "signup": show_signup_page,
            "reset": show_reset_page,
        }
        page_map[st.session_state.auth_page]()
        return

    # --- LOGGED-IN VIEW ---
    st.title("💰 Smart Expense Tracker")

    with st.sidebar:
        # st.success(f"Welcome {st.session_state.username}!", icon="👋")
        st.markdown(
            f"""
            <div style='display: flex; justify-content: center; margin-bottom: 1rem;'>
                <div style='background-color: rgb(14, 184, 2); padding: 0.5rem 1rem; 
                     border-radius: 0.5rem; text-align: center; width: 100%;'>
                    <p style='color: white; margin: 0;'>
                        Welcome {st.session_state.username}! 👋
                    </p>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.markdown("---")
        
        tabs = ["Expense", "Dashboard", "Chatbot", "User Profile"]
        for tab in tabs:
            st.button(
                tab,
                use_container_width=True,
                type="primary" if st.session_state.active_tab == tab else "secondary",
                on_click=set_active_tab,
                args=(tab,)
            )

        st.markdown("<div style='height: 30vh;'></div>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            cookies["user_id"] = ""
            cookies["email"] = ""
            cookies["username"] = ""
            cookies.save()
            # st.session_state.clear() # Clear all session state
            # get_expenses_as_df.clear() # Clear data cache
            # st.rerun()
            
            # clear only auth-related session state keys (avoid clearing internal cookie manager state)
            for k in ["user_id", "email", "username", "auth_page", "active_tab"]:
                if k in st.session_state:
                    del st.session_state[k]

            # clear cached data that depends on user session
            try:
                get_expenses_as_df.clear()
            except Exception:
                pass

            # force a rerun to return to the login page
            st.rerun()

    # --- RENDER ACTIVE TAB ---
    if st.session_state.active_tab == "Expense":
        show_expense_page()
    elif st.session_state.active_tab == "Dashboard":
        # st.markdown("## 📈 Dashboard (Coming Soon...)")
        show_dashboard_page()
    elif st.session_state.active_tab == "Chatbot":
        # st.markdown("## 🤖 Chatbot (Coming Soon...)")
        show_chatbot_page()
    elif st.session_state.active_tab == "User Profile":
        show_profile_page(cookies)

if __name__ == "__main__":
    main()