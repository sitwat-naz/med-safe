import os
import base64
import random
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pypdf import PdfReader

load_dotenv()

def get_llm():
    keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY_4"),
        os.getenv("GROQ_API_KEY"),  # fallback to single key
    ]
    keys = [k for k in keys if k]  # remove empty
    if not keys:
        raise ValueError("No Groq API key found!")
    key = random.choice(keys)
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=key
    )

def get_vision_key():
    keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY_4"),
    ]
    keys = [k for k in keys if k]
    return random.choice(keys)

REPORT_TYPES = {
    "lab": [
        "cbc", "blood", "urine", "complete blood count",
        "hemoglobin", "glucose", "cholesterol", "lipid",
        "thyroid", "liver", "kidney", "metabolic", "hba1c",
        "electrolyte", "creatinine", "bilirubin", "platelet",
        "wbc", "rbc", "culture", "sensitivity", "stool",
        "amylase", "lipase", "enzyme", "panel", "profile",
        "calcium", "sodium", "potassium", "vitamin",
        "iron", "ferritin", "albumin", "protein", "uric acid",
        "esr", "crp", "troponin", "d-dimer", "inr", "psa"
    ],
    "descriptive": [
        "ct scan", "computed tomography",
        "x-ray", "xray", "x ray", "chest pa",
        "mri", "magnetic resonance",
        "ultrasound", "sonography", "usg",
        "echocardiogram", "endoscopy",
        "colonoscopy", "biopsy", "pathology", "radiology",
        "mammogram", "bone density", "dexa", "pet scan",
        "angiography", "doppler", "eeg"
    ],
    "prescription": [
        "prescription", "rx", "medicine", "prescribed",
        "tablet", "capsule", "syrup", "injection", "dose"
    ]
}

def detect_report_type(text: str) -> str:
    """Detect if report is lab, descriptive, or prescription"""
    text_lower = text.lower()

    # Check descriptive ONLY with multi-word phrases to avoid
    # false matches (e.g. "ct" alone matching "count")
    for keyword in REPORT_TYPES["descriptive"]:
        if keyword in text_lower:
            return "descriptive"

    # Check lab keywords
    for keyword in REPORT_TYPES["lab"]:
        if keyword in text_lower:
            return "lab"

    # Check prescription
    for keyword in REPORT_TYPES["prescription"]:
        if keyword in text_lower:
            return "prescription"

    return "lab"

def detect_report_title(text: str) -> str:
    """Extract a meaningful title from report text"""
    text_lower = text.lower()

    title_map = {
        "Complete Blood Count (CBC)": ["cbc", "complete blood count"],
        "Blood Sugar / Glucose Test": ["glucose", "blood sugar", "hba1c", "fasting"],
        "Lipid Profile": ["lipid", "cholesterol", "triglyceride"],
        "Thyroid Function Test": ["thyroid", "tsh", "t3", "t4"],
        "Liver Function Test": ["liver", "bilirubin", "alt", "ast", "sgpt", "sgot"],
        "Kidney Function Test": ["kidney", "creatinine", "urea", "gfr"],
        "Urine Analysis": ["urine", "urinalysis"],
        "CT Scan Report": ["ct scan", "computed tomography"],
        "X-Ray Report": ["x-ray", "xray", "x ray", "chest pa"],
        "MRI Report": ["mri", "magnetic resonance"],
        "Ultrasound Report": ["ultrasound", "sonography", "usg"],
        "ECG / EKG Report": ["ecg", "ekg", "electrocardiogram"],
        "Echocardiogram Report": ["echo", "echocardiogram"],
        "Prescription": ["prescription", "rx"],
        "Pathology Report": ["pathology", "biopsy", "histology"],
    }

    for title, keywords in title_map.items():
        for kw in keywords:
            if kw in text_lower:
                return title

    return "Medical Report"

def extract_from_pdf(file_path: str) -> str:
    """Extract text from PDF"""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_from_image(file_path: str) -> str:
    """Extract text from image using LLaMA 4 Scout vision"""
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    ext = file_path.split(".")[-1].lower()
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "gif": "image/gif",
        "webp": "image/webp"
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    from groq import Groq
    client = Groq(api_key=get_vision_key())

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}"
                    }
                },
                {
                    "type": "text",
                    "text": """Please read and transcribe ALL text from this 
                    medical document completely and accurately.
                    Include all test names, values, units, reference ranges,
                    doctor names, patient names, dates, medications, 
                    diagnoses, findings — everything visible.
                    Preserve the original structure as much as possible."""
                }
            ]
        }],
        max_tokens=2000
    )
    return response.choices[0].message.content

def parse_medical_data(raw_text: str) -> str:
    """
    Parse medical data into structured JSON.
    Handles lab reports, descriptive reports, and prescriptions.
    """

    report_type = detect_report_type(raw_text)
    report_title = detect_report_title(raw_text)

    if report_type == "descriptive":
        prompt = f"""
        You are a medical data extraction expert.
        
        This is a DESCRIPTIVE medical report (CT scan, X-ray, MRI, 
        Ultrasound, ECG, or similar imaging/diagnostic report).
        
        Report Text:
        {raw_text}
        
        Extract and return ONLY this JSON structure:
        {{
            "report_type": "descriptive",
            "report_title": "{report_title}",
            "patient_name": "patient name or Unknown",
            "report_date": "date or Unknown",
            "findings": "2-3 sentence plain English summary of key findings",
            "impression": "doctor conclusion or diagnosis if mentioned",
            "medications": []
        }}
        
        Rules:
        - findings must be plain English, max 3 sentences
        - Do NOT create lab_results for descriptive reports
        - Return ONLY JSON, no extra text
        """

    elif report_type == "prescription":
        prompt = f"""
        You are a medical data extraction expert.
        
        This is a PRESCRIPTION or medication record.
        
        Report Text:
        {raw_text}
        
        Extract and return ONLY this JSON structure:
        {{
            "report_type": "prescription",
            "report_title": "Prescription",
            "patient_name": "patient name or Unknown",
            "report_date": "date or Unknown",
            "diagnosis": "diagnosis or condition if mentioned",
            "findings": "brief summary of why medications were prescribed",
            "lab_results": [],
            "medications": [
                {{
                    "name": "medication name",
                    "dosage": "dosage if mentioned",
                    "frequency": "how often",
                    "duration": "for how long"
                }}
            ]
        }}
        
        Return ONLY JSON, no extra text.
        """

    else:
        prompt = f"""
        You are a medical data extraction expert.
        
        This is a LAB REPORT with numeric test results.
        
        Report Text:
        {raw_text}
        
        Extract and return ONLY this JSON structure:
        {{
            "report_type": "lab",
            "report_title": "{report_title}",
            "patient_name": "patient name or Unknown",
            "report_date": "date or Unknown",
            "findings": "",
            "lab_results": [
                {{
                    "test_name": "name",
                    "value": "numeric value",
                    "unit": "unit",
                    "reference_range": "low-high"
                }}
            ],
            "medications": []
        }}
        
        Return ONLY JSON, no extra text.
        """

    response = get_llm().invoke(prompt)
    return response.content

def process_report(file_path: str):
    """Main function - routes by file type and report type"""
    ext = file_path.split(".")[-1].lower()

    if ext == "pdf":
        raw_text = extract_from_pdf(file_path)
    else:
        raw_text = extract_from_image(file_path)

    structured_data = parse_medical_data(raw_text)
    return structured_data, raw_text