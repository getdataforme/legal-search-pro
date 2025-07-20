#!/usr/bin/env python3
"""
Sample data insertion script for Legal Cases Search API
This script adds the sample legal case data you provided to the database.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Your exact sample data
SAMPLE_CASE = {
    "case_number": "2025-CA-006779-O",
    "description": "AUGUSTE, LUCIE vs. SIMONET, CHARLENE M.",
    "location": "Div 48",
    "ucn": "482025CA006779A001OX",
    "case_type": "CA - Auto Negligence",
    "status": "Pending",
    "judge_name": "Brian Sandor",
    "filed_date": "2025-07-17",
    "parties": [
        {
            "name": "LUCIE  AUGUSTE",
            "type": "Plaintiff",
            "attorney": "LINA LOPEZ-FULLAM",
            "atty_phone": "386-281-6794"
        },
        {
            "name": "CHARLENE M. SIMONET",
            "type": "Defendant",
            "attorney": "",
            "atty_phone": ""
        }
    ],
    "documents": [
        {
            "date": "07/17/2025",
            "description": "Complaint",
            "pages": "3",
            "doc_link": "https://myeclerk.myorangeclerk.com/DocView/Doc?eCode=ArmwaLXNQEFMDJi2a6SkZchGUR%2FRv6A2jrqPtFQChyp8ZUKmqgW7fbkZEr%2B5LarUrmvkZT%2FA54RYxYhBcZKMM9citWOrZYyIUUnR3UKhw0R5uUD1fJROlnmbXpTj0ZQAwSPr7CES00bM%2BCF7H0vOmw%3D%3D",
            "path": "orangecounty/2025-CA-006779-O/2025-07-18/Complaint0.pdf"
        },
        {
            "date": "07/17/2025",
            "description": "Civil Cover Sheet",
            "pages": "3",
            "doc_link": "https://myeclerk.myorangeclerk.com/DocView/Doc?eCode=PseXFtHdRj8iRhIT5Ih3glO%2F5jY5YAsdlNhXCNqwYqVd3kZhaL3lZRPlMh%2FbZEjZGVMKBRFhGAcdOI3OpPvfkWlFaSm6tKF9Cz8Dl2Z9c4qHavdET4CdsqqM4rQ0zZSHGn%2BY1PKJuKAgfWje4XNaPg%3D%3D",
            "path": "orangecounty/2025-CA-006779-O/2025-07-18/Civil_Cover_Sheet1.pdf"
        }
    ],
    "actor-id": "202502",
    "county": "Orange",
    "court-id": "L6crt-202502-1685",
    "crawled_date": "2025-07-18 08:42:41"
}

# Additional sample cases for demonstration
ADDITIONAL_CASES = [
    {
        "case_number": "2025-CV-001234-B",
        "description": "SMITH, JOHN vs. ACME CORPORATION",
        "location": "Div 12",
        "ucn": "122025CV001234B001OX",
        "case_type": "CV - Contract Dispute",
        "status": "Active",
        "judge_name": "Maria Rodriguez",
        "filed_date": "2025-06-15",
        "parties": [
            {
                "name": "JOHN SMITH",
                "type": "Plaintiff",
                "attorney": "MICHAEL JOHNSON",
                "atty_phone": "407-555-0123"
            },
            {
                "name": "ACME CORPORATION",
                "type": "Defendant",
                "attorney": "SARAH WILLIAMS",
                "atty_phone": "407-555-0456"
            }
        ],
        "documents": [
            {
                "date": "06/15/2025",
                "description": "Initial Complaint",
                "pages": "5",
                "doc_link": "https://example.com/doc1",
                "path": "orangecounty/2025-CV-001234-B/2025-06-15/Complaint0.pdf"
            }
        ],
        "actor-id": "202501",
        "county": "Orange",
        "court-id": "L6crt-202501-1234",
        "crawled_date": "2025-06-16 09:15:22"
    },
    {
        "case_number": "2025-FA-005678-C",
        "description": "BROWN, MARY vs. BROWN, DAVID",
        "location": "Div 25",
        "ucn": "252025FA005678C001OX",
        "case_type": "FA - Family Law",
        "status": "Pending",
        "judge_name": "Robert Chen",
        "filed_date": "2025-07-01",
        "parties": [
            {
                "name": "MARY BROWN",
                "type": "Petitioner",
                "attorney": "LISA DAVIS",
                "atty_phone": "407-555-0789"
            },
            {
                "name": "DAVID BROWN",
                "type": "Respondent",
                "attorney": "",
                "atty_phone": ""
            }
        ],
        "documents": [
            {
                "date": "07/01/2025",
                "description": "Petition for Dissolution",
                "pages": "8",
                "doc_link": "https://example.com/doc2",
                "path": "orangecounty/2025-FA-005678-C/2025-07-01/Petition0.pdf"
            }
        ],
        "actor-id": "202503",
        "county": "Orange",
        "court-id": "L6crt-202503-5678",
        "crawled_date": "2025-07-02 14:30:45"
    }
]

API_BASE_URL = "http://localhost:5000"

async def insert_case(session, case_data):
    """Insert a single case into the API"""
    async with session.post(f"{API_BASE_URL}/cases/", json=case_data) as response:
        if response.status == 201:
            result = await response.json()
            print(f"✓ Successfully inserted case: {case_data['case_number']}")
            return result
        else:
            error = await response.text()
            print(f"✗ Failed to insert case {case_data['case_number']}: {error}")
            return None

async def test_search(session):
    """Test various search scenarios"""
    print("\n--- Testing Search Functionality ---")
    
    search_tests = [
        ("Text search for 'AUGUSTE'", "/search/?q=AUGUSTE"),
        ("Search by case type", "/search/?case_type=CA - Auto Negligence"),
        ("Search by county", "/search/?county=Orange"),
        ("Search by judge", "/search/?judge_name=Brian Sandor"),
        ("Search by party name", "/search/?party_name=LUCIE"),
        ("Search by attorney", "/search/?attorney_name=LOPEZ"),
        ("Date range search", "/search/?filed_date_from=2025-07-01&filed_date_to=2025-07-31"),
    ]
    
    for test_name, endpoint in search_tests:
        async with session.get(f"{API_BASE_URL}{endpoint}") as response:
            if response.status == 200:
                result = await response.json()
                count = result.get('total_count', 0)
                print(f"✓ {test_name}: Found {count} results")
            else:
                print(f"✗ {test_name}: Failed with status {response.status}")

async def main():
    """Main function to insert sample data and test the API"""
    print("Legal Cases Search API - Sample Data Insertion")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test API connectivity
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✓ API is running: {health.get('status', 'unknown')}")
                else:
                    print(f"✗ API health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"✗ Cannot connect to API: {e}")
            return
        
        # Insert your main sample case
        print("\n--- Inserting Sample Cases ---")
        await insert_case(session, SAMPLE_CASE)
        
        # Insert additional sample cases
        for case in ADDITIONAL_CASES:
            await insert_case(session, case)
        
        # Test search functionality
        await test_search(session)
        
        # Get case suggestions
        print("\n--- Testing Filter Suggestions ---")
        suggestions = [
            ("case types", "/search/suggest/case-types"),
            ("statuses", "/search/suggest/statuses"),
            ("judges", "/search/suggest/judges"),
            ("counties", "/search/suggest/counties"),
        ]
        
        for name, endpoint in suggestions:
            async with session.get(f"{API_BASE_URL}{endpoint}") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✓ Available {name}: {result}")
                else:
                    print(f"✗ Failed to get {name}")

if __name__ == "__main__":
    asyncio.run(main())