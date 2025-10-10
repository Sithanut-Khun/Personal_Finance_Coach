import streamlit as st
import time
from datetime import datetime, timedelta
from src.expense_manager import get_expenses_as_df 

KHR_TO_USD = 4050

def get_user_chat_key(user_id):
    """Generate a unique session state key for each user's chat history"""
    return f"messages_{user_id}"


def get_last_month_expenses(user_id):
    """Get user's expenses from last month with currency conversion"""
    today = datetime.now()
    first_of_month = today.replace(day=1)
    last_month_end = first_of_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    
    df = get_expenses_as_df(user_id, last_month_start, last_month_end)
    if df.empty:
        return 0
        
    # Convert all amounts to USD for consistency
    def convert_amount(row):
        if row['currency'] == 'KHR':
            return row['amount'] / KHR_TO_USD
        return row['amount']
    
    df['converted_amount'] = df.apply(convert_amount, axis=1)
    return df['converted_amount'].sum()



def show_chatbot_page():
    """
    Displays the chatbot interface.
    """
    
    if not st.session_state.user_id:
        st.warning("Please log in to use the chatbot.")
        return
    
    st.header("🤖 Financial Coach Chatbot")
    st.markdown("Ask me anything about your spending habits!")

    # --- (Your existing CSS code remains unchanged here) ---
    st.markdown("""
        <style>
            .chat-container {
                display: flex;
                flex-direction: column-reverse;
                gap: 15px;
                padding: 10px;
                overflow-y: auto;
                height: 60vh; 
                border: 1px solid #2d2d2d;
                border-radius: 10px;
                background-color: #1a1a1a;
            }
            .chat-bubble {
                padding: 10px 15px;
                border-radius: 20px;
                max-width: 70%;
                word-wrap: break-word;
            }
            .user-bubble {
                background-color: #0078D4;
                color: white;
                align-self: flex-end;
                border-bottom-right-radius: 5px;
            }
            .bot-bubble {
                background-color: #333333;
                color: white;
                align-self: flex-start;
                border-bottom-left-radius: 5px;
            }
        </style>
    """, unsafe_allow_html=True)
    
     # Initialize user-specific chat history
    chat_key = get_user_chat_key(st.session_state.user_id)
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {"role": "assistant", "content": f"Hi {st.session_state.username}! I'm your personal financial coach. How can I help you analyze your spending today?"}
        ]
        
    # Display chat history
    chat_history_html = '<div class="chat-container">'
    for message in reversed(st.session_state[chat_key]):
        bubble_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
        chat_history_html += f'<div class="chat-bubble {bubble_class}">{message["content"]}</div>'
    chat_history_html += '</div>'
    st.markdown(chat_history_html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Suggestions")
    s_col1, s_col2, s_col3 = st.columns(3)

    # --- We will now tie the buttons to the chat logic ---
    if s_col1.button("How much did I spend last month?"):
        st.session_state.prompt_from_button = "How much did I spend last month?"
        st.rerun()
    if s_col2.button("What are my top 5 merchants?"):
        st.session_state.prompt_from_button = "What are my top 5 merchants?"
        st.rerun()
    if s_col3.button("Compare spending: May vs June"):
        st.session_state.prompt_from_button = "Compare spending: May vs June"
        st.rerun()

    # Get input from chat box or from the suggestion buttons
    prompt = st.chat_input("What would you like to know?")
    if "prompt_from_button" in st.session_state and st.session_state.prompt_from_button:
        prompt = st.session_state.prompt_from_button
        st.session_state.prompt_from_button = None # Reset after use

    if prompt:
        # Add user message to chat history
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        
        with st.spinner("Analyzing..."):
            time.sleep(3)
        
        # Bot response logic
        prompt_lower = prompt.lower()
        bot_response = ""

        try:
            if "hello" in prompt_lower or "hi" in prompt_lower:
                bot_response = f"Hello {st.session_state.username}! How can I help you with your finances today?"

            elif "how much" in prompt_lower and "last month" in prompt_lower:
                last_month_total = get_last_month_expenses(st.session_state.user_id)
                bot_response = (
                    f"Last month, you spent **${last_month_total:,.2f}** "
                    f"(converted to USD for consistency)."
                )

            elif "top" in prompt_lower and ("merchant" in prompt_lower or "stores" in prompt_lower):
                df = get_expenses_as_df(st.session_state.user_id, 
                                     (datetime.now() - timedelta(days=30)).date(),
                                     datetime.now().date())
                
                # Convert amounts to USD
                df['converted_amount'] = df.apply(
                    lambda x: x['amount'] / KHR_TO_USD if x['currency'] == 'KHR' else x['amount'], 
                    axis=1
                )
                
                top_merchants = df.groupby('merchant_name')['converted_amount'].sum().nlargest(5)
                
                bot_response = "Here are your top 5 merchants by spending (in USD):\n"
                for i, (merchant, amount) in enumerate(top_merchants.items(), 1):
                    bot_response += f"{i}. {merchant}: ${amount:,.2f}\n"
            elif "compare" in prompt_lower and ("may" in prompt_lower or "june" in prompt_lower):
                # Implement actual comparison logic here
                bot_response = "I'll help you compare those months. Feature coming soon!"

            elif "thank" in prompt_lower:
                bot_response = "You're welcome! Is there anything else you'd like to know about your finances?"

            else:
                bot_response = "I'm not sure about that. I can help you with:\n" + \
                             "- Spending analysis\n" + \
                             "- Top merchants\n" + \
                             "- Monthly comparisons"

        except Exception as e:
            bot_response = "I encountered an error while analyzing your data. Please try again."
            st.error(f"Error: {str(e)}")

        # Add bot response to chat history
        st.session_state[chat_key].append({"role": "assistant", "content": bot_response})
        st.rerun()