import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from PIL import Image

# Dynamic translator helper that varies the output text depending on chosen language
class MockBhashiniTranslator:
    def __init__(self, source_lang, target_lang):
        self.source = source_lang
        self.target = target_lang
        
    def asr_nmt(self, audio_base64):
        # Dynamically alters the simulated transcription depending on the source language dialect
        if "tel" in self.source:
            return "Grievance: The borewell pump in our village has been damaged for 4 days, leaving 30 families without drinking water. Please repair it immediately."
        elif "hin" in self.source:
            return "Grievance: The local fertilizer distribution center is refusing to supply urea at the government subsidized rate, charging extra overhead fees."
        elif "kan" in self.source:
            return "Grievance: Stray cattle have broken through the primary wire fence and completely ruined our ripening ragi crops overnight."
        else:
            return "Grievance: Power fluctuations are destroying our agricultural motors. We request stable electricity during daytime hours."

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
    "English": "eng_Latn", "Hindi (हिन्दी)": "hin_Deva", "Bengali (বাংলা)": "ben_Beng",
    "Marathi (मराठी)": "mar_Deva", "Telugu (తెలుగు)": "tel_Telu", "Tamil (தமிழ்)": "tam_Taml",
    "Gujarati (ગુજરાતી)": "guj_Gujr", "Urdu (اُردُو)": "urd_Arab", "Kannada (ಕನ್ನಡ)": "kan_Knda",
    "Odia (ଓଡ଼ିଆ)": "ory_Orya", "Malayalam (മലയാളം)": "mal_Mlym", "Punjabi (ਪੰਜਾਬੀ)": "pan_Guru",
    "Assamese (অસમীয়া)": "asm_Asme", "Maithili (मैथिली)": "mai_Deva", "Santali (সន្តាលী)": "sat_Olch",
    "Kashmiri (کأشُر)": "kas_Arab", "Nepali (नेपाली)": "nep_Deva", "Konkani (कोंकणी)": "kok_Deva",
    "Sindhi (सिन्धी)": "snd_Arab", "Dogri (डोगरी)": "doi_Deva", "Manipuri (মণিপুরী)": "mni_Beng",
    "Bodo (বড়ो)": "brx_Deva"
}

selected_ui_lang = st.selectbox("🌐 Choose your language / भाषा चुनें", list(languages_map.keys()))
source_lang_code = languages_map[selected_ui_lang]
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
        st.sidebar.error(f"Secrets configuration error: {e}")
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
    # Mandatory text entry fields
    farmer_name = st.text_input("👤 Enter Full Name / पूरा नाम दर्ज करें *")
    farmer_address = st.text_area("🏠 Enter Village & Address / गांव और पता दर्ज करें *", height=70)
    
    st.write("---")
    st.subheader("🎙️ Record Your Grievance")
    audio_file = st.audio_input("Press record and speak naturally (e.g., 'Heavy rains ruined my crops')")
    
    if audio_file:
        st.success("Audio captured successfully!")
        
        audio_bytes = audio_file.read()
        base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
        
        st.info("Processing voice input via Bhashini Translation Core...")
        translator = MockBhashiniTranslator(source_lang=source_lang_code, target_lang="eng_Latn")
        translated_english_text = translator.asr_nmt(base64_audio)
        
        st.subheader("📋 English Translation Output for Verification:")
        st.text_area(label="", value=translated_english_text, height=120)
        
        # Validation gate logic check: True only if name, address, and audio exist
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
                        st.error("Submission failed at the gateway layer. Please check server status.")
        else:
            # Notice displayed warning the user to enter data before proceeding
            st.warning("⚠️ Action Required: Please fill out both your Name and Address fields above to unlock the Submit button.")

with tab2:
    st.subheader("Upload or Snap ID / Land Records")
    uploaded_image = st.camera_input("Take a photo of Document or Land Record")
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Document", use_container_width=True)
        st.info("Extracting data via Mobile OCR Engine...")
