import streamlit as st
import os
import smtplib
import io
import speech_recognition as sr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image
from google import genai
from gtts import gTTS

# --- INITIALIZE GEMINI AI CLIENT ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Gemini Configuration Error: {e}")

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

# --- DYNAMIC MULTI-LANGUAGE FALLBACK MESSAGES ---
FALLBACK_MESSAGES = {
    "Hindi (हिन्दी)": "आपका प्रश्न अधिकारियों को भेज दिया गया है। सहायता के लिए निकटतम सेवा केंद्र से संपर्क करें।",
    "Telugu (తెలుగు)": "మీ ప్రశ్న అధికారులకు పంపబడింది. సహాయం కోసం సమీపంలో ఉన్న సేవా కేంద్రాన్ని సంప్రదించండి.",
    "English": "Your query has been forwarded to the officers. Please contact the nearest service center for further assistance.",
    "Tamil (தமிழ்)": "உங்கள் கேள்வி அதிகாரிகளுக்கு அனுப்பப்பட்டுள்ளது. உதவிக்கு அருகிலுள்ள சேவை மையத்தைத் தொடர்பு கொள்ளவும்.",
    "Kannada (ಕನ್ನಡ)": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಅಧಿಕಾರಿಗಳಿಗೆ ಕಳುಹಿಸಲಾಗಿದೆ. ನೆರವಿಗಾಗಿ ಹತ್ತಿರದ ಸೇವಾ ಕೇಂದ್ರವನ್ನು ಸಂಪರ್ಕಿಸಿ.",
    "Marathi (मराठी)": "तुमचा प्रश्न अधिकाऱ्यांकडे पाठवण्यात आला आहे. मदतीसाठी जवळच्या सेवा केंद्राशी संपर्क साधा.",
    "Bengali (বাংলা)": "আপনার প্রশ্নটি কর্মকর্তাদের কাছে পাঠানো হয়েছে। সহায়তার জন্য নিকটস্থ সেবা কেন্দ্রে যোগাযোগ করুন।",
    "Gujarati (ગુજરાતી)": "તમારો પ્રશ્ન અધિકારીઓને મોકલવામાં આવ્યો છે. સહાય માટે નજીકના સેવા કેન્દ્રનો સંપર્ક કરો.",
    "Malayalam (മലയാളം)": "നിങ്ങളുടെ ചോദ്യം ഉദ്യോഗസ്ഥർക്ക് കൈമാറി. സഹായത്തിന് അടുത്തുള്ള സേവന കേന്ദ്രവുമായി ബന്ധപ്പെടുക.",
    "Punjabi (ਪੰਜਾਬੀ)": "ਤੁਹਾਡਾ ਸਵਾਲ ਅਧਿਕਾਰੀਆਂ ਨੂੰ ਭੇਜ ਦਿੱਤਾ ਗਿਆ ਹੈ। ਸਹਾਇਤਾ ਲਈ ਨੇੜਲੇ ਸੇਵਾ ਕੇਂਦਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
    "Urdu (اُردُو)": "آپ کا سوال حکام کو بھیج دیا گیا ہے۔ مدد کے لیے قریبی سروس سنٹر سے رابطہ کریں۔"
}

