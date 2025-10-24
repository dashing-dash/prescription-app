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
    common_dosages: List[str] = []

class PrescriptionMedicine(BaseModel):
    name: str
    dosage: str
    frequency: str

class Prescription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_name: str
    patient_age: Optional[int] = None
    date: str
    medicines: List[PrescriptionMedicine]
    doctor_notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PrescriptionCreate(BaseModel):
    patient_name: str
    patient_age: Optional[int] = None
    date: str
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

# Initialize database with doctor and medicines
async def init_db():
    # Create doctor if not exists
    doctor = await db.users.find_one({"username": "doctor"})
    if not doctor:
        hashed_pwd = get_password_hash("doctor123")
        doctor_data = {
            "id": str(uuid.uuid4()),
            "username": "doctor",
            "name": "Dr. Sanjeev Maheshwari",
            "hashed_password": hashed_pwd
        }
        await db.users.insert_one(doctor_data)
    
    # Add medicines if collection is empty
    count = await db.medicines.count_documents({})
    if count == 0:
        medicines = [
            {"id": str(uuid.uuid4()), "name": "Paracetamol", "common_dosages": ["500mg", "650mg", "1000mg"]},
            {"id": str(uuid.uuid4()), "name": "Ibuprofen", "common_dosages": ["200mg", "400mg", "600mg"]},
            {"id": str(uuid.uuid4()), "name": "Amoxicillin", "common_dosages": ["250mg", "500mg"]},
            {"id": str(uuid.uuid4()), "name": "Azithromycin", "common_dosages": ["250mg", "500mg"]},
            {"id": str(uuid.uuid4()), "name": "Ciprofloxacin", "common_dosages": ["250mg", "500mg", "750mg"]},
            {"id": str(uuid.uuid4()), "name": "Omeprazole", "common_dosages": ["20mg", "40mg"]},
            {"id": str(uuid.uuid4()), "name": "Metformin", "common_dosages": ["500mg", "850mg", "1000mg"]},
            {"id": str(uuid.uuid4()), "name": "Atorvastatin", "common_dosages": ["10mg", "20mg", "40mg"]},
            {"id": str(uuid.uuid4()), "name": "Losartan", "common_dosages": ["25mg", "50mg", "100mg"]},
            {"id": str(uuid.uuid4()), "name": "Amlodipine", "common_dosages": ["2.5mg", "5mg", "10mg"]},
            {"id": str(uuid.uuid4()), "name": "Levothyroxine", "common_dosages": ["25mcg", "50mcg", "100mcg"]},
            {"id": str(uuid.uuid4()), "name": "Cetirizine", "common_dosages": ["5mg", "10mg"]},
            {"id": str(uuid.uuid4()), "name": "Montelukast", "common_dosages": ["5mg", "10mg"]},
            {"id": str(uuid.uuid4()), "name": "Pantoprazole", "common_dosages": ["20mg", "40mg"]},
            {"id": str(uuid.uuid4()), "name": "Clopidogrel", "common_dosages": ["75mg"]},
            {"id": str(uuid.uuid4()), "name": "Aspirin", "common_dosages": ["75mg", "150mg", "325mg"]},
            {"id": str(uuid.uuid4()), "name": "Diclofenac", "common_dosages": ["50mg", "75mg"]},
            {"id": str(uuid.uuid4()), "name": "Ranitidine", "common_dosages": ["150mg", "300mg"]},
            {"id": str(uuid.uuid4()), "name": "Prednisolone", "common_dosages": ["5mg", "10mg", "20mg"]},
            {"id": str(uuid.uuid4()), "name": "Vitamin D3", "common_dosages": ["1000 IU", "2000 IU", "60000 IU"]},
        ]
        await db.medicines.insert_many(medicines)

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
        medicines = await db.medicines.find({}, {"_id": 0}).limit(20).to_list(20)
    else:
        medicines = await db.medicines.find(
            {"name": {"$regex": q, "$options": "i"}},
            {"_id": 0}
        ).limit(20).to_list(20)
    return medicines

@api_router.post("/prescriptions", response_model=Prescription)
async def create_prescription(prescription: PrescriptionCreate, _: str = Depends(get_current_user)):
    prescription_obj = Prescription(**prescription.model_dump())
    doc = prescription_obj.model_dump()
    await db.prescriptions.insert_one(doc)
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

@api_router.get("/prescriptions/{prescription_id}/pdf")
async def download_prescription_pdf(prescription_id: str, _: str = Depends(get_current_user)):
    prescription = await db.prescriptions.find_one({"id": prescription_id}, {"_id": 0})
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=50, bottomMargin=50)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1e40af'),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    subheader_style = ParagraphStyle(
        'CustomSubHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    # Header
    story.append(Paragraph("Dr. Sanjeev Maheshwari", header_style))
    story.append(Paragraph("MBBS, MD (Medicine)", subheader_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Patient Info
    story.append(Paragraph("<b>Prescription</b>", section_header_style))
    
    patient_data = [
        ['Patient Name:', prescription['patient_name']],
        ['Date:', prescription['date']]
    ]
    if prescription.get('patient_age'):
        patient_data.insert(1, ['Age:', str(prescription['patient_age'])])
    
    patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Medicines
    story.append(Paragraph("<b>Rx</b>", section_header_style))
    
    medicine_data = [['Medicine', 'Dosage', 'Frequency']]
    for med in prescription['medicines']:
        medicine_data.append([med['name'], med['dosage'], med['frequency']])
    
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
    
    # Signature
    story.append(Spacer(1, 0.5*inch))
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT
    )
    story.append(Paragraph("<b>Dr. Sanjeev Maheshwari</b>", signature_style))
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=prescription_{prescription_id}.pdf"}
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