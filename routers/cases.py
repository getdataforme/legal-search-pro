from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from typing import Optional, List
from bson import ObjectId
from bson.errors import InvalidId
import logging

from models import LegalCase, LegalCaseCreate, LegalCaseUpdate, ErrorResponse
from database import get_collection
from utils import validate_object_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cases", tags=["Legal Cases"])

@router.post("/", response_model=LegalCase, status_code=status.HTTP_201_CREATED)
async def create_case(case: LegalCaseCreate):
    """Create a new legal case"""
    try:
        collection = get_collection()
        
        # Convert to dict and handle field aliases
        case_dict = case.dict(by_alias=True)
        
        # Check if case number already exists
        existing_case = await collection.find_one({"case_number": case_dict["case_number"]})
        if existing_case:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Case with number {case_dict['case_number']} already exists"
            )
        
        # Insert the case
        result = await collection.insert_one(case_dict)
        
        # Retrieve the created case
        created_case = await collection.find_one({"_id": result.inserted_id})
        
        if not created_case:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create case"
            )
        
        return LegalCase(**created_case)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating case"
        )

@router.get("/{case_id}", response_model=LegalCase)
async def get_case(case_id: str = Path(..., description="Case ID")):
    """Get a specific legal case by ID"""
    try:
        if not validate_object_id(case_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid case ID format"
            )
        
        collection = get_collection()
        case = await collection.find_one({"_id": ObjectId(case_id)})
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
        
        return LegalCase(**case)
        
    except HTTPException:
        raise
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
    except Exception as e:
        logger.error(f"Error retrieving case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving case"
        )

@router.put("/{case_id}", response_model=LegalCase)
async def update_case(
    case_id: str = Path(..., description="Case ID"),
    case_update: LegalCaseUpdate = ...
):
    """Update a legal case"""
    try:
        if not validate_object_id(case_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid case ID format"
            )
        
        collection = get_collection()
        
        # Check if case exists
        existing_case = await collection.find_one({"_id": ObjectId(case_id)})
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
        
        # Prepare update data (exclude None values)
        update_data = {k: v for k, v in case_update.dict(by_alias=True).items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )
        
        # Check for case number conflict if updating case_number
        if "case_number" in update_data:
            case_number_conflict = await collection.find_one({
                "case_number": update_data["case_number"],
                "_id": {"$ne": ObjectId(case_id)}
            })
            if case_number_conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Case with number {update_data['case_number']} already exists"
                )
        
        # Update the case
        result = await collection.update_one(
            {"_id": ObjectId(case_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes were made to the case"
            )
        
        # Retrieve updated case
        updated_case = await collection.find_one({"_id": ObjectId(case_id)})
        return LegalCase(**updated_case)
        
    except HTTPException:
        raise
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
    except Exception as e:
        logger.error(f"Error updating case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating case"
        )

@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: str = Path(..., description="Case ID")):
    """Delete a legal case"""
    try:
        if not validate_object_id(case_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid case ID format"
            )
        
        collection = get_collection()
        
        # Check if case exists
        existing_case = await collection.find_one({"_id": ObjectId(case_id)})
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with ID {case_id} not found"
            )
        
        # Delete the case
        result = await collection.delete_one({"_id": ObjectId(case_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete case"
            )
        
    except HTTPException:
        raise
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid case ID format"
        )
    except Exception as e:
        logger.error(f"Error deleting case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting case"
        )

@router.get("/", response_model=List[LegalCase])
async def list_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of cases per page")
):
    """List all legal cases with pagination"""
    try:
        collection = get_collection()
        
        # Calculate skip value for pagination
        skip = (page - 1) * page_size
        
        # Get cases with pagination
        cursor = collection.find().skip(skip).limit(page_size).sort("filed_date", -1)
        cases = await cursor.to_list(length=page_size)
        
        # Convert to LegalCase objects
        result = [LegalCase(**case) for case in cases]
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while listing cases"
        )

@router.get("/case-number/{case_number}", response_model=LegalCase)
async def get_case_by_number(case_number: str = Path(..., description="Case number")):
    """Get a legal case by case number"""
    try:
        collection = get_collection()
        case = await collection.find_one({"case_number": case_number})
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with number {case_number} not found"
            )
        
        return LegalCase(**case)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving case by number {case_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving case"
        )
