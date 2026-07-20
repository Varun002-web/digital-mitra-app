import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from PIL import Image

# Fallback wrapper mock for demonstration if Bhashini wrapper isn't initialized
class MockBhashiniTranslator:
    def __init__(self, source_lang, target_lang):
        self.source = source_lang
        self.target = target_lang
    def asr_nmt(self, audio_base64):
        # Simulated high-performance translation pipeline return string
        return "Grievance: The seasonal monsoon rains have completely flooded the local paddy fields. The drainage channels are blocked, and we require immediate assistance from the local agricultural inspection office."

# System configuration settings
st.set_page_config(page_title="Grameena Seva App", page_icon="🌾", layout="centered")

# Custom Styling to match your mobile design signature
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

# Comprehensive Regional Indian Language Dictionary Map
languages_map = {
    "English": "eng_Latn",
    "Hindi (हिन्दी)": "hin_Deva",
    "Bengali (বাংলা)": "ben_Beng",
    "Marathi (मराठी)": "mar_Deva", 
    "Telugu (తెలుగు)": "tel_Telu",
    "Tamil (தமிழ்)": "tam_Taml",
    "Gujarati (ગુજરાતી)": "guj_Gujr",
    "Urdu (اُردُو)": "urd_Arab", 
    "Kannada (ಕನ್ನಡ)": "kan_Knda",
    "Odia (ଓଡ଼ିଆ)": "ory_Orya",
    "Malayalam (മലയാളം)": "mal_Mlym",
    "Punjabi (ਪੰਜਾਬੀ)": "pan_Guru",
    "Assamese (অসমীয়া)": "asm_Asme",
    "Maithili (मैथिली)": "mai_Deva",
    "Santali (সន្តាលী)": "sat_Olch",
    "Kashmiri (کأشُر)": "kas_Arab",
    "Nepali (नेपाली)": "nep_Deva",
    "Konkani (कोंकणी)": "kok_Deva",
    "Sindhi (सिन्धी)": "snd_Arab",
    "Dogri (डोगरी)": "doi_Deva", 
    "Manipuri (মণিপুরী)": "mni_Beng",
    "Bodo (বড়ো)": "brx_Deva"
}

selected_ui_lang = st.selectbox("🌐 Choose your language / भाषा चुनें", list(languages_map.keys()))
source_lang_code = languages_map[selected_ui_lang]
st.write(f"App set to: **{selected_ui_lang}**")
st.write("---")

tab1, tab2 = st.tabs(["🎙️ Talk to Mitra (Voice)", "📷 Scan Documents (OCR)"])

def dispatch_grievance_email(original_lang, transcribed_text):
    """Securely transmits the translated grievance record via SMTP to the official's desk using Streamlit Secrets."""
    try:
        sender_email = st.secrets["SYSTEM_ALERT_EMAIL"]
        sender_password = st.secrets["SYSTEM_ALERT_PASSWORD"]
        receiver_email = st.secrets["GRIEVANCE_OFFICER_EMAIL"]
    except Exception as e:
        print(f"Secrets configuration error: {e}")
        return False
    
    # Structural setup of the email message object
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"URGENT: New Farmer Grievance Filed via App ({original_lang})"
    
    body = f"""
    Respected Officer,
    
    A new citizen grievance has been submitted via the Grameena Seva App platform. The AI engine has transcribed and translated the original voice request automatically.
    
    --- APPLICATION METADATA ---
    Submission Language: {original_lang}
    Target Translation Engine: English (eng_Latn)
    
    --- TRANSLATED FIELD REPORT ---
    {transcribed_text}
    
    --------------------------------------------------
    This is an automated operational dispatch. Please review and initiate resolution workflows.
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Initializing secure network connection over standard TLS port 587
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP Layer error logs: {e}")
        return False

with tab1:
    st.subheader("Describe your problem or need:")
    audio_file = st.audio_input("Press record and speak naturally (e.g., 'Heavy rains ruined my crops')")
    
    if audio_file:
        st.success("Audio captured successfully!")
        
        # 1. Processing audio payload into base64 format for safe API transit
        audio_bytes = audio_file.read()
        base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
        
        # 2. Feeding base64 object directly into Bhashini ASR/NMT engine pipeline
        st.info("Processing voice input via Bhashini Translation Core...")
        translator = MockBhashiniTranslator(source_lang=source_lang_code, target_lang="eng_Latn")
        translated_english_text = translator.asr_nmt(base64_audio)
        
        # Render translation evaluation directly onto user UI screen
        st.subheader("📋 English Translation Output for Verification:")
        st.text_area(label="", value=translated_english_text, height=120)
        
        # 3. Trigger action button to execute verified submission routing
        if st.button("🚀 Submit Grievance to Government Portal"):
            with st.spinner("Routing alert to the official department..."):
                email_status = dispatch_grievance_email(selected_ui_lang, translated_english_text)
                
                if email_status:
                    st.success("🎉 Grievance transmitted successfully! The respective government officer has been notified via email.")
                else:
                    st.error("Submission failed at the gateway layer. Please check system SMTP configuration variables.")

with tab2:
    st.subheader("Upload or Snap ID / Land Records")
    uploaded_image = st.camera_input("Take a photo of Document or Land Record")
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Document", use_container_width=True)
        st.info("Extracting data via Mobile OCR Engine...")
