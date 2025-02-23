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

# Domain categories and their keywords
DOMAIN_CATEGORIES = {
    'finance': ['invoice', 'payment', 'bank', 'transaction', 'budget', 'financial', 'tax', 'revenue', 'expense'],
    'education': ['study', 'course', 'academic', 'school', 'university', 'grade', 'assignment', 'lecture', 'exam'],
    'legal': ['contract', 'agreement', 'law', 'legal', 'terms', 'conditions', 'policy', 'compliance'],
    'technical': ['specification', 'technical', 'manual', 'documentation', 'system', 'software', 'hardware'],
    'medical': ['health', 'medical', 'patient', 'diagnosis', 'treatment', 'prescription', 'hospital']
}

def init_system():
    """Initialize system directories and files"""
    base_dirs = ['uploads'] + list(DOMAIN_CATEGORIES.keys()) + ['general']
    for dir in base_dirs:
        os.makedirs(dir, exist_ok=True)
    
    if not os.path.exists('document_registry.json'):
        with open('document_registry.json', 'w') as f:
            json.dump([], f)

def extract_text_from_image(image):
    """Extract text from an image using Tesseract OCR"""
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
        return text
    except Exception as e:
        st.error(f"Image text extraction error: {e}")
        return ""

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded file (PDF or Image)"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            images = pdf2image.convert_from_bytes(uploaded_file.read())
            text = ""
            for image in images:
                text += extract_text_from_image(image) + "\n"
        else:
            image_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            image = Image.open(io.BytesIO(image_bytes))
            text = extract_text_from_image(image)
        
        return text.strip()
    except Exception as e:
        st.error(f"File processing error: {e}")
        return ""

def determine_domain(text):
    """Determine the document domain based on content analysis"""
    if not text:
        return 'general'
    
    text_lower = text.lower()
    domain_scores = {}
    
    for domain, keywords in DOMAIN_CATEGORIES.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        domain_scores[domain] = score
    
    max_score = max(domain_scores.values())
    if max_score > 0:
        return max(domain_scores.items(), key=lambda x: x[1])[0]
    return 'general'

def generate_summary(text):
    """Generate a concise summary of the document"""
    if not text:
        return "No text available for summarization"
    
    try:
        prompt = """
        Please provide a concise summary of the following document, including:
        1. Main purpose/topic (1-2 sentences)
        2. Key points (3-5 bullet points)
        3. Important dates or deadlines
        4. Action items (if any)
        
        Document text:
        {text}
        """
        
        response = model.generate_content(prompt.format(text=text))
        return response.text if response.text else "Summary generation failed"
    except Exception as e:
        st.error(f"Summary generation error: {e}")
        return "Summary generation failed"

def analyze_with_gemini(text, domain):
    """Enhanced document analysis using Gemini AI"""
    if not text:
        return "No text available for analysis"
    
    try:
        prompt = f"""
        Provide a detailed analysis of this {domain} document, including:
        1. Document type and purpose
        2. Key information extraction:
           - Dates and deadlines
           - Financial amounts (if any)
           - Names and roles
           - Contact information
        3. Main topics covered
        4. Critical points and implications
        5. Recommendations or next steps
        6. Risk factors or concerns (if any)
        
        Document text:
        {text}
        """
        
        response = model.generate_content(prompt)
        return response.text if response.text else "Analysis failed"
    except Exception as e:
        st.error(f"Analysis error: {e}")
        return "Analysis failed"

