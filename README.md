DOCMATRIX

DOCMATRIX is a powerful Streamlit-based document processing and analysis tool. It leverages OCR (Optical Character Recognition) using Tesseract, document classification, and Google Gemini AI for detailed analysis and summarization.

🚀 Features

- 📄 Document Upload: Supports PDF and image uploads.
- 🔍 OCR Integration: Extracts text using Tesseract OCR.
- 🧠 Content Analysis: Uses Google Gemini AI for:
  - Detailed document analysis
  - Content summarization
- 🏷 Domain Classification: Categorizes documents into domains like Finance, Education, Legal, Technical, and Medical.
- 💾 Document Management: Saves documents with metadata and categorizes them.
- 📊 Reporting:
  - Domain distribution
  - Timeline analysis

📂 Folder Structure

```
DOCMATRIX/
├── app.py                   Main Streamlit app
├── uploads/                 Uploaded documents
├── document_registry.json   Registry for processed documents
├── .env                     Environment variables (API keys)
├── requirements.txt         Python dependencies
└── README.md                Project documentation
```

⚙️ Setup Instructions

1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/docmatrix.git
cd docmatrix
```

2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

3️⃣ Configure Environment Variables

Create a `.env` file in the root directory:

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

4️⃣ Run the App

```bash
streamlit run app.py
```

📋 Usage

1. Upload & Analyze
   - Upload PDFs or images.
   - Extract text and classify documents.
   - View summaries and detailed analyses.

2. View Documents
   - Browse processed documents.
   - Filter by domain.

3. Generate Reports
   - Analyze document trends and distributions.

🔑 API Integration

- Google Gemini AI
  - Used for document summarization and analysis.
  - Set up using the `GOOGLE_API_KEY` in the `.env` file.

🛠 Dependencies

- streamlit
- pytesseract
- Pillow
- google-generativeai
- pdf2image
- python-dotenv
- shutil
- pandas

🧹 Troubleshooting

- Tesseract not found?
  - Ensure Tesseract is installed and added to your PATH.
  - On Ubuntu:
    ```bash
    sudo apt install tesseract-ocr
    ```

- Google API issues?
  - Double-check your `GOOGLE_API_KEY` in `.env`.

🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a pull request

📜 License

This project is licensed under the MIT License.

---

💡 "Simplifying document analysis with AI."

