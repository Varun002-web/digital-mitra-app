import streamlit as st
import os
from PIL import Image
import fitz # PyMuPDF for handling PDF automation
# Placeholder for AI libraries (e.g., openai, bhashini API wrapper)

st.set_page_config(page_title="Digital Mitra", page_icon="🌾", layout="centered")

# Custom Styling to make it look like a clean mobile application
st.markdown("""
    <style>
    .big-button { font-size:24px !important; font-weight: bold; }
    .stButton>button { width: 100%; height: 60px; background-color: #E2725B; color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

## --- 1. THE USER INTERFACE ---
st.title("🌾 Digital Mitra AI Hub")
st.write("Bridging the Linguistic Gap for Rural India")
st.write("---")

# Language Selection
languages = [
    "English", "Hindi (हिन्दी)", "Bengali (বাংলা)", "Marathi (मराठी)", 
    "Telugu (తెలుగు)", "Tamil (தமிழ்)", "Gujarati (ગુજરાતી)", "Urdu (اُردُو)", 
    "Kannada (ಕನ್ನಡ)", "Odia (ଓଡ଼ିଆ)", "Malayalam (മലയാളം)", "Punjabi (ਪੰਜਾਬੀ)",
    "Assamese (অসমীয়া)", "Maithili (मैथिली)", "Santali (សន្តាលី)", "Kashmiri (کأشُر)",
    "Nepali (नेपाली)", "Konkani (कोंकणी)", "Sindhi (सिन्धी)", "Dogri (डोगरी)", 
    "Manipuri (মণিপুরী)", "Bodo (বড়ো)"]

# Tab Layout for Voice or Document Submission
tab1, tab2 = st.tabs(["🎙️ Talk to Mitra (Voice)", "📷 Scan Documents (OCR)"])

with tab1:
    st.subheader("Describe your problem or need:")
    # Streamlit audio input acts as the native microphone intake hook
    audio_file = st.audio_input("Press record and speak naturally (e.g., 'Heavy rains ruined my crops')")
    
    if audio_file:
        st.success("Audio captured successfully!")
        # Trigger Intent Classifier Pipeline
        st.info("Processing your voice context with Bhashini Voice AI...")

with tab2:
    st.subheader("Upload or Snap ID / Land Records")
    uploaded_image = st.camera_input("Take a photo of Aadhaar or Land Record Document")
    
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Document", use_container_width=True)
        st.info("Extracting data via Mobile OCR Engine...")
