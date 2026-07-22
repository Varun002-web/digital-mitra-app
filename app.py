import streamlit as st
import os
import smtplib
import io
import speech_recognition as sr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image
import google.generativeai as genai

# --- INITIALIZE GEMINI AI CLIENT ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Gemini API key is missing in Streamlit secrets! Please add GEMINI_API_KEY.")

# --- SPEECH RECOGNITION ENGINE ---
def transcribe_actual_audio(audio_bytes, target_language_code):
    """Processes real microphone audio bytes and extracts spoken words using the selected regional language code."""
    recognizer = sr.Recognizer()
    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            actual_text = recognizer.recognize_google(audio_data, language=target_language_code)
            return actual_text
    except sr.UnknownValueError:
        return None
    except Exception as e:
        return None

# --- IMPROVED AI TRIAGE & RESPONSE CORE ---
def process_citizen_input(text_input, language_name):
    """
    Uses Gemini AI to evaluate citizen input:
    Returns (category, response_text)
    category: 'GRIEVANCE' or 'GENERAL_QUERY'
    """
    prompt = f"""
    You are an AI Assistant for Grameena Seva, a rural government portal in India.
    Analyze the following user input spoken in/translated from {language_name}:
    
    User Input: "{text_input}"
    
    Categorization Rules:
    - 'GENERAL_QUERY': The user is asking a question about government schemes, subsidies (e.g., tractor subsidy, PM-KISAN, seeds, fertilizers), eligibility, rules, processes, or general information.
    - 'GRIEVANCE': The user is reporting an actual operational problem, broken public utility (road, water pipe, street light), delay in official service, corruption, or requesting direct government intervention for an issue.

    Tasks:
    1. Decide if it is GENERAL_QUERY or GRIEVANCE.
    2. If GENERAL_QUERY: Provide a helpful, polite, and detailed answer explaining the scheme or answer in {language_name}.
    3. If GRIEVANCE: Provide a concise English summary of the issue for government officials.

    Output MUST follow this format exactly:
    CATEGORY: <GENERAL_QUERY or GRIEVANCE>
    RESPONSE: <Your answer in {language_name} if GENERAL_QUERY, or English summary if GRIEVANCE>
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text.strip()
        
        # Explicit check for GENERAL_QUERY
        if "CATEGORY: GENERAL_QUERY" in res_text or "GENERAL_QUERY" in res_text:
            category = "GENERAL_QUERY"
        else:
            category = "GRIEVANCE"
            
        content = res_text.split("RESPONSE:")[-1].strip() if "RESPONSE:" in res_text else res_text
        return category, content
    except Exception as e:
        # Fallback if Gemini fails
        return "GRIEVANCE", text_input

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
        "submit_btn": "🚀 Submit / Process Request"
    },
    "Hindi (हिन्दी)": {
        "name_label": "👤 पूरा नाम दर्ज करें *",
        "address_label": "🏠 गांव और पता दर्ज करें *",
        "record_label": "रिकॉर्ड दबाएं और अपनी भाषा में बोलें",
        "submit_btn": "🚀 सबमिट करें / जानकारी प्राप्त करें"
    },
    "Telugu (తెలుగు)": {
        "name_label": "👤 పూర్తి పేరు నమోదు చేయండి *",
        "address_label": "🏠 గ్రామం మరియు చిరునామా నమోదు చేయండి *",
        "record_label": "రైటు బటన్ నొక్కి మీ మాట్లాడండి",
        "submit_btn": "🚀 సమర్పించండి / సమాచారం పొందండి"
    },
    "Tamil (தமிழ்)": {
        "name_label": "👤 முழு பெயரை உள்ளிடவும் *",
        "address_label": "🏠 கிராமம் மற்றும் முகவரியை உள்ளிடவும் *",
        "record_label": "பதிவு செய்து பேசுங்கள்",
        "submit_btn": "🚀 சமர்ப்பிக்கவும்"
    },
    "Kannada (ಕನ್ನಡ)": {
        "name_label": "👤 ಪೂರ್ಣ ಹೆಸರನ್ನು ನಮೂದಿಸಿ *",
        "address_label": "🏠 ಗ್ರಾಮ ಮತ್ತು ವಿಳಾಸವನ್ನು ನಮೂದಿಸಿ *",
        "record_label": "ರೆಕಾರ್ಡ್ ಒತ್ತಿ ಮತ್ತು ಮಾತನಾಡಿ",
        "submit_btn": "🚀 ಸಲ್ಲಿಸಿ"
    },
    "Marathi (मराठी)": {
        "name_label": "👤 पूर्ण नाव प्रविष्ट करा *",
        "address_label": "🏠 गाव आणि पत्ता प्रविष्ट करा *",
        "record_label": "रेकॉर्ड दाबा आणि बोला",
        "submit_btn": "🚀 सबमिट करा"
    },
    "Bengali (বাংলা)": {
        "name_label": "👤 সম্পূর্ণ নাম লিখুন *",
        "address_label": "🏠 গ্রাম ও ঠিকানা লিখুন *",
        "record_label": "রেকর্ড চাপুন এবং বলুন",
        "submit_btn": "🚀 জমা দিন"
    },
    "Gujarati (ગુજરાતી)": {
        "name_label": "👤 પૂરું નામ દાખલ કરો *",
        "address_label": "🏠 ગામ અને સરનામું દાખલ કરો *",
        "record_label": "રેકોર્ડ દબાવો અને બોલો",
        "submit_btn": "🚀 સબમિટ કરો"
    },
    "Malayalam (മലയാളം)": {
        "name_label": "👤 പൂർണ്ണ പേര് നൽകുക *",
        "address_label": "🏠 ഗ്രാമവും മേൽവിലാസവും നൽകുക *",
        "record_label": "റെക്കോർഡ് ചെയ്ത് സംസാരിക്കുക",
        "submit_btn": "🚀 സമർപ്പിക്കുക"
    },
    "Punjabi (ਪੰਜਾਬੀ)": {
        "name_label": "👤 ਪੂਰਾ ਨਾਮ ਦਰਜ ਕਰੋ *",
        "address_label": "🏠 ਪਿੰਡ ਅਤੇ ਪਤਾ ਦਰਜ ਕਰੋ *",
        "record_label": "ਰਿਕਾਰਡ ਦਬਾਓ ਅਤੇ ਬੋਲੋ",
        "submit_btn": "🚀 ਸ਼ੁਰੂ ਕਰੋ"
    },
    "Urdu (اُردُو)": {
        "name_label": "👤 پورا نام درج کریں *",
        "address_label": "🏠 گاؤں اور پتہ درج کریں *",
        "record_label": "ریکارڈ بٹن دبائیں اور بولیں",
        "submit_btn": "🚀 جمع کریں"
    }
}

selected_ui_lang = st.selectbox("🌐 Choose your language / भाषा चुनें", list(languages_map.keys()))
lang_code = languages_map[selected_ui_lang]
labels = ui_translations.get(selected_ui_lang, ui_translations["English"])

st.write(f"App set to: **{selected_ui_lang}** (Code: `{lang_code}`)")
st.write("---")

tab1, tab2 = st.tabs(["🎙️ Talk to Mitra (Voice)", "📷 Scan Documents (OCR)"])

# --- SMTP EMAIL DISPATCH SYSTEM ---
def dispatch_grievance_email(original_lang, transcribed_text, ai_summary, citizen_name, citizen_address):
    """Transmits actionable official grievances via SMTP using Streamlit Secrets."""
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
    msg['Subject'] = f"ACTION REQUIRED: New Field Grievance - {citizen_name} ({original_lang})"
    
    body = f"""
    Respected Officer,
    
    A citizen grievance requiring official intervention has been verified and routed via Grameena Seva.
    
    --- CITIZEN IDENTITY DETAILS ---
    Name of Citizen : {citizen_name}
    Village/Address : {citizen_address}
    
    --- AI TRIAGE REPORT ---
    Original Language : {original_lang}
    Raw Transcription : {transcribed_text}
    
    AI Incident Summary:
    {ai_summary}
    
    --------------------------------------------------
    This is an automated operational dispatch. Please review and initiate resolution.
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.sidebar.error(f"Mail Server Error: {e}")
        return False

