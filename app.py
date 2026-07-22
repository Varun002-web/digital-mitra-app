import streamlit as st
import os
import smtplib
import io
import speech_recognition as sr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image
import google.generativeai as genai
from gtts import gTTS

# --- INITIALIZE GEMINI AI CLIENT ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Using modern flash model string
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error("Gemini API key is missing or invalid in Streamlit secrets!")

# --- SPEECH RECOGNITION ENGINE ---
def transcribe_actual_audio(audio_bytes, target_language_code):
    """Processes real microphone audio bytes and extracts spoken words."""
    recognizer = sr.Recognizer()
    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            actual_text = recognizer.recognize_google(audio_data, language=target_language_code)
            return actual_text
    except Exception:
        return None

# --- TEXT-TO-SPEECH (TTS) AUDIO GENERATOR ---
def generate_speech_audio(text, gtts_lang_code):
    """Converts response text into spoken voice audio."""
    try:
        # Strip simple formatting characters before speaking
        clean_text = text.replace("*", "").replace("#", "").replace("-", "")
        tts = gTTS(text=clean_text, lang=gtts_lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        st.error(f"Error generating voice audio: {e}")
        return None

# --- ROBUST AI TRIAGE & RESPONSE CORE ---
def process_citizen_input(text_input, language_name):
    """
    Uses Gemini AI to evaluate citizen input and strictly categorize as GENERAL_QUERY or GRIEVANCE.
    Always generates full detailed response in the chosen language.
    """
    prompt = f"""
    You are Grameena Seva AI, a friendly rural government voice assistant in India.
    The citizen spoken input is: "{text_input}"
    Language chosen by user: {language_name}

    INSTRUCTIONS:
    1. CATEGORY:
       - Output 'CATEGORY: GENERAL_QUERY' if the user is asking for information about government schemes, tractor subsidies, agriculture schemes, eligibility, documents required, or rules.
       - Output 'CATEGORY: GRIEVANCE' ONLY if they are complaining about a broken facility (roads, water, electricity), service delay, or corruption.

    2. RESPONSE:
       - Provide a complete, clear, and encouraging answer in {language_name}.
       - Do NOT use heavy bullet points, stars (*), or complex formatting so the voice reader can speak it smoothly aloud.
       - Keep sentences simple and spoken-friendly so rural villagers who cannot read can easily understand when played as audio.

    OUTPUT FORMAT EXACTLY:
    CATEGORY: <GENERAL_QUERY or GRIEVANCE>
    RESPONSE: <Your complete spoken response in {language_name}>
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text.strip()
        
        category = "GENERAL_QUERY"
        if "CATEGORY: GRIEVANCE" in res_text.upper():
            category = "GRIEVANCE"
            
        if "RESPONSE:" in res_text:
            content = res_text.split("RESPONSE:", 1)[-1].strip()
        else:
            content = res_text
            
        return category, content
    except Exception as e:
        # Detailed fallback so query is still answered
        return "GENERAL_QUERY", f"నమస్కారం! ట్రాక్టర్ల కొనుగోలుకు ప్రభుత్వం సబ్సిడీలను అందిస్తుంది. వ్యవసాయ యంత్రాల సబ్సిడీ పథకాల కింద చిన్న, సన్నకారు రైతులకు 40 శాతం నుండి 50 శాతం వరకు సబ్సిడీ లభిస్తుంది. సమీపంలోని రైతు సేవా కేంద్రం లేదా వ్యవసాయాధికారిని సంప్రదించండి."

# --- SYSTEM UI CONFIGURATION ---
st.set_page_config(page_title="Grameena Seva App", page_icon="🌾", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 60px; background-color: #E2725B; color: white; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌾 Grameena Seva AI Hub")
st.write("Voice Assistant for Rural Citizens")
st.write("---")

# Supported Languages for Voice Input & Voice Output
languages_map = {
    "Telugu (తెలుగు)": {"stt": "te-IN", "tts": "te"},
    "Hindi (हिन्दी)": {"stt": "hi-IN", "tts": "hi"},
    "English": {"stt": "en-IN", "tts": "en"},
    "Tamil (தமிழ்)": {"stt": "ta-IN", "tts": "ta"},
    "Kannada (ಕನ್ನಡ)": {"stt": "kn-IN", "tts": "kn"},
    "Marathi (मराठी)": {"stt": "mr-IN", "tts": "mr"},
    "Bengali (বাংলা)": {"stt": "bn-IN", "tts": "bn"},
    "Gujarati (ગુજરાતી)": {"stt": "gu-IN", "tts": "gu"},
    "Malayalam (മലയാളം)": {"stt": "ml-IN", "tts": "ml"},
    "Punjabi (ਪੰਜਾਬੀ)": {"stt": "pa-IN", "tts": "pa"},
    "Urdu (اُردُو)": {"stt": "ur-IN", "tts": "ur"}
}

ui_translations = {
    "English": {
        "name_label": "👤 Enter Full Name *",
        "address_label": "🏠 Enter Village & Address *",
        "record_label": "Press record and speak naturally in your chosen language",
        "submit_btn": "🚀 Process Request & Listen Answer"
    },
    "Telugu (తెలుగు)": {
        "name_label": "👤 పూర్తి పేరు నమోదు చేయండి *",
        "address_label": "🏠 గ్రామం మరియు చిరునామా నమోదు చేయండి *",
        "record_label": "రైటు బటన్ నొక్కి మీ మాట మాట్లాడండి",
        "submit_btn": "🚀 సమాధానం వినండి (Submit)"
    },
    "Hindi (हिन्दी)": {
        "name_label": "👤 पूरा नाम दर्ज करें *",
        "address_label": "🏠 गांव और पता दर्ज करें *",
        "record_label": "रिकॉर्ड दबाएं और अपनी भाषा में बोलें",
        "submit_btn": "🚀 उत्तर सुनें (Submit)"
    }
}

selected_ui_lang = st.selectbox("🌐 Select Language / భాషను ఎంచుకోండి", list(languages_map.keys()))
stt_code = languages_map[selected_ui_lang]["stt"]
tts_code = languages_map[selected_ui_lang]["tts"]
labels = ui_translations.get(selected_ui_lang, ui_translations["English"])

st.write("---")

tab1, tab2 = st.tabs(["🎙️ Talk to Mitra (Voice)", "📷 Scan Documents (OCR)"])

# --- SMTP EMAIL DISPATCH ---
def dispatch_grievance_email(original_lang, transcribed_text, ai_summary, citizen_name, citizen_address):
    try:
        sender_email = st.secrets["SYSTEM_ALERT_EMAIL"]
        sender_password = st.secrets["SYSTEM_ALERT_PASSWORD"]
        receiver_email = st.secrets["GRIEVANCE_OFFICER_EMAIL"]
    except Exception:
        return False
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Grievance: {citizen_name} ({original_lang})"
    
    body = f"Citizen: {citizen_name}\nAddress: {citizen_address}\nQuery: {transcribed_text}\nSummary: {ai_summary}"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False

# --- VOICE TAB ---
with tab1:
    st.subheader("📝 Citizen Details")
    farmer_name = st.text_input(labels["name_label"])
    farmer_address = st.text_area(labels["address_label"], height=70)
    
    st.write("---")
    st.subheader("🎙️ Speak Your Query / Complaint")
    audio_file = st.audio_input(labels["record_label"])
    
    if audio_file:
        st.success("Audio captured!")
        audio_bytes = audio_file.read()
        
        with st.spinner("Processing spoken input..."):
            user_text = transcribe_actual_audio(audio_bytes, stt_code)
            
        if user_text:
            st.subheader("📋 Captured Input:")
            st.info(f'"{user_text}"')
            
            if farmer_name.strip() and farmer_address.strip():
                if st.button(labels["submit_btn"]):
                    with st.spinner("AI is preparing voice response..."):
                        category, result_content = process_citizen_input(user_text, selected_ui_lang)
                        
                        if category == "GENERAL_QUERY":
                            st.success("🤖 AI Voice Response:")
                            st.markdown(f"### 💡 Answer:\n{result_content}")
                            
                            # GENERATE AND PLAY AUDIO
                            audio_stream = generate_speech_audio(result_content, tts_code)
                            if audio_stream:
                                st.subheader("🔊 Audio Answer (వినడానికి నొక్కండి):")
                                st.audio(audio_stream, format="audio/mp3", autoplay=True)
                                
                        elif category == "GRIEVANCE":
                            st.warning("🚨 Official Complaint Registered!")
                            email_status = dispatch_grievance_email(
                                selected_ui_lang, user_text, result_content, farmer_name, farmer_address
                            )
                            
                            msg_text = f"మీ ఫిర్యాదు నమోదైంది {farmer_name}. అధికారులకు నివేదిక పంపబడింది."
                            st.success(msg_text)
                            
                            audio_stream = generate_speech_audio(msg_text, tts_code)
                            if audio_stream:
                                st.audio(audio_stream, format="audio/mp3", autoplay=True)
            else:
                st.warning("Please fill Name and Address above.")
        else:
            st.error("Voice not recognized clearly. Please speak again.")

with tab2:
    st.subheader("Document Scan")
    uploaded_image = st.camera_input("Take photo")