# --- MULTI-LANGUAGE AI TRIAGE CORE ---
def process_citizen_input(text_input, language_name):
    prompt = f"""
    You are Grameena Seva AI, an empathetic voice assistant for rural citizens in India.
    
    The citizen spoke the following query in {language_name}:
    "{text_input}"

    INSTRUCTIONS:
    1. CATEGORY CLASSIFICATION:
       - Output 'CATEGORY: GENERAL_QUERY' if they are asking for guidance, scheme details, tractor/agriculture subsidies, loans, land value, or general help.
       - Output 'CATEGORY: GRIEVANCE' ONLY if they are explicitly reporting a broken utility (road, water pipe, street light), delay in official service delivery, or official corruption.

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
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt,
        )
        res_text = response.text.strip()
        
        category = "GRIEVANCE" if "CATEGORY: GRIEVANCE" in res_text.upper() else "GENERAL_QUERY"
            
        if "RESPONSE:" in res_text:
            content = res_text.split("RESPONSE:", 1)[-1].strip()
        else:
            content = res_text
            
        return category, content
        
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        fallback_msg = FALLBACK_MESSAGES.get(language_name, FALLBACK_MESSAGES["English"])
        return "FALLBACK_GRIEVANCE", fallback_msg

# --- SMTP EMAIL DISPATCH ---
def dispatch_grievance_email(original_lang, transcribed_text, ai_summary):
    try:
        sender_email = st.secrets["SYSTEM_ALERT_EMAIL"].strip()
        sender_password = st.secrets["SYSTEM_ALERT_PASSWORD"].replace(" ", "").strip()
        receiver_email = st.secrets["GRIEVANCE_OFFICER_EMAIL"].strip()
    except Exception as e:
        st.error(f"Secrets configuration missing: {e}")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Grievance/Query Alert ({original_lang})"
    
    body = f"Language: {original_lang}\nSpoken Input: {transcribed_text}\nAI Note/Summary: {ai_summary}"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.ehlo()
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e1:
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            return True
        except Exception as e2:
            st.error(f"Email Dispatch Failed: {e1} | Fallback: {e2}")
            return False

# --- PAGE CONFIGURATION & DARK THEME ---
st.set_page_config(page_title="Grameena Seva AI", page_icon="🌾", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    .header-box {
        background: linear-gradient(135deg, #1E293B, #334155);
        border: 1px solid #475569;
        color: #F8FAFC;
        padding: 24px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 25px;
    }
    .header-box h1 { margin: 0; font-size: 32px; font-weight: 800; color: #38BDF8; }
    
    .center-card {
        background-color: #1E293B;
        padding: 30px;
        border-radius: 20px;
        margin: 0 auto 20px auto;
        border: 2px solid #059669;
        text-align: center;
    }
    .wave-card {
        background: linear-gradient(135deg, #1E293B, #0F172A);
        border: 2px solid #F59E0B;
        padding: 20px;
        border-radius: 16px;
        margin-top: 20px;
        text-align: center;
    }
    div[data-baseweb="select"] {
        background-color: #1E293B !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] * { color: #FFFFFF !important; }
    .stButton>button {
        width: 100%;
        height: 60px;
        background: linear-gradient(90deg, #D97706, #F59E0B);
        color: #FFFFFF !important;
        border-radius: 14px;
        font-weight: 800;
        font-size: 20px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown("""
    <div class="header-box">
        <h1>🌾 Grama Seva AI Hub</h1>
        <p>ఆల్-ఇన్-వన్ గ్రామీణ వాయిస్ సహాయకుడు | Rural Voice Portal</p>
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
        "title": "🎙️ Tap Mic & Speak",
        "record_label": "Speak your question",
        "submit_btn": "🔊 Process & Listen Response"
    },
    "Telugu (తెలుగు)": {
        "title": "🎙️ మైక్ బటన్ నొక్కి మాట్లాడండి",
        "record_label": "మీ ప్రశ్న చెప్పండి",
        "submit_btn": "🔊 సమాధానం వినండి (Submit)"
    },
    "Hindi (हिन्दी)": {
        "title": "🎙️ माइक दबाएं और बोलें",
        "record_label": "अपना प्रश्न बोलें",
        "submit_btn": "🔊 उत्तर सुनें (Submit)"
    }
}

selected_ui_lang = st.selectbox("🌐 Select Language / भाषा चुनें / భాషను ఎంచుకోండి", list(languages_map.keys()))
stt_code = languages_map[selected_ui_lang]["stt"]
tts_code = languages_map[selected_ui_lang]["tts"]
labels = ui_translations.get(selected_ui_lang, ui_translations["English"])

tab1, tab2 = st.tabs(["🎙️ Speak & Listen", "📷 Document Scan"])

# --- TAB 1: VOICE PORTAL ---
with tab1:
    st.markdown('<div class="center-card">', unsafe_allow_html=True)
    st.markdown(f"### {labels['title']}")
    
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        audio_file = st.audio_input(labels["record_label"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    if audio_file:
        audio_bytes = audio_file.read()
        
        with st.spinner("Processing speech recognition..."):
            user_text = transcribe_actual_audio(audio_bytes, stt_code)
            
        if user_text:
            st.info(f'🎙️ **You Said:** "{user_text}"')
            
            btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
            with btn_col2:
                process_btn = st.button(labels["submit_btn"], use_container_width=True)
                
            if process_btn:
                with st.spinner("Processing request..."):
                    category, result_content = process_citizen_input(user_text, selected_ui_lang)
                    
                    if category == "GENERAL_QUERY":
                        st.success("💡 **AI Response:**")
                        st.write(result_content)
                        
                        audio_stream = generate_speech_audio(result_content, tts_code)
                        if audio_stream:
                            st.markdown('<div class="wave-card">', unsafe_allow_html=True)
                            st.subheader("🔊 Listen to Answer:")
                            st.audio(audio_stream, format="audio/mp3", autoplay=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                    elif category in ["GRIEVANCE", "FALLBACK_GRIEVANCE"]:
                        st.warning("🚨 Routing request to Grievance Officer via Email...")
                        email_status = dispatch_grievance_email(selected_ui_lang, user_text, result_content)
                        
                        if email_status:
                            st.success("📧 Email successfully sent to Grievance Officer!")
                        else:
                            st.error("⚠️ Could not send email. Verify your Gmail App Password in Streamlit Secrets.")

                        st.info(result_content)
                        
                        audio_stream = generate_speech_audio(result_content, tts_code)
                        if audio_stream:
                            st.markdown('<div class="wave-card">', unsafe_allow_html=True)
                            st.audio(audio_stream, format="audio/mp3", autoplay=True)
                            st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: DOCUMENT SCANNER ---
with tab2:
    st.subheader("📷 Land Record & Document Capture")
    uploaded_image = st.camera_input("Snap picture of document")
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Captured Record", use_container_width=True)
        st.success("Document attached successfully.")
