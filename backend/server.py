from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    name: str
    hashed_password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    name: str

class Medicine(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    dosage: str
    frequency: str
    unique_key: str

class PrescriptionMedicine(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: str

class Prescription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_name: str
    patient_age: Optional[int] = None
    date: str
    diagnosis: Optional[str] = None
    investigations: Optional[str] = None
    medicines: List[PrescriptionMedicine]
    doctor_notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DiagnosisInvestigation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    diagnosis: str
    investigations: str
    unique_key: str

class PrescriptionCreate(BaseModel):
    patient_name: str
    patient_age: Optional[int] = None
    date: str
    diagnosis: Optional[str] = None
    investigations: Optional[str] = None
    medicines: List[PrescriptionMedicine]
    doctor_notes: Optional[str] = None

# Helper Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def create_medicine_key(name: str, dosage: str, frequency: str) -> str:
    """Create unique key for medicine combination"""
    return f"{name.lower().strip()}_{dosage.lower().strip()}_{frequency.lower().strip()}"

def create_diagnosis_investigation_key(diagnosis: str, investigations: str) -> str:
    """Create unique key for diagnosis and investigation combination"""
    return f"{diagnosis.lower().strip()}_{investigations.lower().strip()}"

# Initialize database with doctor
async def init_db():
    # Create doctor if not exists
    doctor = await db.users.find_one({"username": "doctor"})
    if not doctor:
        hashed_pwd = get_password_hash("doctor123")
        doctor_data = {
            "id": str(uuid.uuid4()),
            "username": "doctor",
            "name": "Dr. Sanjiv Maheshwari",
            "hashed_password": hashed_pwd
        }
        await db.users.insert_one(doctor_data)
    
    # Clear pre-seeded medicines
    # await db.medicines.delete_many({})

@app.on_event("startup")
async def startup_event():
    await init_db()

# Routes
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = await db.users.find_one({"username": request.username}, {"_id": 0})
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token(data={"sub": user["username"]})
    return LoginResponse(token=token, name=user["name"])

@api_router.get("/medicines/search")
async def search_medicines(q: str = "", _: str = Depends(get_current_user)):
    if not q:
        medicines = await db.medicines.find({}, {"_id": 0}).limit(50).to_list(50)
    else:
        # Search across name, dosage, and frequency
        medicines = await db.medicines.find(
            {
                "$or": [
                    {"name": {"$regex": q, "$options": "i"}},
                    {"dosage": {"$regex": q, "$options": "i"}},
                    {"frequency": {"$regex": q, "$options": "i"}}
                ]
            },
            {"_id": 0}
        ).limit(50).to_list(50)
    return medicines

@api_router.get("/patients/search")
async def search_patients(q: str = "", _: str = Depends(get_current_user)):
    if not q:
        patients = await db.patients.find({}, {"_id": 0}).limit(50).to_list(50)
    else:
        # Search by patient name
        patients = await db.patients.find(
            {"name": {"$regex": q, "$options": "i"}},
            {"_id": 0}
        ).limit(50).to_list(50)
    return patients

@api_router.get("/investigations/search")
async def search_investigations(q: str = "", _: str = Depends(get_current_user)):
    if not q:
        investigations = await db.investigations.find({}, {"_id": 0}).limit(50).to_list(50)
    else:
        # Search by investigation name
        investigations = await db.investigations.find(
            {"name": {"$regex": q, "$options": "i"}},
            {"_id": 0}
        ).limit(50).to_list(50)
    return investigations

@api_router.get("/diagnosis-investigations/search")
async def search_diagnosis_investigations(q: str = "", _: str = Depends(get_current_user)):
    if not q:
        results = await db.diagnosis_investigations.find({}, {"_id": 0}).limit(50).to_list(50)
    else:
        results = await db.diagnosis_investigations.find(
            {
                "$or": [
                    {"diagnosis": {"$regex": q, "$options": "i"}},
                    {"investigations": {"$regex": q, "$options": "i"}}
                ]
            },
            {"_id": 0}
        ).limit(50).to_list(50)
    return results

class InvestigationCreate(BaseModel):
    name: str

class DiagnosisInvestigationCreate(BaseModel):
    diagnosis: str
    investigations: str

@api_router.post("/investigations/save")
async def save_investigation(investigation: InvestigationCreate, _: str = Depends(get_current_user)):
    """Save a new investigation if it doesn't exist"""
    investigation_key = investigation.name.lower().strip()
    
    # Check if this investigation already exists
    existing = await db.investigations.find_one({"unique_key": investigation_key})
    if existing:
        return {"message": "Investigation already exists", "id": existing["id"]}
    
    # Save new investigation
    investigation_doc = {
        "id": str(uuid.uuid4()),
        "name": investigation.name.strip(),
        "unique_key": investigation_key
    }
    await db.investigations.insert_one(investigation_doc)
    return {"message": "Investigation saved", "id": investigation_doc["id"]}

@api_router.post("/diagnosis-investigations/save")
async def save_diagnosis_investigation(item: DiagnosisInvestigationCreate, _: str = Depends(get_current_user)):
    """Save a new diagnosis and investigation combination if it doesn't exist"""
    unique_key = create_diagnosis_investigation_key(item.diagnosis, item.investigations)
    
    existing = await db.diagnosis_investigations.find_one({"unique_key": unique_key})
    if existing:
        return {"message": "Diagnosis/Investigation combination already exists", "id": existing["id"]}
    
    doc = {
        "id": str(uuid.uuid4()),
        "diagnosis": item.diagnosis,
        "investigations": item.investigations,
        "unique_key": unique_key
    }
    await db.diagnosis_investigations.insert_one(doc)
    return {"message": "Diagnosis/Investigation combination saved", "id": doc["id"]}

@api_router.post("/medicines/save")
async def save_medicine(medicine: PrescriptionMedicine, _: str = Depends(get_current_user)):
    """Save a new medicine combination if it doesn't exist"""
    unique_key = create_medicine_key(medicine.name, medicine.dosage, medicine.frequency)
    
    # Check if this combination already exists
    existing = await db.medicines.find_one({"unique_key": unique_key})
    if existing:
        return {"message": "Medicine combination already exists", "id": existing["id"]}
    
    # Save new medicine combination
    medicine_doc = {
        "id": str(uuid.uuid4()),
        "name": medicine.name,
        "dosage": medicine.dosage,
        "frequency": medicine.frequency,
        "unique_key": unique_key
    }
    await db.medicines.insert_one(medicine_doc)
    return {"message": "Medicine combination saved", "id": medicine_doc["id"]}

@api_router.post("/prescriptions", response_model=Prescription)
async def create_prescription(prescription: PrescriptionCreate, _: str = Depends(get_current_user)):
    prescription_obj = Prescription(**prescription.model_dump())
    doc = prescription_obj.model_dump()
    await db.prescriptions.insert_one(doc)
    
    # Auto-save patient (name + age combination)
    patient_key = f"{prescription.patient_name.lower().strip()}_{prescription.patient_age if prescription.patient_age else 'unknown'}"
    existing_patient = await db.patients.find_one({"unique_key": patient_key})
    if not existing_patient:
        patient_doc = {
            "id": str(uuid.uuid4()),
            "name": prescription.patient_name,
            "age": prescription.patient_age,
            "unique_key": patient_key
        }
        await db.patients.insert_one(patient_doc)
    
    # Auto-save diagnosis and investigation if provided
    if prescription.diagnosis and prescription.diagnosis.strip() and prescription.investigations and prescription.investigations.strip():
        unique_key = create_diagnosis_investigation_key(prescription.diagnosis, prescription.investigations)
        existing_di = await db.diagnosis_investigations.find_one({"unique_key": unique_key})
        if not existing_di:
            di_doc = {
                "id": str(uuid.uuid4()),
                "diagnosis": prescription.diagnosis,
                "investigations": prescription.investigations,
                "unique_key": unique_key
            }
            await db.diagnosis_investigations.insert_one(di_doc)

    # Auto-save investigation if provided
    if prescription.investigations and prescription.investigations.strip():
        investigation_key = prescription.investigations.lower().strip()
        existing_investigation = await db.investigations.find_one({"unique_key": investigation_key})
        if not existing_investigation:
            investigation_doc = {
                "id": str(uuid.uuid4()),
                "name": prescription.investigations.strip(),
                "unique_key": investigation_key
            }
            await db.investigations.insert_one(investigation_doc)
    
    # Auto-save all medicine combinations
    for med in prescription.medicines:
        # Only create unique key if dosage is provided
        if med.dosage:
            unique_key = create_medicine_key(med.name, med.dosage, med.frequency)
        else:
            unique_key = f"{med.name.lower().strip()}_{med.frequency.lower().strip()}_nodosage"
        
        existing = await db.medicines.find_one({"unique_key": unique_key})
        if not existing:
            medicine_doc = {
                "id": str(uuid.uuid4()),
                "name": med.name,
                "dosage": med.dosage if med.dosage else "",
                "frequency": med.frequency,
                "unique_key": unique_key
            }
            await db.medicines.insert_one(medicine_doc)
    
    return prescription_obj

@api_router.get("/prescriptions", response_model=List[Prescription])
async def get_prescriptions(patient_name: Optional[str] = None, _: str = Depends(get_current_user)):
    query = {}
    if patient_name:
        query["patient_name"] = {"$regex": patient_name, "$options": "i"}
    
    prescriptions = await db.prescriptions.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return prescriptions

@api_router.get("/prescriptions/{prescription_id}", response_model=Prescription)
async def get_prescription(prescription_id: str, _: str = Depends(get_current_user)):
    prescription = await db.prescriptions.find_one({"id": prescription_id}, {"_id": 0})
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription

@api_router.delete("/prescriptions/{prescription_id}")
async def delete_prescription(prescription_id: str, _: str = Depends(get_current_user)):
    result = await db.prescriptions.delete_one({"id": prescription_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return {"message": "Prescription deleted successfully"}

@api_router.get("/medicines", response_model=List[Medicine])
async def get_all_medicines(_: str = Depends(get_current_user)):
    medicines = await db.medicines.find({}, {"_id": 0}).sort("name", 1).to_list(1000)
    return medicines

@api_router.delete("/medicines/{medicine_id}")
async def delete_medicine(medicine_id: str, _: str = Depends(get_current_user)):
    result = await db.medicines.delete_one({"id": medicine_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return {"message": "Medicine deleted successfully"}

@api_router.get("/prescriptions/{prescription_id}/pdf")
async def download_prescription_pdf(prescription_id: str, inline: bool = True, token: str = None):
    # Try to get token from query parameter or header
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    prescription = await db.prescriptions.find_one({"id": prescription_id}, {"_id": 0})
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # Create PDF with extra margins for pre-printed letterhead
    buffer = io.BytesIO()
    # Increased top and bottom margins to leave space for pre-printed header/footer
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=120, bottomMargin=100)
    
    # Register Hindi font - Using Nakula for proper Unicode Devanagari rendering
    try:
        font_path = os.path.join(ROOT_DIR, 'fonts', 'nakula.ttf')
        pdfmetrics.registerFont(TTFont('Nakula', font_path))
        hindi_font = 'Nakula'
    except Exception as e:
        logger.error(f"Failed to load Hindi font: {e}")
        hindi_font = 'Helvetica'  # Fallback
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    # NO HEADER - Will be on pre-printed letterhead
    # Start directly with prescription content
    
    # Patient Info
    story.append(Paragraph("<b>Prescription</b>", section_header_style))
    
    # Single line for name, age, date
    patient_info_parts = [f"Patient Name: {prescription['patient_name']}"]
    if prescription.get('patient_age'):
        patient_info_parts.append(f"Age: {prescription['patient_age']}")
    patient_info_parts.append(f"Date: {prescription['date']}")
    
    patient_info_line = " | ".join(patient_info_parts)
    story.append(Paragraph(patient_info_line, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    # Diagnosis and Investigations
    if prescription.get('diagnosis'):
        story.append(Paragraph(f"<b>Diagnosis:</b> {prescription['diagnosis']}", styles['Normal']))
        story.append(Spacer(1, 0.05*inch))
    
    if prescription.get('investigations'):
        story.append(Paragraph(f"<b>Investigations Advised:</b> {prescription['investigations']}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Medicines
    story.append(Paragraph("<b>Rx</b>", section_header_style))
    
    medicine_data = [['Medicine', 'Dosage', 'Frequency']]
    for med in prescription['medicines']:
        medicine_data.append([
            med['name'],
            med.get('dosage', '-') if med.get('dosage') else '-',
            med['frequency']
        ])
    
    medicine_table = Table(medicine_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
    medicine_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e7ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(medicine_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Notes
    if prescription.get('doctor_notes'):
        story.append(Paragraph("<b>Notes</b>", section_header_style))
        story.append(Paragraph(prescription['doctor_notes'], styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
    
    # NO FOOTER OR SIGNATURE - Will be on pre-printed letterhead
    
    doc.build(story)
    buffer.seek(0)
    
    # Return inline for viewing in browser, or attachment for download
    disposition = "inline" if inline else "attachment"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="prescription_{prescription_id}.pdf"',
            "Cache-Control": "no-cache"
        }
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()