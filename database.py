import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging
from config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    try:
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            maxPoolSize=10
        )
        mongodb.database = mongodb.client[settings.DATABASE_NAME]
        
        # Test the connection
        await mongodb.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Create text index for full-text search
        await create_search_indexes()
        
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}")
        logger.info("Running in offline mode - API will function but data will not persist")
        # Don't raise the exception to allow the app to start

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")

async def create_search_indexes():
    """Create text indexes for efficient searching"""
    try:
        collection = mongodb.database[settings.COLLECTION_NAME]
        
        # Create text index for full-text search
        text_index = {
            "case_number": "text",
            "description": "text",
            "ucn": "text",
            "case_type": "text",
            "status": "text",
            "judge_name": "text",
            "county": "text",
            "location": "text",
            "parties.name": "text",
            "parties.attorney": "text",
            "documents.description": "text"
        }
        
        await collection.create_index(text_index, name="text_search_index")
        
        # Create individual indexes for filtering
        await collection.create_index("case_number")
        await collection.create_index("case_type")
        await collection.create_index("status")
        await collection.create_index("judge_name")
        await collection.create_index("county")
        await collection.create_index("filed_date")
        await collection.create_index("parties.name")
        await collection.create_index("parties.attorney")
        
        logger.info("Search indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating search indexes: {e}")

def get_database():
    """Get database instance"""
    return mongodb.database

def get_collection():
    """Get cases collection"""
    return mongodb.database[settings.COLLECTION_NAME]
