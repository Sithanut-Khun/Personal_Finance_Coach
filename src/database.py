# src/database.py
import streamlit as st
import psycopg2
import toml
from sqlalchemy import create_engine

# Load DB config from secrets.toml
DB_CONFIG = toml.load(".streamlit/secrets.toml")['database']

@st.cache_resource
def get_db_engine():
    """Creates a cached SQLAlchemy engine."""
    db_uri = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        "?sslmode=require"
    )
    return create_engine(
        db_uri,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True
    )

def get_connection():
    """Establishes a new psycopg2 connection."""
    return psycopg2.connect(
        **DB_CONFIG,
        sslmode="require"
    )