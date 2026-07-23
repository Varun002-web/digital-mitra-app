import streamlit as st
import os
import smtplib
import io
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image
from google import genai
from google.genai import types
from gtts import gTTS

# --- INITIALIZE GEMINI AI CLIENT ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Gemini Configuration Error: {e}")

# --- TEXT-TO-SPEECH (TTS) AUDIO GENERATOR ---
def generate_speech_audio(text, gtts_lang_code):
    try:
        clean_text = text.replace("*", "").replace("#", "").replace("-", "").replace("`", "")
        # Fallback to hindi if code is unparseable
        lang = gtts_lang_code if len(gtts_lang_code) == 2 else 'hi' 
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        st.error(f"Error generating voice audio: {e}")
        return None

# --- MULTIMODAL AI TRIAGE CORE (AUTO-DETECTS AUDIO LANGUAGE) ---
def process_audio_with_gemini(audio_bytes):
    prompt = """
    You are Grameena Seva AI, an empathetic voice assistant for rural citizens in India.
    Listen to the attached audio query.

    INSTRUCTIONS:
    1. Detect the language the user is speaking.
    2. CATEGORY CLASSIFICATION: 
       - Output 'CATEGORY: GENERAL_QUERY' for schemes, subsidies, loans, land value, or general help.
       - Output 'CATEGORY: GRIEVANCE' ONLY for broken utilities, delays, or corruption.
    3. RESPONSE GENERATION: Answer their specific question directly. 
       - Respond ENTIRELY in the EXACT SAME language they spoke in.
       - Use simple, conversational spoken language. No bullet points or complex formatting.
    4. Provide the exact transcript of what they said.
    5. Provide the 2-letter ISO language code for their language (e.g., 'te' for Telugu, 'hi' for Hindi, 'ta' for Tamil, 'mr' for Marathi, 'en' for English).

    OUTPUT FORMAT STRICTLY LIKE THIS:
    TRANSCRIPT: <What the user actually said>
    TTS_CODE: <2-letter-code>
    CATEGORY: <GENERAL_QUERY or GRIEVANCE>
    RESPONSE: <Your answer in their language>
    """
    
    try:
        # Pass the raw audio bytes directly to Gemini
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type='audio/wav')
        
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=[audio_part, prompt],
        )
        res_text = response.text.strip()
        
        # Parse the structured response using regex
        transcript_match = re.search(r"TRANSCRIPT:\s*(.*)", res_text, re.IGNORECASE)
        tts_match = re.search(r"TTS_CODE:\s*(.*)", res_text, re.IGNORECASE)
        cat_match = re.search(r"CATEGORY:\s*(.*)", res_text, re.IGNORECASE)
        resp_match = re.search(r"RESPONSE:\s*(.*)", res_text, re.IGNORECASE | re.DOTALL)
        
        transcript = transcript_match.group(1).strip() if transcript_match else "Audio processed."
        tts_code = tts_match.group(1).strip().lower() if tts_match else "hi"
        category = "GRIEVANCE" if cat_match and "GRIEVANCE" in cat_match.group(1).upper() else "GENERAL_QUERY"
        content = resp_match.group(1).strip() if resp_match else res_text
            
        return transcript, tts_code, category, content
        
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return "Audio error", "hi", "FALLBACK_GRIEVANCE", "क्षमा करें, तकनीकी समस्या है। आपकी शिकायत दर्ज कर ली गई है।"

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
    .header-box h1 { margin: 0; font-size: 30px; font-weight: 800; color: #38BDF8; }
    .card-container {
        background-color: #1E293B;
        padding: 22px;
        border-radius: 16px;
        margin-bottom: 20px;
        border-left: 6px solid #10B981;
    }
    /* Centered Pulse Mic Card */
    .pulse-card {
        background-color: #1E293B;
        padding: 22px;
        border-radius: 16px;
        margin-bottom: 20px;
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
    div[data-baseweb="input"] {
        background-color: #1E293B !important;
        border-radius: 10px !important;
    }
    input { color: #FFFFFF !important; background-color: #1E293B !important; }
    label { color: #E2E8F0 !important; font-weight: 600; }
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
        <p>Speak in any language! | ఏదైనా భాషలో మాట్లాడండి | किसी भी भाषा में बोलें</p>
    </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🎙️ Speak & Listen", "📷 Document Scan"])

# --- SMTP EMAIL DISPATCH ---
def dispatch_grievance_email(transcribed_text, ai_summary, citizen_name, citizen_address):
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
    msg['Subject'] = f"Grievance/Unresolved Query: {citizen_name}"
    
    body = f"Citizen Name: {citizen_name}\nAddress: {citizen_address}\nSpoken Input: {transcribed_text}\nAI Note/Summary: {ai_summary}"
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
        return False

# --- TAB 1: VOICE PORTAL ---
with tab1:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("📝 Citizen Identity / पहचान")
    col_a, col_b = st.columns(2)
    with col_a:
        farmer_name = st.text_input("👤 Full Name *")
    with col_b:
        farmer_address = st.text_input("🏠 Village & Address *")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="pulse-card">', unsafe_allow_html=True)
    st.markdown("<h3>🎙️ Tap Mic to Speak (Auto-detects language)</h3>", unsafe_allow_html=True)
    
    # 🎯 CENTER THE AUDIO INPUT USING COLUMNS
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        audio_file = st.audio_input("Record", label_visibility="hidden")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if audio_file:
        audio_bytes = audio_file.read()
            
        if farmer_name.strip() and farmer_address.strip():
            if st.button("🔊 Process & Listen (Submit)"):
                with st.spinner("Analyzing audio and detecting language..."):
                    
                    # Pass bytes directly to Gemini 
                    transcript, tts_code, category, result_content = process_audio_with_gemini(audio_bytes)
                    
                    st.info(f'🎙️ **Transcript (Detected by AI):** "{transcript}"')
                    
                    if category == "GENERAL_QUERY":
                        st.success("💡 **AI Mitra Response:**")
                        st.write(result_content)
                        
                        audio_stream = generate_speech_audio(result_content, tts_code)
                        if audio_stream:
                            st.markdown('<div class="wave-card">', unsafe_allow_html=True)
                            st.subheader("🔊 Listen to Answer:")
                            st.audio(audio_stream, format="audio/mp3", autoplay=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                    elif category in ["GRIEVANCE", "FALLBACK_GRIEVANCE"]:
                        st.warning("🚨 Routing request to Grievance Officer via Email...")
                        email_status = dispatch_grievance_email(
                            transcript, result_content, farmer_name, farmer_address
                        )
                        
                        if email_status:
                            st.success("📧 Email successfully sent to Grievance Officer!")
                        
                        st.info(result_content)
                        audio_stream = generate_speech_audio(result_content, tts_code)
                        if audio_stream:
                            st.markdown('<div class="wave-card">', unsafe_allow_html=True)
                            st.audio(audio_stream, format="audio/mp3", autoplay=True)
                            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please fill in Name and Address fields above before submitting.")

# --- TAB 2: DOCUMENT SCANNER ---
with tab2:
    st.subheader("📷 Land Record & Document Capture")
    uploaded_image = st.camera_input("Snap picture of document")
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Captured Record", use_container_width=True)
        st.success("Document attached successfully.")
