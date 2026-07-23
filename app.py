import streamlit as st
import os
import smtplib
import io
import speech_recognition as sr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from gtts import gTTS

# --- INITIALIZE GEMINI AI CLIENT ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Gemini Configuration Error: {e}")

# --- SPEECH RECOGNITION ENGINE ---
def transcribe_actual_audio(audio_bytes):
    recognizer = sr.Recognizer()
    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            # Try transcribing without restricting language
            actual_text = recognizer.recognize_google(audio_data)
            return actual_text
    except Exception:
        return None

# --- TEXT-TO-SPEECH (TTS) AUDIO GENERATOR ---
def generate_speech_audio(text, gtts_lang_code='hi'):
    try:
        clean_text = text.replace("*", "").replace("#", "").replace("-", "").replace("`", "")
        tts = gTTS(text=clean_text, lang=gtts_lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        # Fallback to English TTS if specific language fails
        try:
            tts = gTTS(text=clean_text, lang='en', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp
        except Exception:
            return None

# --- AUTO-DETECTING MULTI-LANGUAGE AI TRIAGE ---
def process_citizen_input_auto(text_input):
    prompt = f"""
    You are Grameena Seva AI, an empathetic voice assistant for rural citizens in India.
    
    The citizen spoke the following query:
    "{text_input}"

    INSTRUCTIONS:
    1. LANGUAGE DETECTION:
       - Automatically detect the language of the spoken text (e.g., Hindi, Telugu, Tamil, Marathi, English, etc.).
       - Store the detected language name in standard English (e.g., 'Hindi', 'Telugu').
       - Provide the ISO 639-1 2-letter language code for TTS playback (e.g., 'hi' for Hindi, 'te' for Telugu, 'en' for English, 'ta' for Tamil, 'mr' for Marathi, 'bn' for Bengali).

    2. CATEGORY CLASSIFICATION:
       - Output 'CATEGORY: GENERAL_QUERY' if they are asking for guidance, scheme details, tractor/agriculture subsidies, loans, land value, or general help.
       - Output 'CATEGORY: GRIEVANCE' ONLY if they are explicitly reporting a broken utility (road, water pipe, street light), delay in official service delivery, or official corruption.

    3. RESPONSE GENERATION:
       - DIRECTLY answer the user's specific question: "{text_input}"
       - Respond ENTIRELY in the same language as the spoken text.
       - Use simple, conversational spoken language suitable for Voice/Audio playback.
       - DO NOT use bullet points, asterisks (*), hash signs (#), or complex formatting so text-to-speech reads smoothly.

    OUTPUT FORMAT STRICTLY:
    LANGUAGE: <Language Name>
    LANG_CODE: <2-letter ISO language code>
    CATEGORY: <GENERAL_QUERY or GRIEVANCE>
    RESPONSE: <Your answer directly addressing their question in detected language>
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt,
        )
        res_text = response.text.strip()
        
        # Parse output fields
        lang_name = "English"
        lang_code = "en"
        category = "GENERAL_QUERY"
        content = res_text

        lines = res_text.split("\n")
        for line in lines:
            if line.startswith("LANGUAGE:"):
                lang_name = line.replace("LANGUAGE:", "").strip()
            elif line.startswith("LANG_CODE:"):
                lang_code = line.replace("LANG_CODE:", "").strip().lower()
            elif line.startswith("CATEGORY:"):
                category = "GRIEVANCE" if "GRIEVANCE" in line.upper() else "GENERAL_QUERY"

        if "RESPONSE:" in res_text:
            content = res_text.split("RESPONSE:", 1)[-1].strip()
            
        return lang_name, lang_code, category, content
        
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return "Unknown", "en", "FALLBACK_GRIEVANCE", "Your query has been forwarded to the officers for assistance."

# --- SMTP EMAIL DISPATCH ---
def dispatch_grievance_email(detected_lang, transcribed_text, ai_summary):
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
    msg['Subject'] = f"New Grievance Registered ({detected_lang})"
    
    body = f"Spoken Input: {transcribed_text}\nDetected Language: {detected_lang}\nAI Response / Note: {ai_summary}"
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

# --- PAGE CONFIGURATION & CENTERED STYLING ---
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
    
    /* Center aligning container elements */
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
        <p>Multilingual Rural Voice Assistant | మాట్లాడండి / बोलें / Speak</p>
    </div>
    """, unsafe_allow_html=True)

# --- CENTERED VOICE INPUT UI ---
st.markdown('<div class="center-card">', unsafe_allow_html=True)
st.markdown("### 🎙️ Tap & Speak / మాట్లాడండి / बोलें")
st.caption("Auto-detects Hindi, Telugu, English, Tamil, Kannada, Marathi & more")

# Center audio input control
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    audio_file = st.audio_input("Record Voice")
st.markdown('</div>', unsafe_allow_html=True)

if audio_file:
    audio_bytes = audio_file.read()
    
    with st.spinner("Recognizing speech..."):
        user_text = transcribe_actual_audio(audio_bytes)
        
    if user_text:
        st.info(f'🎙️ **You Said:** "{user_text}"')
        
        # CENTERED PROCESS BUTTON
        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
        with btn_col2:
            process_btn = st.button("🔊 Process & Respond", use_container_width=True)
            
        if process_btn:
            with st.spinner("Analyzing query and language..."):
                lang_name, lang_code, category, result_content = process_citizen_input_auto(user_text)
                
                st.success(f"🌐 **Detected Language:** {lang_name}")
                
                if category == "GENERAL_QUERY":
                    st.markdown(f"### 💡 **AI Response ({lang_name}):**")
                    st.write(result_content)
                    
                    audio_stream = generate_speech_audio(result_content, gtts_lang_code=lang_code)
                    if audio_stream:
                        st.markdown('<div class="wave-card">', unsafe_allow_html=True)
                        st.subheader("🔊 Listen to Answer:")
                        st.audio(audio_stream, format="audio/mp3", autoplay=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                elif category in ["GRIEVANCE", "FALLBACK_GRIEVANCE"]:
                    st.warning("🚨 Routing request to Grievance Officer via Email...")
                    email_status = dispatch_grievance_email(lang_name, user_text, result_content)
                    
                    if email_status:
                        st.success("📧 Email successfully sent to Grievance Officer!")
                    
                    st.info(result_content)
                    audio_stream = generate_speech_audio(result_content, gtts_lang_code=lang_code)
                    if audio_stream:
                        st.markdown('<div class="wave-card">', unsafe_allow_html=True)
                        st.audio(audio_stream, format="audio/mp3", autoplay=True)
                        st.markdown('</div>', unsafe_allow_html=True)
