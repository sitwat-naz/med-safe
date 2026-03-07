# 🏥 Med-Safe: Medical Report Interpretation & Verification System

## Overview
Med-Safe is an AI-powered system that reads medical reports 
(PDFs and handwritten images), extracts clinical data, detects 
abnormalities, verifies medications, and generates summaries 
for both patients and healthcare professionals.

## Features
- 📄 PDF medical report reading
- 🖼️ Handwritten prescription reading (image support)
- 🔬 Abnormality detection with severity classification
- 💊 Medication verification
- 👤 Patient-friendly summaries
- 👨‍⚕️ Clinical physician briefs
- ⚠️ Safety disclaimers and hallucination reduction

## Tech Stack
- Python
- Streamlit (UI)
- LangChain (orchestration)
- Groq API - LLaMA 3.3 (text reasoning)
- LLaMA 4 Scout (vision/image reading)
- PyPDF (PDF parsing)

## How to Run

### 1. Clone the repository
git clone https://github.com/yourusername/med-safe.git
cd med-safe

### 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Add API keys
Create a .env file:
GROQ_API_KEY=your_groq_key_here

### 5. Run the app
streamlit run app.py

## Project Structure
med_safe/
├── app.py           # Streamlit UI
├── extractor.py     # PDF/Image parsing
├── tools.py         # Abnormality + Drug verification
├── summarizer.py    # Summary generation
├── requirements.txt
└── README.md

## Disclaimer
Med-Safe is an AI-powered assistant and does NOT replace 
professional medical advice. Always consult a qualified 
healthcare professional.

## Developer
Sitwat Naz
AI Bootcamp — Atomcamp