def save_document(uploaded_file, text, domain, analysis, summary):
    """Save document and its metadata"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_dir = Path(domain)
        domain_dir.mkdir(exist_ok=True)
        
        file_path = domain_dir / f"{timestamp}_{uploaded_file.name}"
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        doc_entry = {
            'filename': uploaded_file.name,
            'domain': domain,
            'processed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'file_path': str(file_path),
            'analysis': analysis,
            'summary': summary,
            'text_content': text  # Store extracted text for potential reprocessing
        }
        
        with open('document_registry.json', 'r+') as f:
            registry = json.load(f)
            registry.append(doc_entry)
            f.seek(0)
            json.dump(registry, f, indent=4)
            f.truncate()
        
        return True
    except Exception as e:
        st.error(f"Error saving document: {e}")
        return False

def load_documents():
    """Load and validate document registry"""
    try:
        with open('document_registry.json', 'r') as f:
            documents = json.load(f)
        
        # Validate and fix document entries
        valid_documents = []
        for doc in documents:
            if isinstance(doc, dict) and 'filename' in doc:
                if 'domain' not in doc:
                    doc['domain'] = 'general'
                if 'processed_date' not in doc:
                    doc['processed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                valid_documents.append(doc)
        
        return valid_documents
    except Exception as e:
        st.error(f"Error loading documents: {e}")
        return []

def main():
    st.title("DOCMATRIX")
    st.sidebar.title("Navigation")
    
    if not GOOGLE_API_KEY:
        st.error("Please set up your Google API key in the .env file")
        return
    
    init_system()
    
    page = st.sidebar.radio("Select Page", ["Upload & Analyze", "View Documents", "Generate Reports"])
    
    if page == "Upload & Analyze":
        st.header("Document Upload and Analysis")
        
        uploaded_file = st.file_uploader("Choose a document", type=['pdf', 'png', 'jpg', 'jpeg'])
        
        if uploaded_file:
            try:
                if uploaded_file.type.startswith('image'):
                    st.image(uploaded_file, caption="Uploaded Document", use_container_width=True)
                else:
                    st.write(f"Uploaded: {uploaded_file.name}")
                
                if st.button("Process Document"):
                    with st.spinner("Processing document..."):
                        text = extract_text_from_file(uploaded_file)
                        
                        if text:
                            with st.expander("View Extracted Text"):
                                st.text(text)
                            
                            domain = determine_domain(text)
                            st.info(f"Detected Domain: {domain.title()}")
                            
                            st.subheader("Document Summary")
                            summary = generate_summary(text)
                            st.markdown(summary)
                            
                            st.subheader("Detailed Analysis")
                            analysis = analyze_with_gemini(text, domain)
                            st.markdown(analysis)
                            
                            if save_document(uploaded_file, text, domain, analysis, summary):
                                st.success("Document processed and saved successfully!")
                            else:
                                st.error("Failed to save document")
                        else:
                            st.error("No text could be extracted from the document.")
                
            except Exception as e:
                st.error(f"Error processing document: {str(e)}")
    
    elif page == "View Documents":
        st.header("Document Repository")
        documents = load_documents()
        
        if documents:
            # Get unique domains including 'general'
            unique_domains = {'All'} | {doc.get('domain', 'general') for doc in documents}
            selected_domain = st.selectbox("Filter by Domain", sorted(list(unique_domains)))
            
            filtered_docs = documents if selected_domain == 'All' else [
                doc for doc in documents if doc.get('domain', 'general') == selected_domain
            ]
            
            for doc in filtered_docs:
                with st.expander(f"{doc['filename']} - {doc.get('domain', 'general').title()} - {doc.get('processed_date', 'Date N/A')}"):
                    if doc.get('summary'):
                        st.subheader("Summary")
                        st.markdown(doc['summary'])
                    if doc.get('analysis'):
                        st.subheader("Detailed Analysis")
                        st.markdown(doc['analysis'])
        else:
            st.info("No documents have been processed yet.")
    
    else:  # Generate Reports
        st.header("Generate Reports")
        documents = load_documents()
        
        if documents:
            report_type = st.selectbox("Select Report Type", 
                                     ["Domain Distribution", "Timeline Analysis"])
            
            if report_type == "Domain Distribution":
                domains = [doc.get('domain', 'general') for doc in documents]
                domain_counts = pd.Series(domains).value_counts().reset_index()
                domain_counts.columns = ['Domain', 'Count']
                
                st.subheader("Document Distribution by Domain")
                st.bar_chart(domain_counts.set_index('Domain'))
                st.dataframe(domain_counts)
            
            elif report_type == "Timeline Analysis":
                timeline_data = pd.DataFrame([{
                    'date': datetime.strptime(doc.get('processed_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                           "%Y-%m-%d %H:%M:%S"),
                    'domain': doc.get('domain', 'general')
                } for doc in documents])
                
                st.subheader("Documents Processed Over Time")
                daily_counts = timeline_data.groupby('date').size()
                st.line_chart(daily_counts)
                
                st.subheader("Processing Statistics")
                st.write(f"Total documents: {len(documents)}")
                st.write(f"First document: {timeline_data['date'].min()}")
                st.write(f"Last document: {timeline_data['date'].max()}")
        else:
            st.info("No documents available for reporting.")

if __name__ == "__main__":
    main()
