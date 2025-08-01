import streamlit as st
from PIL import Image
import pytesseract
from streamlit_mic_recorder import speech_to_text
from src.hackatone.crew import SchemeAndDocumentCrew
import re

st.set_page_config(page_title="🎤📄 Scheme Info Assistant", layout="wide")

# --- Inject custom CSS ---
def inject_css(file_path):
    with open(file_path, "r") as f:
        css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

inject_css("static/style.css")  # or "styles.css" if in root

# Set up Tesseract (adjust path for your system)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize session variables
if "scheme_result" not in st.session_state:
    st.session_state.scheme_result = None
if "last_mic_input" not in st.session_state:
    st.session_state.last_mic_input = ""
if "scheme_ran" not in st.session_state:
    st.session_state.scheme_ran = False

def show_scheme_reminders(agent_output: str):
    # 📅 Deadline detection
    deadline_match = re.search(
        r'(Deadline|Last date|Apply before):?\s*(\d{1,2}(st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})',
        agent_output, re.IGNORECASE
    )

    # 🧓 Age eligibility (improved)
    age_match = re.search(
        r'(above|over|under|below)?\s*(the\s+age\s+of\s+)?(\d{1,2})\s*(years)?(\s*(and|to|–|-)\s*(\d{1,2}))?',
        agent_output, re.IGNORECASE
    )

    # 🧒 Minor eligibility
    minor_match = re.search(
        r'(minor|children)\s*\(?(aged|age)?\s*(\d{1,2})\s*(to|–|-)\s*(\d{1,2})\)?',
        agent_output, re.IGNORECASE
    )

    # 💰 Income eligibility (improved)
    income_match = re.search(
        r'(BPL|Below Poverty Line|income\s*(below|under|less than)?\s*₹?\s*\d{1,3}(,\d{3})*|no income (restrictions|limit))',
        agent_output, re.IGNORECASE
    )

    # Show deadline
    if deadline_match:
        st.warning(f"⏰ Deadline: {deadline_match.group(0)}")

    # Show age requirement
    if age_match:
        st.info(f"🎯 Age Requirement: {age_match.group(0)}")
    
    if minor_match:
        st.info(f"🧒 Minor Eligibility: {minor_match.group(0)}")

    # Show income condition
    if income_match:
        st.info(f"💸 Income Condition: {income_match.group(0)}")

# Page setup


st.markdown(
    '<div class="main-title">📋 Ask About Any Government Scheme '
    '<span style="font-size:28px;">(किसी भी सरकारी योजना के बारे में पूछें)</span></div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-subtitle">'
    'You can record your voice and upload related documents to verify if they match scheme requirements. <br>'
    'आवाज़ रिकॉर्ड कर सकते हैं और संबंधित दस्तावेज़ अपलोड कर सकते हैं ताकि यह जांचा जा सके कि वे योजना की आवश्यकताओं से मेल खाते हैं या नहीं।'
    '</div>',
    unsafe_allow_html=True
)


# Initialize crew
crew = SchemeAndDocumentCrew()

# --- 🎙 Audio Recording ---
text_from_mic = speech_to_text(
    start_prompt="🎙 Start Recording",
    stop_prompt="🔴 Stop Recording",
    language="en",
    use_container_width=True,
    just_once=True,
    key="mic"
)
if text_from_mic == "Listening...":
    st.markdown("""
        <div class="recording-indicator">
            <div class="recording-dot"></div>
            Recording in progress...
        </div>
    """, unsafe_allow_html=True)

# Detect mic input change
mic_changed = (
    text_from_mic and text_from_mic.strip() != "" and
    text_from_mic != st.session_state.last_mic_input
)

# --- 🧠 Processing ---
# --- 🧠 Processing ---
# Run the crew if mic input changed
if mic_changed or (text_from_mic and not st.session_state.scheme_ran):
    with st.spinner("Working on your request..."):
        result = crew.run_scheme_or_fraud_flow(text_from_mic)
        st.session_state.scheme_result = result
        st.session_state.last_mic_input = text_from_mic
        st.session_state.scheme_ran = True

# Always display stored result if available

# --- 🧠 Processing ---
if text_from_mic and text_from_mic.strip() != "":
    st.markdown(f"""
    <div class='response-box'>
        <div class='response-heading'>📝 Transcribed Query:</div>
        {text_from_mic}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='response-box'>
        <div class='response-heading'>🤖 AI Response:</div>
    """, unsafe_allow_html=True)

    with st.spinner("Working on your request..."):
        result = crew.run_scheme_or_fraud_flow(text_from_mic)

        st.markdown(f"""
        <div style="padding-left: 1rem; padding-right: 1rem; padding-bottom: 1rem; font-size: 1.05rem; color: #003344;">
        📄 {result}
        </div>
        </div> <!-- closes response-box -->
        """, unsafe_allow_html=True)

        show_scheme_reminders(str(result))

# --- 📤 Sidebar for Document Upload ---
with st.sidebar:
    st.header("📄 Optional: Upload Scheme Documents (वैकल्पिक: योजना दस्तावेज़ अपलोड करें)")
    uploaded_files = st.file_uploader(
        "Upload Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )

documents_info = []

if uploaded_files:
    st.sidebar.markdown("✅ Documents received.")
    for file in uploaded_files:
        img = Image.open(file)
        text = pytesseract.image_to_string(img)
        def mask_sensitive_info(text):
            # Mask Aadhaar numbers (12-digit)
            text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'XXXX-XXXX-XXXX', text)

            # Optional: mask phone numbers (10-digit)
            text = re.sub(r'\b\d{10}\b', 'XXXXXXXXXX', text)

            # Optional: remove full address lines if patterns match
            text = re.sub(r'(Address:.*)', '[Address Hidden]', text, flags=re.IGNORECASE)

            # Optional: redact email IDs
            text = re.sub(r'\S+@\S+', '[email hidden]', text)

            return text
        # Mask sensitive information
        new_text = mask_sensitive_info(text)

        documents_info.append({
            "filename": file.name,
            "text": new_text
        })

    # Optional: Preview
    with st.expander("📜 Preview Extracted Texts"):
        for doc in documents_info:
            st.markdown(f"🗂 {doc['filename']}")
            st.text_area(label="", value=doc["text"], height=150)

    if documents_info:
        st.subheader("📁 Document Validation:")
        with st.spinner("Checking your documents for the scheme..."):
            validation_result = crew.run_document_validation_flow(
                scheme_info=st.session_state.last_mic_input,
                documents_info=documents_info
            )
            st.markdown(validation_result)

# 🔄 Reset button
if st.button("🔄 Reset Session"):
    st.session_state.scheme_result = None
    st.session_state.last_mic_input = ""
    st.session_state.scheme_ran = False
    st.rerun()