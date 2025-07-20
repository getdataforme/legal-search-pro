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
    name: Optional[str] = Field(None, description="Name of the party")
    type: Optional[str] = Field(None, description="Type of party (Plaintiff, Defendant, etc.)")
    attorney: Optional[str] = Field(None, description="Attorney name")
    atty_phone: Optional[str] = Field(None, description="Attorney phone number")
    
    # Handle different data formats
    first_name: Optional[str] = Field(None, alias="First Name")
    middle_name: Optional[str] = Field(None, alias="Middle Name")
    last_name: Optional[str] = Field(None, alias="Last Name")
    party_association: Optional[str] = Field(None, alias="Party Association")
    
    class Config:
        populate_by_name = True
        extra = "ignore"  # Ignore extra fields
    
    def __init__(self, **data):
        # Construct name from first/middle/last if name not provided
        if not data.get('name') and (data.get('First Name') or data.get('first_name')):
            parts = []
            for key in ['First Name', 'first_name']:
                if data.get(key):
                    parts.append(data[key])
                    break
            for key in ['Middle Name', 'middle_name']:
                if data.get(key):
                    parts.append(data[key])
                    break
            for key in ['Last Name', 'last_name']:
                if data.get(key):
                    parts.append(data[key])
                    break
            if parts:
                data['name'] = ' '.join(filter(None, parts))
        
        # Use party association as type if type not provided
        if not data.get('type') and data.get('Party Association'):
            data['type'] = data['Party Association'] or 'Unknown'
            
        super().__init__(**data)

class Document(BaseModel):
    date: Optional[str] = Field(None, description="Document date")
    description: Optional[str] = Field(None, description="Document description")
    pages: Optional[str] = Field(None, description="Number of pages")
    doc_link: Optional[str] = Field(None, description="Link to document")
    path: Optional[str] = Field(None, description="Document path")
    filename: Optional[str] = Field(None, description="Document filename")
    
    class Config:
        extra = "ignore"  # Ignore extra fields
    
    def __init__(self, **data):
        # Use filename as description if description not provided
        if not data.get('description') and data.get('filename'):
            data['description'] = data['filename']
        
        # Set default values
        if not data.get('date'):
            data['date'] = 'Unknown'
        if not data.get('pages'):
            data['pages'] = 'Unknown'
        if not data.get('doc_link'):
            data['doc_link'] = '#'
            
        super().__init__(**data)

class LegalCase(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    case_number: Optional[str] = Field(None, description="Unique case number")
    description: Optional[str] = Field(None, description="Case description")
    location: Optional[str] = Field(None, description="Court location/division")
    ucn: Optional[str] = Field(None, description="Uniform case number")
    case_type: Optional[str] = Field(None, description="Type of case")
    status: Optional[str] = Field(None, description="Current case status")
    judge_name: Optional[str] = Field(None, description="Assigned judge name")
    filed_date: Optional[str] = Field(None, description="Date case was filed")
    parties: Optional[List[Party]] = Field(default_factory=list, description="List of parties involved")
    documents: Optional[List[Document]] = Field(default_factory=list, description="List of case documents")
    actor_id: Optional[str] = Field(None, alias="actor-id", description="Actor ID")
    county: Optional[str] = Field(None, description="County where case is filed")
    court_id: Optional[str] = Field(None, alias="court-id", description="Court identifier")
    crawled_date: Optional[str] = Field(None, description="Date when case was crawled")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        extra = "ignore"  # Ignore extra fields
        
    def __init__(self, **data):
        # Set default values for missing required fields
        if not data.get('case_number'):
            data['case_number'] = f"CASE-{str(data.get('_id', 'UNKNOWN'))[:8]}"
        if not data.get('description'):
            data['description'] = 'Case description not available'
        if not data.get('ucn'):
            data['ucn'] = f"UCN-{str(data.get('_id', 'UNKNOWN'))[:8]}"
        if not data.get('judge_name'):
            data['judge_name'] = 'Judge not assigned'
        if not data.get('filed_date'):
            data['filed_date'] = 'Date not available'
        if not data.get('case_type'):
            data['case_type'] = 'Unknown'
        if not data.get('status'):
            data['status'] = 'Unknown'
        if not data.get('location'):
            data['location'] = 'Location not specified'
        if not data.get('county'):
            data['county'] = 'Unknown'
        if not data.get('parties'):
            data['parties'] = []
        if not data.get('documents'):
            data['documents'] = []
            
        super().__init__(**data)

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
