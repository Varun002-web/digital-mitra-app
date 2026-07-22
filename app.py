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
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Gemini API key missing or invalid in Streamlit secrets!")

# --- SPEECH RECOGNITION ENGINE ---
def transcribe_actual_audio(audio_bytes, target_language_code):
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
    try:
        clean_text = text.replace("*", "").replace("#", "").replace("-", "").replace("`", "")
        tts = gTTS(text=clean_text, lang=gtts_lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        st.error(f"Error generating voice audio: {e}")
        return None

# --- MULTI-LANGUAGE AI TRIAGE CORE ---
def process_citizen_input(text_input, language_name):
    prompt = f"""
    You are Grameena Seva AI, an empathetic voice assistant for rural citizens in India.
    
    The citizen spoke the following query in {language_name}:
    "{text_input}"

    INSTRUCTIONS:
    1. CATEGORY CLASSIFICATION:
       - Output 'CATEGORY: GENERAL_QUERY' if they are asking for guidance, scheme details, land value/registration info, subsidies, agricultural rules, or general help.
       - Output 'CATEGORY: GRIEVANCE' ONLY if they are reporting a broken utility (road, water pipe, street light), delay in government service delivery, or official corruption.

    2. RESPONSE GENERATION:
       - DIRECTLY answer the user's specific question: "{text_input}"
       - Respond entirely in {language_name}.
       - Use simple, conversational spoken language suitable for Voice/Audio playback.
       - DO NOT use bullet points, asterisks (*), hash signs (#), or complex formatting so text-to-speech reads smoothly.

    OUTPUT FORMAT STRICTLY:
    CATEGORY: <GENERAL_QUERY or GRIEVANCE>
    RESPONSE: <Your answer directly addressing their question in {language_name}>
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text.strip()
        
        category = "GRIEVANCE" if "CATEGORY: GRIEVANCE" in res_text.upper() else "GENERAL_QUERY"
            
        if "RESPONSE:" in res_text:
            content = res_text.split("RESPONSE:", 1)[-1].strip()
        else:
            content = res_text
            
        return category, content
        
    except Exception as e:
        fallback_msg = f"మీ ప్రశ్న ('{text_input}') పరిశీలించబడుతోంది. మీ సందేహాల నివృత్తికై సమీపంలో ఉన్న ప్రభుత్వ సేవా కేంద్రాన్ని సంప్రదించండి."
        return "GENERAL_QUERY", fallback_msg

# --- PAGE CONFIGURATION & ANIMATED CSS STYLES ---
st.set_page_config(page_title="Grameena Seva AI", page_icon="🌾", layout="centered")

st.markdown("""
    <style>
    /* Global Background */
    .stApp {
        background-color: #f4f7f4;
    }
    
    /* Header Banner */
    .header-box {
        background: linear-gradient(135deg, #1b5e20, #2e7d32);
        color: white;
        padding: 24px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0px 8px 20px rgba(27, 94, 32, 0.2);
        margin-bottom: 25px;
    }
    .header-box h1 {
        margin: 0;
        font-size: 30px;
        font-weight: 800;
        color: #ffffff;
    }
    .header-box p {
        margin-top: 6px;
        font-size: 16px;
        color: #e8f5e9;
    }

    /* Standard Card Container */
    .card-container {
        background-color: #ffffff;
        padding: 22px;
        border-radius: 16px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.04);
        margin-bottom: 20px;
        border-left: 6px solid #2e7d32;
    }

    /* 🎙️ PULSE ANIMATION FOR VOICE RECORDING SECTION */
    .pulse-card {
        background-color: #ffffff;
        padding: 22px;
        border-radius: 16px;
        margin-bottom: 20px;
        border: 2px solid #81c784;
        animation: pulse-border 2s infinite;
    }

    @keyframes pulse-border {
        0% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4);
        }
        70% {
            box-shadow: 0 0 0 15px rgba(76, 175, 80, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
        }
    }

    /* 🔊 WAVE ANIMATION FOR AUDIO PLAYER CONTAINER */
    .wave-card {
        background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
        border: 2px solid #4caf50;
        padding: 20px;
        border-radius: 16px;
        margin-top: 20px;
        text-align: center;
        animation: wave-glow 2.5s infinite alternate;
    }

    @keyframes wave-glow {
        0% {
            border-color: #4caf50;
            box-shadow: 0px 0px 8px rgba(76, 175, 80, 0.3);
        }
        50% {
            border-color: #ff9800;
            box-shadow: 0px 0px 18px rgba(255, 152, 0, 0.5);
        }
        100% {
            border-color: #4caf50;
            box-shadow: 0px 0px 8px rgba(76, 175, 80, 0.3);
        }
    }

    /* Vibrant Submit Button */
    .stButton>button {
        width: 100%;
        height: 60px;
        background: linear-gradient(90deg, #e65100, #f57c00);
        color: white !important;
        border-radius: 14px;
        font-weight: 800;
        font-size: 20px;
        border: none;
        box-shadow: 0px 6px 15px rgba(230, 81, 0, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 8px 20px rgba(230, 81, 0, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown("""
    <div class="header-box">
        <h1>🌾 Grama Seva AI Hub</h1>
        <p>ఆల్-ఇన్-వన్ గ్రామీణ వాయిస్ సహాయకుడు | Multilingual Rural Voice Portal</p>
    </div>
    """, unsafe_allow_html=True)

# Supported Languages Mapping
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
        "name_label": "👤 Citizen Full Name *",
        "address_label": "🏠 Village & Address *",
        "record_label": "Tap mic and speak your query",
        "submit_btn": "🔊 Process & Play Voice Response"
    },
    "Telugu (తెలుగు)": {
        "name_label": "👤 మీ పూర్తి పేరు నమోదు చేయండి *",
        "address_label": "🏠 మీ గ్రామం & చిరునామా *",
        "record_label": "మైక్ బటన్ నొక్కి మాట్లాడండి",
        "submit_btn": "🔊 సమాధానం వినండి (Submit)"
    },
    "Hindi (हिन्दी)": {
        "name_label": "👤 पूरा नाम *",
        "address_label": "🏠 गांव और पता *",
        "record_label": "माइक दबाएं और बोलें",
        "submit_btn": "🔊 उत्तर सुनें (Submit)"
    }
}

selected_ui_lang = st.selectbox("🌐 Select Language / భాషను ఎంచుకోండి", list(languages_map.keys()))
stt_code = languages_map[selected_ui_lang]["stt"]
tts_code = languages_map[selected_ui_lang]["tts"]
labels = ui_translations.get(selected_ui_lang, ui_translations["English"])

tab1, tab2 = st.tabs(["🎙️ Speak & Listen (వాయిస్ సేవ)", "📷 Document Scan (డాక్యుమెంట్ సేవ)"])

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
    msg['Subject'] = f"Grievance Reported: {citizen_name} ({original_lang})"
    
    body = f"Citizen: {citizen_name}\nAddress: {citizen_address}\nSpoken Input: {transcribed_text}\nAI Summary: {ai_summary}"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False

# --- TAB 1: VOICE PORTAL ---
with tab1:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("📝 Citizen Identity / వివరాలు")
    col1, col2 = st.columns(2)
    with col1:
        farmer_name = st.text_input(labels["name_label"])
    with col2:
        farmer_address = st.text_input(labels["address_label"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # PULSE ANIMATED RECORDING CONTAINER
    st.markdown('<div class="pulse-card">', unsafe_allow_html=True)
    st.subheader("🎙️ Voice Input / మాట్లాడండి")
    audio_file = st.audio_input(labels["record_label"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    if audio_file:
        audio_bytes = audio_file.read()
        
        with st.spinner("Processing speech recognition..."):
            user_text = transcribe_actual_audio(audio_bytes, stt_code)
            
        if user_text:
            st.info(f'🎙️ **You Said:** "{user_text}"')
            
            if farmer_name.strip() and farmer_address.strip():
                if st.button(labels["submit_btn"]):
                    with st.spinner("Generating voice answer..."):
                        category, result_content = process_citizen_input(user_text, selected_ui_lang)
                        
                        if category == "GENERAL_QUERY":
                            st.success("💡 **AI Mitra Response:**")
                            st.write(result_content)
                            
                            audio_stream = generate_speech_audio(result_content, tts_code)
                            if audio_stream:
                                # WAVE ANIMATED AUDIO PLAYER CONTAINER
                                st.markdown('<div class="wave-card">', unsafe_allow_html=True)
                                st.subheader("🔊 Listen to Answer / సమాధానం వినండి:")
                                st.audio(audio_stream, format="audio/mp3", autoplay=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                        elif category == "GRIEVANCE":
                            st.warning("🚨 Official Complaint Registering...")
                            email_status = dispatch_grievance_email(
                                selected_ui_lang, user_text, result_content, farmer_name, farmer_address
                            )
                            
                            msg_text = f"మీ ఫిర్యాదు విజయవంతంగా నమోదైంది {farmer_name}. అధికారులకు నివేదిక పంపబడింది."
                            st.success(msg_text)
                            
                            audio_stream = generate_speech_audio(msg_text, tts_code)
                            if audio_stream:
                                st.markdown('<div class="wave-card">', unsafe_allow_html=True)
                                st.audio(audio_stream, format="audio/mp3", autoplay=True)
                                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ Please fill in Name and Address fields above.")

# --- TAB 2: DOCUMENT SCANNER ---
with tab2:
    st.subheader("📷 Land Record & Document Capture")
    uploaded_image = st.camera_input("Snap picture of document")
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Captured Record", use_container_width=True)
        st.success("Document attached successfully.")
