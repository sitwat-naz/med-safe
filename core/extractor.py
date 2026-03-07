import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import base64
from pypdf import PdfReader

load_dotenv()

# Initialize Groq (Free!)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

def extract_from_pdf(file_path):
    """Extract text from PDF medical report"""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_from_image(image_path):
    """Extract text from handwritten or printed image using Groq Vision"""
    import base64
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    ext = image_path.split(".")[-1].lower()
    mime_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"

    vision_llm = ChatGroq(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        api_key=os.getenv("GROQ_API_KEY")
    )

    message = HumanMessage(content=[
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{image_data}"
            }
        },
        {
            "type": "text",
            "text": """You are a medical document reader.
            Carefully read this handwritten or printed medical prescription/report.
            Extract ALL readable information including:
            - Patient name and date
            - Symptoms or diagnosis mentioned
            - All medications with dosage and frequency
            - Any lab values or test results
            - Doctor name and hospital
            Write out everything you can read clearly."""
        }
    ])

    response = vision_llm.invoke([message])
    return response.content

def parse_medical_data(raw_text):
    """Use Groq to convert raw text into structured JSON"""
    prompt = f"""
    You are a medical data extraction expert.
    From the following medical report text, extract and return ONLY a JSON object with this structure:
    {{
        "patient_name": "",
        "report_date": "",
        "lab_results": [
            {{
                "test_name": "",
                "value": "",
                "unit": "",
                "reference_range": ""
            }}
        ],
        "medications": [
            {{
                "name": "",
                "dosage": "",
                "frequency": ""
            }}
        ]
    }}
    
    Medical Report Text:
    {raw_text}
    
    Return ONLY the JSON. No explanation.
    """
    
    response = llm.invoke(prompt)
    return response.content

def process_report(file_path):
    """Main function - handles both PDF and image"""
    ext = file_path.split(".")[-1].lower()
    
    if ext == "pdf":
        raw_text = extract_from_pdf(file_path)
    elif ext in ["jpg", "jpeg", "png"]:
        raw_text = extract_from_image(file_path)
    else:
        return "Unsupported file format"
    
    structured_data = parse_medical_data(raw_text)
    return structured_data, raw_text