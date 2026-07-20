import streamlit as st
import os
import smtplib
import io
import speech_recognition as sr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image

def transcribe_actual_audio(audio_bytes):
    """Processes real microphone audio bytes and extracts the exact spoken words using Speech AI."""
    recognizer = sr.Recognizer()
    
    try:
        # Convert raw audio bytes into an in-memory file object that the AI engine can read
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            # Calibrate for ambient noise baseline
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
            # Execute standard Speech-to-Text inference
            actual_text = recognizer.recognize_google(audio_data)
            return f"Grievance: {actual_text}"
            
    except sr.UnknownValueError:
        return "Grievance Status: Audio captured, but the AI could not clearly identify the spoken words. Please speak closer to your microphone."
    except sr.RequestError as e:
        return f"Speech Core Interruption: Network connection error ({e}). Please try again."
    except Exception as e:
        return f"Processing Error: Could not parse audio format. Ensure your recording contains clear voice input."

# System configuration settings
st.set_page_config(page_title="Grameena Seva App", page_icon="🌾", layout="centered")

st.markdown("""
    <style>
    .big-button { font-size:24px !important; font-weight: bold; }
    .stButton>button { width: 100%; height: 60px; background-color: #E2725B; color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

## --- USER INTERFACE HEADERS ---
st.title("🌾 Grameena Seva AI Hub")
st.write("Bridging the Linguistic Gap for Rural India")
st.write("---")

languages_map = {
    "English": "en-IN", "Hindi (हिन्दी)": "hi-IN", "Telugu (తెలుగు)": "te-IN",
    "Tamil (தமிழ்)": "ta-IN", "Kannada (ಕನ್ನಡ)": "kn-IN", "Marathi (मराठी)": "mr-IN"
}

selected_ui_lang = st.selectbox("🌐 Choose your language / भाषा चुनें", list(languages_map.keys()))
st.write(f"App set to: **{selected_ui_lang}**")
st.write("---")

tab1, tab2 = st.tabs(["🎙️ Talk to Mitra (Voice)", "📷 Scan Documents (OCR)"])

def dispatch_grievance_email(original_lang, transcribed_text, citizen_name, citizen_address):
    """Securely transmits the dynamic grievance and citizen profile via SMTP using Streamlit Secrets."""
    try:
        sender_email = st.secrets["SYSTEM_ALERT_EMAIL"]
        sender_password = st.secrets["SYSTEM_ALERT_PASSWORD"]
        receiver_email = st.secrets["GRIEVANCE_OFFICER_EMAIL"]
    except Exception as e:
        st.sidebar.error(f"Secrets missing: {e}")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"URGENT: New Grievance Filed by {citizen_name} ({original_lang})"
    
    body = f"""
    Respected Officer,
    
    A new citizen grievance has been submitted via the Grameena Seva App platform.
    
    --- CITIZEN IDENTITY DETAILS ---
    Name of Citizen : {citizen_name}
    Village/Address : {citizen_address}
    
    --- TRANSLATED FIELD REPORT ---
    {transcribed_text}
    
    --------------------------------------------------
    This is an automated operational dispatch. Please review and initiate resolution workflows.
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return True
    except Exception as e:
        st.sidebar.error(f"Mail Server Error: {e}")
        return False

with tab1:
    st.subheader("📝 Citizen Information Form")
    farmer_name = st.text_input("👤 Enter Full Name / पूरा नाम दर्ज करें *")
    farmer_address = st.text_area("🏠 Enter Village & Address / गांव और पता दर्ज करें *", height=70)
    
    st.write("---")
    st.subheader("🎙️ Record Your Grievance")
    audio_file = st.audio_input("Press record and speak naturally (e.g., 'Heavy rains ruined my crops')")
    
    if audio_file:
        st.success("Audio captured successfully!")
        
        audio_bytes = audio_file.read()
        st.info("Converting spoken audio into text data...")
        
        # Pass raw audio into the engine for live translation text matching
        translated_english_text = transcribe_actual_audio(audio_bytes)
        
        st.subheader("📋 Verification Output:")
        st.text_area(label="", value=translated_english_text, height=120)
        
        # Validation Gate Check
        if farmer_name.strip() and farmer_address.strip():
            if st.button("🚀 Submit Grievance to Government Portal"):
                with st.spinner("Routing alert to the official department..."):
                    email_status = dispatch_grievance_email(
                        selected_ui_lang, 
                        translated_english_text, 
                        farmer_name, 
                        farmer_address
                    )
                    
                    if email_status:
                        st.success(f"🎉 Grievance filed for {farmer_name}! Sent to the government official.")
                    else:
                        st.error("Submission failed. Check system credentials.")
        else:
            st.warning("⚠️ Action Required: Please fill out both your Name and Address fields above to unlock the Submit button.")

with tab2:
    st.subheader("Upload or Snap ID / Land Records")
    uploaded_image = st.camera_input("Take a photo of Document or Land Record")
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Document", use_container_width=True)
        st.info("Extracting data via Mobile OCR Engine...")
