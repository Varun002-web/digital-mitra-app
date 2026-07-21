import streamlit as st
import os
import smtplib
import io
import speech_recognition as sr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image

# --- SPEECH RECOGNITION ENGINE ---
def transcribe_actual_audio(audio_bytes, target_language_code):
    """Processes real microphone audio bytes and extracts spoken words using the selected regional language code."""
    recognizer = sr.Recognizer()
    
    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
            # Pass selected regional language code (e.g. 'hi-IN', 'te-IN') to Google Speech engine
            actual_text = recognizer.recognize_google(audio_data, language=target_language_code)
            return f"Grievance: {actual_text}"
            
    except sr.UnknownValueError:
        return "Grievance Status: Audio captured, but the AI could not clearly identify the spoken words. Please speak closer to your microphone."
    except sr.RequestError as e:
        return f"Speech Core Interruption: Network connection error ({e}). Please check your internet connection."
    except Exception as e:
        return f"Processing Error: Could not parse audio format. Ensure your recording contains clear voice input."

# --- SYSTEM UI CONFIGURATION ---
st.set_page_config(page_title="Grameena Seva App", page_icon="🌾", layout="centered")

st.markdown("""
    <style>
    .big-button { font-size:24px !important; font-weight: bold; }
    .stButton>button { width: 100%; height: 60px; background-color: #E2725B; color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER SECTION ---
st.title("🌾 Grameena Seva AI Hub")
st.write("Bridging the Linguistic Gap for Rural India")
st.write("---")

# Language code mapping for Indian regional languages
languages_map = {
    "English": "en-IN",
    "Hindi (हिन्दी)": "hi-IN",
    "Telugu (తెలుగు)": "te-IN",
    "Tamil (தமிழ்)": "ta-IN",
    "Kannada (ಕನ್ನಡ)": "kn-IN",
    "Marathi (मराठी)": "mr-IN",
    "Bengali (বাংলা)": "bn-IN",
    "Gujarati (ગુજરાતી)": "gu-IN",
    "Malayalam (മലയാളം)": "ml-IN",
    "Punjabi (ਪੰਜਾਬੀ)": "pa-IN",
    "Urdu (اُردُو)": "ur-IN"
}

# UI Labels Translation Dictionary
ui_translations = {
    "English": {
        "name_label": "👤 Enter Full Name *",
        "address_label": "🏠 Enter Village & Address *",
        "record_label": "Press record and speak naturally in your chosen language",
        "submit_btn": "🚀 Submit Grievance to Government Portal"
    },
    "Hindi (हिन्दी)": {
        "name_label": "👤 पूरा नाम दर्ज करें *",
        "address_label": "🏠 गांव और पता दर्ज करें *",
        "record_label": "रिकॉर्ड दबाएं और अपनी भाषा में बोलें",
        "submit_btn": "🚀 शिकायत दर्ज करें"
    },
    "Telugu (తెలుగు)": {
        "name_label": "👤 పూర్తి పేరు నమోదు చేయండి *",
        "address_label": "🏠 గ్రామం మరియు చిరునామా నమోదు చేయండి *",
        "record_label": "రైటు బటన్ నొక్కి మీ మాట్లాడండి",
        "submit_btn": "🚀 ఫిర్యాదును సమర్పించండి"
    },
    "Tamil (தமிழ்)": {
        "name_label": "👤 முழு பெயரை உள்ளிடவும் *",
        "address_label": "🏠 கிராமம் மற்றும் முகவரியை உள்ளிடவும் *",
        "record_label": "பதிவு செய்து பேசுங்கள்",
        "submit_btn": "🚀 புகாரைச் சமர்ப்பிக்கவும்"
    },
    "Kannada (ಕನ್ನಡ)": {
        "name_label": "👤 ಪೂರ್ಣ ಹೆಸರನ್ನು ನಮೂದಿಸಿ *",
        "address_label": "🏠 ಗ್ರಾಮ ಮತ್ತು ವಿಳಾಸವನ್ನು ನಮೂದಿಸಿ *",
        "record_label": "ರೆಕಾರ್ಡ್ ಒತ್ತಿ ಮತ್ತು ಮಾತನಾಡಿ",
        "submit_btn": "🚀 ದೂರು ಸಲ್ಲಿಸಿ"
    },
    "Marathi (मराठी)": {
        "name_label": "👤 पूर्ण नाव प्रविष्ट करा *",
        "address_label": "🏠 गाव आणि पत्ता प्रविष्ट करा *",
        "record_label": "रेकॉर्ड दाबा आणि बोला",
        "submit_btn": "🚀 तक्रार नोंदवा"
    },
    "Bengali (বাংলা)": {
        "name_label": "👤 সম্পূর্ণ নাম লিখুন *",
        "address_label": "🏠 গ্রাম ও ঠিকানা লিখুন *",
        "record_label": "রেকর্ড চাপুন এবং বলুন",
        "submit_btn": "🚀 অভিযোগ জমা দিন"
    },
    "Gujarati (ગુજરાતી)": {
        "name_label": "👤 પૂરું નામ દાખલ કરો *",
        "address_label": "🏠 ગામ અને સરનામું દાખલ કરો *",
        "record_label": "રેકોર્ડ દબાવો અને બોલો",
        "submit_btn": "🚀 ફરિયાદ સબમિટ કરો"
    },
    "Malayalam (മലയാളം)": {
        "name_label": "👤 പൂർണ്ണ പേര് നൽകുക *",
        "address_label": "🏠 ഗ്രാമവും മേൽവിലാസവും നൽകുക *",
        "record_label": "റെക്കോർഡ് ചെയ്ത് സംസാരിക്കുക",
        "submit_btn": "🚀 പരാതി സമർപ്പിക്കുക"
    },
    "Punjabi (ਪੰਜਾਬੀ)": {
        "name_label": "👤 ਪੂਰਾ ਨਾਮ ਦਰਜ ਕਰੋ *",
        "address_label": "🏠 ਪਿੰਡ ਅਤੇ ਪਤਾ ਦਰਜ ਕਰੋ *",
        "record_label": "ਰਿਕਾਰਡ ਦਬਾਓ ਅਤੇ ਬੋਲੋ",
        "submit_btn": "🚀 ਸ਼ਿਕਾਇਤ ਦਰਜ ਕਰੋ"
    },
    "Urdu (اُردُو)": {
        "name_label": "👤 پورا نام درج کریں *",
        "address_label": "🏠 گاؤں اور پتہ درج کریں *",
        "record_label": "ریکارڈ بٹن دبائیں اور بولیں",
        "submit_btn": "🚀 شکایت درج کریں"
    }
}

selected_ui_lang = st.selectbox("🌐 Choose your language / भाषा चुनें", list(languages_map.keys()))
lang_code = languages_map[selected_ui_lang]

# Fetch the dynamic labels for the active language selection
labels = ui_translations.get(selected_ui_lang, ui_translations["English"])

st.write(f"App set to: **{selected_ui_lang}** (Code: `{lang_code}`)")
st.write("---")

tab1, tab2 = st.tabs(["🎙️ Talk to Mitra (Voice)", "📷 Scan Documents (OCR)"])

# --- SMTP EMAIL DISPATCH SYSTEM ---
def dispatch_grievance_email(original_lang, transcribed_text, citizen_name, citizen_address):
    """Securely transmits the grievance and citizen profile via SMTP using Streamlit Secrets."""
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
    
    --- FIELD REPORT ---
    Language Selected: {original_lang}
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

# --- TAB 1: VOICE GRIEVANCE FORM ---
with tab1:
    st.subheader("📝 Citizen Information Form")
    
    # Dynamic language input labels
    farmer_name = st.text_input(labels["name_label"])
    farmer_address = st.text_area(labels["address_label"], height=70)
    
    st.write("---")
    st.subheader("🎙️ Record Your Grievance")
    audio_file = st.audio_input(labels["record_label"])
    
    if audio_file:
        st.success("Audio captured successfully!")
        
        audio_bytes = audio_file.read()
        st.info(f"Processing voice input in {selected_ui_lang}...")
        
        # Transcribe audio using the selected language code
        translated_text = transcribe_actual_audio(audio_bytes, lang_code)
        
        st.subheader("📋 Output Verification:")
        st.text_area(label="", value=translated_text, height=120)
        
        # Validation Gate Check
        if farmer_name.strip() and farmer_address.strip():
            if st.button(labels["submit_btn"]):
                with st.spinner("Routing alert to the official department..."):
                    email_status = dispatch_grievance_email(
                        selected_ui_lang, 
                        translated_text, 
                        farmer_name, 
                        farmer_address
                    )
                    
                    if email_status:
                        st.success(f"🎉 Grievance filed for {farmer_name}! Sent to the government official.")
                    else:
                        st.error("Submission failed. Check system credentials.")
        else:
            st.warning("⚠️ Action Required: Please fill out both your Name and Address fields above to unlock the Submit button.")

# --- TAB 2: DOCUMENT OCR PLACEHOLDER ---
with tab2:
    st.subheader("Upload or Snap ID / Land Records")
    uploaded_image = st.camera_input("Take a photo of Document or Land Record")
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Document", use_container_width=True)
        st.info("Extracting data via Mobile OCR Engine...")
