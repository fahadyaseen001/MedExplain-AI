# MedExplain AI - Medical Report Assistant 🩺

An AI-powered tool that helps users understand medical reports, test results, and clinical documents using natural language processing.

## Features

- 📄 Support for multiple document formats (PDF, DOCX, PNG, JPG)
- 🔍 Intelligent text extraction with OCR capabilities
- 💬 Interactive chat interface for asking questions
- 🔒 HIPAA-aware design with no data retention
- ⚡ Powered by DeepSeek-R1 language model

## Prerequisites

- Python 3.8+
- Together AI API key
- Tesseract OCR installed

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/medexplain-ai.git
cd medexplain-ai
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
- Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

## Usage

1. Get your API key from [Together AI](https://together.ai)
2. Run the Streamlit app:
```bash
streamlit run app.py
```
3. Enter your Together AI API key in the sidebar
4. Upload a medical document
5. Start asking questions about your report

## Security & Privacy

- No data is stored or retained
- Document processing is encrypted
- Local processing where possible
- API communications are secured

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for informational purposes only and does not replace professional medical advice. Always consult with healthcare professionals for medical decisions.
