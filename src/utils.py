# src/utils.py
import streamlit as st

def switch_page(page_name: str):
    """Switches the 'auth_page' in session state and reruns."""
    st.session_state.auth_page = page_name
    st.rerun()

# --- CONSTANTS ---
CATEGORIES_DATA = {
    "Dining": ["Eatary Meals", "Restaurant Meals", "Snacks", "Drinks", "Fast Food"],
    "Transportation": ["Ride-Hailing", "Tuk-Tuk/Moto-Dop", "Fuel", "Public Transport", "Parking Fees"],
    "Education": ["Tuition Fees", "Books & Supplies", "Online Courses", "Workshops/Seminars"],
    "Housing & Utilities": ["Rent", "Electricity Bill", "Water Bill", "Internet Bill", "Home Supplies"],
    "Food & Groceries": ["Meat", "Vegetables", "Fruits", "Staples", "Snacks & Beverages", "Fish & Seafood", "Condiments & Spices", "Dairy Products", "Canned & Packaged Foods"],
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
PAYMENT_METHODS = ["Cash", "Mobile Pay", "Credit Card", "Debit Card", "Other"]
CURRENCY_OPTIONS = ["USD", "KHR"]