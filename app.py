import os
import re
import time
import streamlit as st
from together import Together
import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import io
import base64

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.error(f"Image not found: {image_path}")
        return ""

def extract_text(file_bytes, file_type):
    text = ""
    try:
        if file_type == "application/pdf":
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                        tables = page.extract_tables()
                        for table in tables:
                            text += "\n".join(["\t".join(map(str, row)) for row in table]) + "\n"
                if text.strip():
                    return text
            except Exception as pdf_error:
                st.error(f"PDF parsing failed: {str(pdf_error)}")
                images = convert_from_bytes(file_bytes)
                for image in images:
                    text += pytesseract.image_to_string(image)
        
        elif file_type in ["image/png", "image/jpeg"]:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
        
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            
        return text.strip()
    
    except Exception as e:
        st.error(f"Text extraction failed: {str(e)}")
        return ""

def parse_response(response):
    # Extract sections using regex
    summary = re.search(r"\[Summary\](.*?)(?=\[Key Findings\]|$)", response, re.DOTALL)
    findings = re.search(r"\[Key Findings\](.*?)(?=\[Recommended Actions\]|$)", response, re.DOTALL)
    actions = re.search(r"\[Recommended Actions\](.*)", response, re.DOTALL)
    
    formatted = ""
    if summary:
        formatted += f"**Summary**\n{summary.group(1).strip()}\n\n"
    if findings:
        formatted += f"**Key Findings**\n{findings.group(1).strip()}\n\n"
    if actions:
        formatted += f"**Recommended Actions**\n{actions.group(1).strip()}"
    
    return formatted if formatted else "Could not parse response. Please try again."

def medical_chat(api_key, text, question):
    if not api_key:
        st.error("Please enter your Together API Key")
        return ""
    
    client = Together(api_key=api_key)
    
    prompt = f"""
    You are a medical report interpreter. Respond ONLY in this format:
    
    [Summary]
    - Concise 2-3 line summary
    - Focus on main concerns
    
    [Key Findings]
    - Bullet points of notable results
    - Highlight abnormal values with ⚠️
    - Include normal ranges
    
    [Recommended Actions]
    - Suggest next steps
    - List specialist referrals if needed
    - Reminder to consult doctor
    
    Do NOT include:
    - Your thought process
    - Disclaimers
    - Explanations
    - Markdown formatting
    
    Document:
    {text[:6000]}
    
    Question: {question}
    
    Response:
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2050,
            request_timeout=45
        )
        return parse_response(response.choices[0].message.content)
        
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return "Error generating response. Please try again."

def main():
    st.set_page_config(
        page_title="MedExplain AI - Medical Report Assistant",
        layout="centered",
        page_icon="🩺"
    )

    MEDICAL_LOGO = get_base64_image("medical-logo.png")
    HIPAA_LOGO = get_base64_image("hipaa-logo.png")
    POWERED_LOGO = get_base64_image("deepseek-medical.png")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Upload a medical report and ask questions about:\n\n- Test results\n- Scan findings\n- Medication lists\n- Doctor's notes"
        }]

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 1rem;">
        <img src="data:image/png;base64,{MEDICAL_LOGO}" style="height: 100px; width: auto;"/>
        <h1 style="margin: 0; font-size: 2.2rem;">MedExplain AI</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.warning("⚠️ This tool provides general explanations and does not replace professional medical advice.")

    with st.sidebar:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 25px;">
                <img src="data:image/png;base64,{HIPAA_LOGO}" style="height: 40px; width: auto;"/>
                <div>
                    <h3 style="margin: 0;">Security</h3>
                    <p style="font-size: 0.8rem; margin: 0;">Encrypted processing<br>No data retention</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        api_key = st.text_input("Enter Together API Key:", type="password")
        st.markdown("[Get API Key →](https://together.ai)")
        
        st.divider()
        
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="data:image/png;base64,{POWERED_LOGO}" style="height: 35px; width: auto;"/>
                <span style="font-size: 0.9rem;">Powered by DeepSeek-R1</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    uploaded_file = st.file_uploader(
        "Upload Medical Report",
        type=["pdf", "docx", "png", "jpg", "jpeg"],
        help="Max size: 200MB"
    )

    if uploaded_file and uploaded_file.size > 200 * 1024 * 1024:
        st.error("File size exceeds 200MB limit")
        return
    
    # Reset chat if file is removed
    if uploaded_file is None and 'document_text' in st.session_state:
        del st.session_state.document_text
        st.session_state.messages = [{
        "role": "assistant",
        "content": "Upload a medical report and ask questions about:\n\n- Test results\n- Scan findings\n- Medication lists\n- Doctor's notes"
    }]

    if uploaded_file and api_key:
        if 'document_text' not in st.session_state:
            with st.spinner("Analyzing document..."):
                text = extract_text(uploaded_file.getvalue(), uploaded_file.type)
                if text:
                    st.session_state.document_text = text
                    st.success("Analysis complete! Ask questions below.")
                else:
                    st.error("Failed to process document")

    if 'document_text' in st.session_state:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if question := st.chat_input("Ask about your report..."):
            st.session_state.messages.append({"role": "user", "content": question})
            
            with st.chat_message("user"):
                st.markdown(question)
            
            with st.chat_message("assistant"):
                with st.spinner("Generating response..."):
                    start_time = time.time()
                    response = medical_chat(api_key, st.session_state.document_text, question)
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 50px; justify-content: center;">
            <img src="data:image/png;base64,{POWERED_LOGO}" style="height: 25px; width: auto;"/>
            <span style="font-size: 0.9rem; color: #666;">Medical AI Analysis System</span>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()