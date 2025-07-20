from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import Optional, List, Dict, Any
import logging

from models import SearchQuery, SearchResponse, LegalCase
from database import get_collection
from utils import build_search_filter, build_sort_criteria, calculate_pagination, sanitize_search_input
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])

async def get_search_params(
    q: Optional[str] = Query(None, description="General text search query"),
    case_number: Optional[str] = Query(None, description="Search by case number"),
    case_type: Optional[str] = Query(None, description="Filter by case type"),
    status: Optional[str] = Query(None, description="Filter by case status"),
    judge_name: Optional[str] = Query(None, description="Filter by judge name"),
    county: Optional[str] = Query(None, description="Filter by county"),
    party_name: Optional[str] = Query(None, description="Search by party name"),
    attorney_name: Optional[str] = Query(None, description="Search by attorney name"),
    filed_date_from: Optional[str] = Query(None, description="Filter cases filed from this date (YYYY-MM-DD)"),
    filed_date_to: Optional[str] = Query(None, description="Filter cases filed until this date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="Number of results per page")
) -> SearchQuery:
    """Dependency to extract search parameters"""
    return SearchQuery(
        q=q,
        case_number=case_number,
        case_type=case_type,
        status=status,
        judge_name=judge_name,
        county=county,
        party_name=party_name,
        attorney_name=attorney_name,
        filed_date_from=filed_date_from,
        filed_date_to=filed_date_to,
        page=page,
        page_size=page_size
    )

@router.get("/", response_model=SearchResponse)
async def search_cases(search_params: SearchQuery = Depends(get_search_params)):
    """
    Search legal cases with comprehensive filtering options.
    
    Supports:
    - Full-text search across case fields
    - Filtering by case type, status, judge, county
    - Party and attorney name search
    - Date range filtering
    - Pagination with relevance scoring
    """
    try:
        collection = get_collection()
        
        # Sanitize text search input
        search_dict = search_params.dict()
        if search_dict.get("q"):
            search_dict["q"] = sanitize_search_input(search_dict["q"])
        
        # Build MongoDB filter
        filter_query = build_search_filter(search_dict)
        
        # Determine if we have text search for sorting
        has_text_search = "$text" in filter_query
        
        # Build sort criteria
        sort_criteria = build_sort_criteria(has_text_search)
        
        # Calculate skip for pagination
        skip = (search_params.page - 1) * search_params.page_size
        
        # Execute search with aggregation pipeline for better performance
        pipeline = [
            {"$match": filter_query}
        ]
        
        # Add text score projection if doing text search
        if has_text_search:
            pipeline.append({
                "$addFields": {
                    "score": {"$meta": "textScore"}
                }
            })
        
        # Add sorting
        if sort_criteria:
            sort_stage = {}
            for field, direction in sort_criteria:
                if field == "score":
                    sort_stage[field] = direction
                else:
                    sort_stage[field] = direction
            pipeline.append({"$sort": sort_stage})
        
        # Count total results for pagination
        count_pipeline = pipeline.copy()
        count_pipeline.append({"$count": "total"})
        
        count_result = await collection.aggregate(count_pipeline).to_list(length=1)
        total_count = count_result[0]["total"] if count_result else 0
        
        # Add pagination to main pipeline
        pipeline.extend([
            {"$skip": skip},
            {"$limit": search_params.page_size}
        ])
        
        # Execute search
        cursor = collection.aggregate(pipeline)
        cases = await cursor.to_list(length=search_params.page_size)
        
        # Convert to LegalCase objects
        results = []
        for case in cases:
            # Remove score field if it exists (not part of LegalCase model)
            if "score" in case:
                del case["score"]
            results.append(LegalCase(**case))
        
        # Calculate pagination metadata
        pagination_info = calculate_pagination(total_count, search_params.page, search_params.page_size)
        
        return SearchResponse(
            results=results,
            **pagination_info
        )
        
    except Exception as e:
        logger.error(f"Error searching cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while searching cases"
        )

@router.get("/suggest/case-types", response_model=List[str])
async def get_case_types():
    """Get all unique case types for filtering suggestions"""
    try:
        collection = get_collection()
        
        case_types = await collection.distinct("case_type")
        return sorted([ct for ct in case_types if ct])
        
    except Exception as e:
        logger.error(f"Error getting case types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving case types"
        )

@router.get("/suggest/statuses", response_model=List[str])
async def get_statuses():
    """Get all unique case statuses for filtering suggestions"""
    try:
        collection = get_collection()
        
        statuses = await collection.distinct("status")
        return sorted([s for s in statuses if s])
        
    except Exception as e:
        logger.error(f"Error getting statuses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving statuses"
        )

@router.get("/suggest/judges", response_model=List[str])
async def get_judges():
    """Get all unique judge names for filtering suggestions"""
    try:
        collection = get_collection()
        
        judges = await collection.distinct("judge_name")
        return sorted([j for j in judges if j])
        
    except Exception as e:
        logger.error(f"Error getting judges: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving judges"
        )

@router.get("/suggest/counties", response_model=List[str])
async def get_counties():
    """Get all unique counties for filtering suggestions"""
    try:
        collection = get_collection()
        
        counties = await collection.distinct("county")
        return sorted([c for c in counties if c])
        
    except Exception as e:
        logger.error(f"Error getting counties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving counties"
        )

@router.get("/advanced", response_model=SearchResponse)
async def advanced_search(
    text_query: Optional[str] = Query(None, description="Full-text search query"),
    case_numbers: Optional[str] = Query(None, description="Comma-separated case numbers"),
    case_types: Optional[str] = Query(None, description="Comma-separated case types"),
    statuses: Optional[str] = Query(None, description="Comma-separated statuses"),
    judges: Optional[str] = Query(None, description="Comma-separated judge names"),
    counties: Optional[str] = Query(None, description="Comma-separated counties"),
    parties: Optional[str] = Query(None, description="Comma-separated party names"),
    attorneys: Optional[str] = Query(None, description="Comma-separated attorney names"),
    filed_after: Optional[str] = Query(None, description="Filed after date (YYYY-MM-DD)"),
    filed_before: Optional[str] = Query(None, description="Filed before date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="Results per page")
):
    """
    Advanced search with multiple value support for each field.
    Supports OR logic within field types and AND logic between different field types.
    """
    try:
        collection = get_collection()
        
        # Build complex filter query
        filter_conditions = []
        
        # Handle text search
        if text_query:
            sanitized_query = sanitize_search_input(text_query)
            if sanitized_query:
                filter_conditions.append({"$text": {"$search": sanitized_query}})
        
        # Handle multiple case numbers
        if case_numbers:
            case_number_list = [cn.strip() for cn in case_numbers.split(",") if cn.strip()]
            if case_number_list:
                case_number_conditions = [
                    {"case_number": {"$regex": f".*{cn}.*", "$options": "i"}} 
                    for cn in case_number_list
                ]
                filter_conditions.append({"$or": case_number_conditions})
        
        # Handle multiple case types
        if case_types:
            case_type_list = [ct.strip() for ct in case_types.split(",") if ct.strip()]
            if case_type_list:
                filter_conditions.append({"case_type": {"$in": case_type_list}})
        
        # Handle multiple statuses
        if statuses:
            status_list = [s.strip() for s in statuses.split(",") if s.strip()]
            if status_list:
                filter_conditions.append({"status": {"$in": status_list}})
        
        # Handle multiple judges
        if judges:
            judge_list = [j.strip() for j in judges.split(",") if j.strip()]
            if judge_list:
                judge_conditions = [
                    {"judge_name": {"$regex": f".*{judge}.*", "$options": "i"}} 
                    for judge in judge_list
                ]
                filter_conditions.append({"$or": judge_conditions})
        
        # Handle multiple counties
        if counties:
            county_list = [c.strip() for c in counties.split(",") if c.strip()]
            if county_list:
                filter_conditions.append({"county": {"$in": county_list}})
        
        # Handle multiple parties
        if parties:
            party_list = [p.strip() for p in parties.split(",") if p.strip()]
            if party_list:
                party_conditions = [
                    {"parties.name": {"$regex": f".*{party}.*", "$options": "i"}} 
                    for party in party_list
                ]
                filter_conditions.append({"$or": party_conditions})
        
        # Handle multiple attorneys
        if attorneys:
            attorney_list = [a.strip() for a in attorneys.split(",") if a.strip()]
            if attorney_list:
                attorney_conditions = [
                    {"parties.attorney": {"$regex": f".*{attorney}.*", "$options": "i"}} 
                    for attorney in attorney_list
                ]
                filter_conditions.append({"$or": attorney_conditions})
        
        # Handle date range
        date_filter = {}
        if filed_after:
            date_filter["$gte"] = filed_after
        if filed_before:
            date_filter["$lte"] = filed_before
        
        if date_filter:
            filter_conditions.append({"filed_date": date_filter})
        
        # Combine all conditions with AND logic
        final_filter = {"$and": filter_conditions} if filter_conditions else {}
        
        # Determine sorting
        has_text_search = any("$text" in condition for condition in filter_conditions)
        sort_criteria = build_sort_criteria(has_text_search)
        
        # Calculate skip for pagination
        skip = (page - 1) * page_size
        
        # Execute search
        pipeline = [
            {"$match": final_filter}
        ]
        
        # Add text score if doing text search
        if has_text_search:
            pipeline.append({
                "$addFields": {
                    "score": {"$meta": "textScore"}
                }
            })
        
        # Add sorting
        if sort_criteria:
            sort_stage = {}
            for field, direction in sort_criteria:
                sort_stage[field] = direction
            pipeline.append({"$sort": sort_stage})
        
        # Get total count
        count_pipeline = pipeline.copy()
        count_pipeline.append({"$count": "total"})
        
        count_result = await collection.aggregate(count_pipeline).to_list(length=1)
        total_count = count_result[0]["total"] if count_result else 0
        
        # Add pagination
        pipeline.extend([
            {"$skip": skip},
            {"$limit": page_size}
        ])
        
        # Execute search
        cursor = collection.aggregate(pipeline)
        cases = await cursor.to_list(length=page_size)
        
        # Convert to LegalCase objects
        results = []
        for case in cases:
            if "score" in case:
                del case["score"]
            results.append(LegalCase(**case))
        
        # Calculate pagination metadata
        pagination_info = calculate_pagination(total_count, page, page_size)
        
        return SearchResponse(
            results=results,
            **pagination_info
        )
        
    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while performing advanced search"
        )