# --- TAB 1: VOICE INTERFACE WITH AI TRIAGE ---
with tab1:
    st.subheader("📝 Citizen Information Form")
    farmer_name = st.text_input(labels["name_label"])
    farmer_address = st.text_area(labels["address_label"], height=70)
    
    st.write("---")
    st.subheader("🎙️ Speak or Record Your Query / Grievance")
    audio_file = st.audio_input(labels["record_label"])
    
    if audio_file:
        st.success("Audio captured successfully!")
        audio_bytes = audio_file.read()
        
        with st.spinner(f"Transcribing voice in {selected_ui_lang}..."):
            user_text = transcribe_actual_audio(audio_bytes, lang_code)
            
        if user_text:
            st.subheader("📋 Captured Input:")
            st.info(f'"{user_text}"')
            
            # Validation Gate Check
            if farmer_name.strip() and farmer_address.strip():
                if st.button(labels["submit_btn"]):
                    with st.spinner("AI analyzing query & determining routing action..."):
                        category, result_content = process_citizen_input(user_text, selected_ui_lang)
                        
                        if category == "GENERAL_QUERY":
                            st.success("🤖 AI Mitra Assistant Answer:")
                            st.markdown(f"### 💡 Solution:\n{result_content}")
                            st.caption("ℹ️ This query was answered directly by AI as it did not require government intervention.")
                            
                        elif category == "GRIEVANCE":
                            st.warning("🚨 Official Action Required: Routing issue to government portal...")
                            email_status = dispatch_grievance_email(
                                selected_ui_lang, 
                                user_text, 
                                result_content, 
                                farmer_name, 
                                farmer_address
                            )
                            
                            if email_status:
                                st.success(f"🎉 Grievance filed successfully for {farmer_name}! Dispatch notification sent to government officials.")
                            else:
                                st.error("Submission failed. Please check your mail server credentials in Streamlit Secrets.")
            else:
                st.warning("⚠️ Action Required: Please fill out both your Name and Address fields above to enable processing.")
        else:
            st.error("Could not transcribe clear speech. Please speak clearly into the microphone.")

# --- TAB 2: DOCUMENT OCR PLACEHOLDER ---
with tab2:
    st.subheader("Upload or Snap ID / Land Records")
    uploaded_image = st.camera_input("Take a photo of Document or Land Record")
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Document", use_container_width=True)
        st.info("Extracting data via Mobile OCR Engine...")
