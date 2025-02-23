import streamlit as st
import pytesseract
from PIL import Image
import os
import json
from datetime import datetime
import pandas as pd
import io
import google.generativeai as genai
import pdf2image
import shutil
from pathlib import Path

# Configure Gemini API
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Apply Custom Styling
st.markdown("""
    <style>
        /* Background color */
        body {
            background-color: #F4F4F8;
        }

        /* Page title styling */
        .title {
            font-size: 40px;
            font-weight: bold;
            text-align: center;
            color: #4A90E2;
        }

        /* Section headers */
        .header {
            font-size: 24px;
            font-weight: bold;
            color: #FF6347;
            margin-top: 20px;
        }

        /* Expander Styling */
        .st-expander {
            border: 2px solid #4CAF50;
            border-radius: 8px;
            background-color: #E8F5E9;
        }

        /* Buttons */
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            font-size: 18px;
            border-radius: 10px;
            padding: 10px 24px;
        }

        /* Sidebar Styling */
        .stSidebar {
            background-color: #333;
            color: white;
        }

    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>📄 DOCMATRIX: AI-Powered Document Analyzer</h1>", unsafe_allow_html=True)

def init_system():
    base_dirs = ['uploads', 'general'] + list(DOMAIN_CATEGORIES.keys())
    for dir in base_dirs:
        os.makedirs(dir, exist_ok=True)

    if not os.path.exists('document_registry.json'):
        with open('document_registry.json', 'w') as f:
            json.dump([], f)

DOMAIN_CATEGORIES = {
    'finance': ['invoice', 'payment', 'bank', 'transaction', 'budget', 'financial', 'tax', 'revenue', 'expense'],
    'education': ['study', 'course', 'academic', 'school', 'university', 'grade', 'assignment', 'lecture', 'exam'],
    'legal': ['contract', 'agreement', 'law', 'legal', 'terms', 'conditions', 'policy', 'compliance'],
    'technical': ['specification', 'technical', 'manual', 'documentation', 'system', 'software', 'hardware'],
    'medical': ['health', 'medical', 'patient', 'diagnosis', 'treatment', 'prescription', 'hospital']
}

def main():
    st.sidebar.title("🔍 Navigation")
    
    page = st.sidebar.radio("Select Page", ["Upload & Analyze", "View Documents", "Generate Reports"])

    if page == "Upload & Analyze":
        st.markdown("<h2 class='header'>📤 Upload and Analyze Document</h2>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose a document", type=['pdf', 'png', 'jpg', 'jpeg'])

        if uploaded_file:
            st.success(f"✅ {uploaded_file.name} uploaded successfully!")

            if st.button("🚀 Process Document"):
                with st.spinner("🔄 Extracting text and analyzing..."):
                    text = extract_text_from_file(uploaded_file)
                    
                    if text:
                        with st.expander("📜 Extracted Text"):
                            st.text(text)

                        domain = determine_domain(text)
                        st.info(f"📌 Detected Domain: **{domain.title()}**")

                        st.markdown("<h3 class='header'>📝 Document Summary</h3>", unsafe_allow_html=True)
                        summary = generate_summary(text)
                        st.markdown(summary)

                        st.markdown("<h3 class='header'>🔬 Detailed Analysis</h3>", unsafe_allow_html=True)
                        analysis = analyze_with_gemini(text, domain)
                        st.markdown(analysis)

                        if save_document(uploaded_file, text, domain, analysis, summary):
                            st.success("✅ Document successfully processed and saved!")
                        else:
                            st.error("❌ Failed to save document.")
                    else:
                        st.error("⚠️ No text could be extracted.")

    elif page == "View Documents":
        st.markdown("<h2 class='header'>📂 View Processed Documents</h2>", unsafe_allow_html=True)
        documents = load_documents()
        
        if documents:
            selected_domain = st.selectbox("🔍 Filter by Domain", sorted({"All"} | {doc.get('domain', 'general') for doc in documents}))

            filtered_docs = documents if selected_domain == 'All' else [doc for doc in documents if doc.get('domain', 'general') == selected_domain]

            for doc in filtered_docs:
                with st.expander(f"📄 {doc['filename']} - {doc.get('domain', 'general').title()} - {doc.get('processed_date', 'N/A')}"):
                    if doc.get('summary'):
                        st.markdown("### 📌 Summary")
                        st.markdown(doc['summary'])
                    if doc.get('analysis'):
                        st.markdown("### 📊 Detailed Analysis")
                        st.markdown(doc['analysis'])

    elif page == "Generate Reports":
        st.markdown("<h2 class='header'>📊 Generate Reports</h2>", unsafe_allow_html=True)
        documents = load_documents()

        if documents:
            report_type = st.selectbox("📁 Select Report Type", ["Domain Distribution", "Timeline Analysis"])

            if report_type == "Domain Distribution":
                domains = [doc.get('domain', 'general') for doc in documents]
                domain_counts = pd.Series(domains).value_counts().reset_index()
                domain_counts.columns = ['Domain', 'Count']
                
                st.subheader("📊 Document Distribution by Domain")
                st.bar_chart(domain_counts.set_index('Domain'))
                st.dataframe(domain_counts)

            elif report_type == "Timeline Analysis":
                timeline_data = pd.DataFrame([{
                    'date': datetime.strptime(doc.get('processed_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),"%Y-%m-%d %H:%M:%S"),
                    'domain': doc.get('domain', 'general')
                } for doc in documents])
                
                st.subheader("📅 Documents Processed Over Time")
                daily_counts = timeline_data.groupby('date').size()
                st.line_chart(daily_counts)
                
                st.subheader("📜 Processing Statistics")
                st.write(f"✅ Total documents: {len(documents)}")
                st.write(f"📅 First document: {timeline_data['date'].min()}")
                st.write(f"📆 Last document: {timeline_data['date'].max()}")

if __name__ == "__main__":
    main()
