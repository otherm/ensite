# app.py
import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access environment variables
api_key = os.getenv('GOOGLE_MAPS_API_KEY')

#st.title('Hello World')
#st.write(f'API Key: {api_key}')
print(api_key)