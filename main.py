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

# Configure Gemini API
# Store your API key in .env file
from dotenv import load_dotenv
load_dotenv()

# Set your Gemini API key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Select Gemini model
model = genai.GenerativeModel('gemini-pro')

# For Windows users, set Tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def init_system():
    """Initialize system directories and files"""
    directories = ['uploads', 'processed', 'invoices', 'contracts', 'others']
    for dir in directories:
        os.makedirs(dir, exist_ok=True)
    
    if not os.path.exists('document_registry.json'):
        with open('document_registry.json', 'w') as f:
            json.dump([], f)

def extract_text_from_file(uploaded_file):
    """Extract text using Tesseract OCR"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            # Convert PDF to images
            images = pdf2image.convert_from_bytes(uploaded_file.read())
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
        else:
            # Handle image files
            image_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            text = pytesseract.image_to_string(image)
        
        return text
    except Exception as e:
        st.error(f"Error in text extraction: {e}")
        return ""

def analyze_with_gemini(text):
    """Analyze document content using Gemini AI"""
    try:
        # Prompt for Gemini to analyze the document
        prompt = f"""
        Analyze the following document text and provide a structured analysis including:
        1. Document type/category
        2. Key information (dates, amounts, names, email addresses)
        3. Main topics or subjects discussed
        4. Important entities mentioned (companies, people, locations)
        5. Any action items or important deadlines
        
        Document text:
        {text}
        
        Provide the analysis in a clear, structured format.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error in Gemini analysis: {e}")
        return "Analysis failed"

def main():
    st.title("Smart Document Management System")
    st.sidebar.title("Navigation")
    
    # Check for API key
    if not GOOGLE_API_KEY:
        st.error("""
        Please set up your Google API key:
        1. Create a .env file in your project directory
        2. Add this line: GOOGLE_API_KEY=your_api_key_here
        3. Get your API key from: https://makersuite.google.com/app/apikey
        """)
        return
    
    # Initialize system
    init_system()
    
    # Navigation
    page = st.sidebar.radio("Select Page", ["Upload & Analyze", "View Documents"])
    
    if page == "Upload & Analyze":
        st.header("Document Upload and Analysis")
        
        uploaded_file = st.file_uploader("Choose a document", type=['pdf', 'png', 'jpg', 'jpeg'])
        
        if uploaded_file:
            try:
                # Display uploaded file
                if uploaded_file.type.startswith('image'):
                    st.image(uploaded_file, caption="Uploaded Document", use_container_width=True)
                else:
                    st.write(f"Uploaded: {uploaded_file.name}")
                
                # Process button
                if st.button("Analyze Document"):
                    with st.spinner("Processing document..."):
                        # Extract text using Tesseract
                        text = extract_text_from_file(uploaded_file)
                        
                        if text.strip():
                            # Show extracted text
                            with st.expander("View Extracted Text"):
                                st.text(text)
                            
                            # Analyze with Gemini
                            st.subheader("AI Analysis Results")
                            with st.spinner("Analyzing with AI..."):
                                analysis = analyze_with_gemini(text)
                                st.markdown(analysis)
                            
                            # Save results
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            doc_entry = {
                                'filename': uploaded_file.name,
                                'processed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'analysis': analysis
                            }
                            
                            # Update registry
                            with open('document_registry.json', 'r+') as f:
                                registry = json.load(f)
                                registry.append(doc_entry)
                                f.seek(0)
                                json.dump(registry, f, indent=4)
                            
                            st.success("Document processed and analyzed successfully!")
                        else:
                            st.error("No text could be extracted from the document.")
                
            except Exception as e:
                st.error(f"Error processing document: {e}")
    
    else:  # View Documents page
        st.header("Document Repository")
        
        try:
            with open('document_registry.json', 'r') as f:
                documents = json.load(f)
            
            if documents:
                for doc in documents:
                    with st.expander(f"{doc['filename']} - {doc['processed_date']}"):
                        st.markdown(doc['analysis'])
            else:
                st.info("No documents have been processed yet.")
                
        except Exception as e:
            st.error(f"Error loading documents: {e}")

if __name__ == "__main__":
    main()