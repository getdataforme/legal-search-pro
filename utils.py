from typing import Dict, Any, Optional
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def build_search_filter(search_params: Dict[str, Any]) -> Dict[str, Any]:
    """Build MongoDB filter from search parameters"""
    filter_query = {}
    
    # Handle general text search
    if search_params.get("q"):
        filter_query["$text"] = {"$search": search_params["q"]}
    
    # Handle exact matches
    exact_match_fields = ["case_type", "status", "judge_name", "county"]
    for field in exact_match_fields:
        if search_params.get(field):
            # Case-insensitive regex search
            filter_query[field] = {
                "$regex": re.escape(search_params[field]), 
                "$options": "i"
            }
    
    # Handle case number search (partial match)
    if search_params.get("case_number"):
        filter_query["case_number"] = {
            "$regex": re.escape(search_params["case_number"]), 
            "$options": "i"
        }
    
    # Handle party name search
    if search_params.get("party_name"):
        filter_query["parties.name"] = {
            "$regex": re.escape(search_params["party_name"]), 
            "$options": "i"
        }
    
    # Handle attorney name search
    if search_params.get("attorney_name"):
        filter_query["parties.attorney"] = {
            "$regex": re.escape(search_params["attorney_name"]), 
            "$options": "i"
        }
    
    # Handle date range filtering
    if search_params.get("filed_date_from") or search_params.get("filed_date_to"):
        date_filter = {}
        
        if search_params.get("filed_date_from"):
            try:
                # Validate date format
                datetime.strptime(search_params["filed_date_from"], "%Y-%m-%d")
                date_filter["$gte"] = search_params["filed_date_from"]
            except ValueError:
                logger.warning(f"Invalid date format for filed_date_from: {search_params['filed_date_from']}")
        
        if search_params.get("filed_date_to"):
            try:
                # Validate date format
                datetime.strptime(search_params["filed_date_to"], "%Y-%m-%d")
                date_filter["$lte"] = search_params["filed_date_to"]
            except ValueError:
                logger.warning(f"Invalid date format for filed_date_to: {search_params['filed_date_to']}")
        
        if date_filter:
            filter_query["filed_date"] = date_filter
    
    return filter_query

def build_sort_criteria(has_text_search: bool) -> list:
    """Build sort criteria for search results"""
    if has_text_search:
        # Sort by text search score when doing text search
        return [("score", {"$meta": "textScore"}), ("filed_date", -1)]
    else:
        # Default sort by filed date (newest first)
        return [("filed_date", -1)]

def calculate_pagination(total_count: int, page: int, page_size: int) -> Dict[str, Any]:
    """Calculate pagination metadata"""
    total_pages = (total_count + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }

def sanitize_search_input(search_text: str) -> str:
    """Sanitize search input to prevent injection attacks"""
    if not search_text:
        return ""
    
    # Remove special MongoDB operators and characters
    sanitized = re.sub(r'[{}$]', '', search_text)
    # Limit length
    sanitized = sanitized[:200]
    return sanitized.strip()

def validate_object_id(object_id: str) -> bool:
    """Validate MongoDB ObjectId format"""
    import re
    return bool(re.match(r'^[0-9a-fA-F]{24}$', object_id))
