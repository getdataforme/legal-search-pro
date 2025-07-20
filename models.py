from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        schema.update(type="string")
        return schema

class Party(BaseModel):
    name: str = Field(..., description="Name of the party")
    type: str = Field(..., description="Type of party (Plaintiff, Defendant, etc.)")
    attorney: Optional[str] = Field(None, description="Attorney name")
    atty_phone: Optional[str] = Field(None, description="Attorney phone number")

class Document(BaseModel):
    date: str = Field(..., description="Document date")
    description: str = Field(..., description="Document description")
    pages: str = Field(..., description="Number of pages")
    doc_link: str = Field(..., description="Link to document")
    path: str = Field(..., description="Document path")

class LegalCase(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    case_number: str = Field(..., description="Unique case number")
    description: str = Field(..., description="Case description")
    location: str = Field(..., description="Court location/division")
    ucn: str = Field(..., description="Uniform case number")
    case_type: str = Field(..., description="Type of case")
    status: str = Field(..., description="Current case status")
    judge_name: str = Field(..., description="Assigned judge name")
    filed_date: str = Field(..., description="Date case was filed")
    parties: List[Party] = Field(..., description="List of parties involved")
    documents: List[Document] = Field(..., description="List of case documents")
    actor_id: str = Field(..., alias="actor-id", description="Actor ID")
    county: str = Field(..., description="County where case is filed")
    court_id: str = Field(..., alias="court-id", description="Court identifier")
    crawled_date: str = Field(..., description="Date when case was crawled")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class LegalCaseCreate(BaseModel):
    case_number: str
    description: str
    location: str
    ucn: str
    case_type: str
    status: str
    judge_name: str
    filed_date: str
    parties: List[Party]
    documents: List[Document]
    actor_id: str = Field(..., alias="actor-id")
    county: str
    court_id: str = Field(..., alias="court-id")
    crawled_date: str

    class Config:
        populate_by_name = True

class LegalCaseUpdate(BaseModel):
    case_number: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    ucn: Optional[str] = None
    case_type: Optional[str] = None
    status: Optional[str] = None
    judge_name: Optional[str] = None
    filed_date: Optional[str] = None
    parties: Optional[List[Party]] = None
    documents: Optional[List[Document]] = None
    actor_id: Optional[str] = Field(None, alias="actor-id")
    county: Optional[str] = None
    court_id: Optional[str] = Field(None, alias="court-id")
    crawled_date: Optional[str] = None

    class Config:
        populate_by_name = True

class SearchQuery(BaseModel):
    q: Optional[str] = Field(None, description="General text search query")
    case_number: Optional[str] = Field(None, description="Search by case number")
    case_type: Optional[str] = Field(None, description="Filter by case type")
    status: Optional[str] = Field(None, description="Filter by case status")
    judge_name: Optional[str] = Field(None, description="Filter by judge name")
    county: Optional[str] = Field(None, description="Filter by county")
    party_name: Optional[str] = Field(None, description="Search by party name")
    attorney_name: Optional[str] = Field(None, description="Search by attorney name")
    filed_date_from: Optional[str] = Field(None, description="Filter cases filed from this date (YYYY-MM-DD)")
    filed_date_to: Optional[str] = Field(None, description="Filter cases filed until this date (YYYY-MM-DD)")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Number of results per page")

class SearchResponse(BaseModel):
    results: List[LegalCase]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
