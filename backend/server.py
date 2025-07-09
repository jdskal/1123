from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import base64
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="School Admin Panel API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    EDITOR = "editor"

class NewsStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.EDITOR
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.EDITOR

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Content Models
class News(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    excerpt: Optional[str] = None
    image: Optional[str] = None  # base64 encoded
    status: NewsStatus = NewsStatus.DRAFT
    author_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

class NewsCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    image: Optional[str] = None
    status: NewsStatus = NewsStatus.DRAFT

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image: Optional[str] = None
    status: Optional[NewsStatus] = None

class SchoolInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    section: str  # about, history, mission, etc.
    title: str
    content: str
    image: Optional[str] = None
    order: int = 0
    is_active: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SchoolInfoCreate(BaseModel):
    section: str
    title: str
    content: str
    image: Optional[str] = None
    order: int = 0

class SchoolInfoUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None

class Gallery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    image: str  # base64 encoded
    category: str = "general"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GalleryCreate(BaseModel):
    title: str
    description: Optional[str] = None
    image: str
    category: str = "general"

class GalleryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # phone, email, address, etc.
    label: str
    value: str
    is_active: bool = True
    order: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContactCreate(BaseModel):
    type: str
    label: str
    value: str
    order: int = 0

class ContactUpdate(BaseModel):
    label: Optional[str] = None
    value: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

class Schedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    date: datetime
    time: str
    location: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScheduleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: datetime
    time: str
    location: Optional[str] = None

class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    time: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    author_name: str
    author_email: Optional[str] = None
    news_id: str
    is_approved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CommentCreate(BaseModel):
    content: str
    author_name: str
    author_email: Optional[str] = None
    news_id: str

class CommentUpdate(BaseModel):
    is_approved: Optional[bool] = None

class SiteStats(BaseModel):
    total_visits: int = 0
    daily_visits: int = 0
    total_users: int = 0
    total_news: int = 0
    total_comments: int = 0
    pending_comments: int = 0
    date: datetime = Field(default_factory=datetime.utcnow)

# Legacy model for backward compatibility
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    
    return User(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_moderator_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Legacy routes for backward compatibility
@api_router.get("/")
async def root():
    return {"message": "School Admin Panel API"}

@api_router.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint is working"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

# Authentication endpoints
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate, current_user: User = Depends(get_admin_user)):
    """Only admins can register new users"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user_dict.pop("password")
    user_dict["hashed_password"] = hashed_password
    
    user_obj = User(**user_dict)
    await db.users.insert_one(user_obj.dict())
    return user_obj

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user.get("hashed_password")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    access_token = create_access_token(data={"sub": user["email"]})
    user_obj = User(**user)
    return Token(access_token=access_token, token_type="bearer", user=user_obj)

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# User management endpoints
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_admin_user)):
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_data: UserUpdate, current_user: User = Depends(get_admin_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    updated_user = await db.users.find_one({"id": user_id})
    return User(**updated_user)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_admin_user)):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# News management endpoints
@api_router.post("/news", response_model=News)
async def create_news(news_data: NewsCreate, current_user: User = Depends(get_current_user)):
    news_dict = news_data.dict()
    news_dict["author_id"] = current_user.id
    
    if news_data.status == NewsStatus.PUBLISHED:
        news_dict["published_at"] = datetime.utcnow()
    
    news_obj = News(**news_dict)
    await db.news.insert_one(news_obj.dict())
    return news_obj

@api_router.get("/news", response_model=List[News])
async def get_news(
    status: Optional[NewsStatus] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    
    news_list = await db.news.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    return [News(**news) for news in news_list]

@api_router.get("/news/{news_id}", response_model=News)
async def get_news_by_id(news_id: str, current_user: User = Depends(get_current_user)):
    news = await db.news.find_one({"id": news_id})
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return News(**news)

@api_router.put("/news/{news_id}", response_model=News)
async def update_news(news_id: str, news_data: NewsUpdate, current_user: User = Depends(get_current_user)):
    news = await db.news.find_one({"id": news_id})
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR] and news["author_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_data = news_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    if news_data.status == NewsStatus.PUBLISHED and news.get("status") != NewsStatus.PUBLISHED:
        update_data["published_at"] = datetime.utcnow()
    
    await db.news.update_one({"id": news_id}, {"$set": update_data})
    updated_news = await db.news.find_one({"id": news_id})
    return News(**updated_news)

@api_router.delete("/news/{news_id}")
async def delete_news(news_id: str, current_user: User = Depends(get_moderator_user)):
    result = await db.news.delete_one({"id": news_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="News not found")
    return {"message": "News deleted successfully"}

# School info management endpoints
@api_router.post("/school-info", response_model=SchoolInfo)
async def create_school_info(info_data: SchoolInfoCreate, current_user: User = Depends(get_current_user)):
    info_obj = SchoolInfo(**info_data.dict())
    await db.school_info.insert_one(info_obj.dict())
    return info_obj

@api_router.get("/school-info", response_model=List[SchoolInfo])
async def get_school_info(section: Optional[str] = None):
    query = {"is_active": True}
    if section:
        query["section"] = section
    
    info_list = await db.school_info.find(query).sort("order", 1).to_list(100)
    return [SchoolInfo(**info) for info in info_list]

@api_router.put("/school-info/{info_id}", response_model=SchoolInfo)
async def update_school_info(info_id: str, info_data: SchoolInfoUpdate, current_user: User = Depends(get_current_user)):
    info = await db.school_info.find_one({"id": info_id})
    if not info:
        raise HTTPException(status_code=404, detail="School info not found")
    
    update_data = info_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.school_info.update_one({"id": info_id}, {"$set": update_data})
    updated_info = await db.school_info.find_one({"id": info_id})
    return SchoolInfo(**updated_info)

@api_router.delete("/school-info/{info_id}")
async def delete_school_info(info_id: str, current_user: User = Depends(get_moderator_user)):
    result = await db.school_info.delete_one({"id": info_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="School info not found")
    return {"message": "School info deleted successfully"}

# Gallery management endpoints
@api_router.post("/gallery", response_model=Gallery)
async def create_gallery_item(gallery_data: GalleryCreate, current_user: User = Depends(get_current_user)):
    gallery_obj = Gallery(**gallery_data.dict())
    await db.gallery.insert_one(gallery_obj.dict())
    return gallery_obj

@api_router.get("/gallery", response_model=List[Gallery])
async def get_gallery(category: Optional[str] = None, limit: int = 50, skip: int = 0):
    query = {"is_active": True}
    if category:
        query["category"] = category
    
    gallery_list = await db.gallery.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    return [Gallery(**item) for item in gallery_list]

@api_router.put("/gallery/{gallery_id}", response_model=Gallery)
async def update_gallery_item(gallery_id: str, gallery_data: GalleryUpdate, current_user: User = Depends(get_current_user)):
    gallery = await db.gallery.find_one({"id": gallery_id})
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    update_data = gallery_data.dict(exclude_unset=True)
    await db.gallery.update_one({"id": gallery_id}, {"$set": update_data})
    updated_gallery = await db.gallery.find_one({"id": gallery_id})
    return Gallery(**updated_gallery)

@api_router.delete("/gallery/{gallery_id}")
async def delete_gallery_item(gallery_id: str, current_user: User = Depends(get_moderator_user)):
    result = await db.gallery.delete_one({"id": gallery_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    return {"message": "Gallery item deleted successfully"}

# Contact management endpoints
@api_router.post("/contacts", response_model=Contact)
async def create_contact(contact_data: ContactCreate, current_user: User = Depends(get_current_user)):
    contact_obj = Contact(**contact_data.dict())
    await db.contacts.insert_one(contact_obj.dict())
    return contact_obj

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts():
    contacts = await db.contacts.find({"is_active": True}).sort("order", 1).to_list(100)
    return [Contact(**contact) for contact in contacts]

@api_router.put("/contacts/{contact_id}", response_model=Contact)
async def update_contact(contact_id: str, contact_data: ContactUpdate, current_user: User = Depends(get_current_user)):
    contact = await db.contacts.find_one({"id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = contact_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.contacts.update_one({"id": contact_id}, {"$set": update_data})
    updated_contact = await db.contacts.find_one({"id": contact_id})
    return Contact(**updated_contact)

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: User = Depends(get_moderator_user)):
    result = await db.contacts.delete_one({"id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}

# Schedule management endpoints
@api_router.post("/schedule", response_model=Schedule)
async def create_schedule(schedule_data: ScheduleCreate, current_user: User = Depends(get_current_user)):
    schedule_obj = Schedule(**schedule_data.dict())
    await db.schedule.insert_one(schedule_obj.dict())
    return schedule_obj

@api_router.get("/schedule", response_model=List[Schedule])
async def get_schedule(limit: int = 50, skip: int = 0):
    schedule_list = await db.schedule.find({"is_active": True}).skip(skip).limit(limit).sort("date", 1).to_list(limit)
    return [Schedule(**item) for item in schedule_list]

@api_router.put("/schedule/{schedule_id}", response_model=Schedule)
async def update_schedule(schedule_id: str, schedule_data: ScheduleUpdate, current_user: User = Depends(get_current_user)):
    schedule = await db.schedule.find_one({"id": schedule_id})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    update_data = schedule_data.dict(exclude_unset=True)
    await db.schedule.update_one({"id": schedule_id}, {"$set": update_data})
    updated_schedule = await db.schedule.find_one({"id": schedule_id})
    return Schedule(**updated_schedule)

@api_router.delete("/schedule/{schedule_id}")
async def delete_schedule(schedule_id: str, current_user: User = Depends(get_moderator_user)):
    result = await db.schedule.delete_one({"id": schedule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    return {"message": "Schedule item deleted successfully"}

# Comment management endpoints
@api_router.post("/comments", response_model=Comment)
async def create_comment(comment_data: CommentCreate):
    """Public endpoint for creating comments"""
    comment_obj = Comment(**comment_data.dict())
    await db.comments.insert_one(comment_obj.dict())
    return comment_obj

@api_router.get("/comments", response_model=List[Comment])
async def get_comments(
    news_id: Optional[str] = None,
    approved_only: bool = True,
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_current_user)
):
    query = {}
    if news_id:
        query["news_id"] = news_id
    if approved_only and current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        query["is_approved"] = True
    
    comments = await db.comments.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    return [Comment(**comment) for comment in comments]

@api_router.put("/comments/{comment_id}", response_model=Comment)
async def update_comment(comment_id: str, comment_data: CommentUpdate, current_user: User = Depends(get_moderator_user)):
    comment = await db.comments.find_one({"id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    update_data = comment_data.dict(exclude_unset=True)
    await db.comments.update_one({"id": comment_id}, {"$set": update_data})
    updated_comment = await db.comments.find_one({"id": comment_id})
    return Comment(**updated_comment)

@api_router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, current_user: User = Depends(get_moderator_user)):
    result = await db.comments.delete_one({"id": comment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"message": "Comment deleted successfully"}

# Statistics endpoints
@api_router.get("/stats", response_model=SiteStats)
async def get_stats(current_user: User = Depends(get_current_user)):
    # Get counts from different collections
    total_users = await db.users.count_documents({})
    total_news = await db.news.count_documents({})
    total_comments = await db.comments.count_documents({})
    pending_comments = await db.comments.count_documents({"is_approved": False})
    
    # For now, we'll use placeholder values for visits
    # In a real application, you would implement proper analytics
    stats = SiteStats(
        total_visits=0,
        daily_visits=0,
        total_users=total_users,
        total_news=total_news,
        total_comments=total_comments,
        pending_comments=pending_comments
    )
    
    return stats

# Initialize admin user endpoint
@api_router.post("/init-admin")
async def init_admin():
    """Initialize the first admin user - only works if no users exist"""
    user_count = await db.users.count_documents({})
    if user_count > 0:
        raise HTTPException(status_code=400, detail="Admin user already exists")
    
    admin_data = {
        "email": "admin@school.com",
        "full_name": "School Administrator",
        "role": UserRole.ADMIN,
        "hashed_password": get_password_hash("admin123"),
        "is_active": True
    }
    
    admin_user = User(**admin_data)
    await db.users.insert_one(admin_user.dict())
    
    return {"message": "Admin user created successfully", "email": "admin@school.com", "password": "admin123"}


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
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
