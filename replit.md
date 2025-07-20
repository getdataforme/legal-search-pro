# Legal Cases Search API

## Overview

This is a FastAPI-based backend system for managing and searching legal case documents. The application provides RESTful APIs for creating, updating, retrieving, and searching legal cases stored in a MongoDB database. It features comprehensive search capabilities including full-text search, field-specific filtering, and pagination.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI (Python) - chosen for its high performance, automatic API documentation, and built-in data validation
- **Async Support**: Full async/await implementation using Motor (async MongoDB driver) for non-blocking database operations
- **API Design**: RESTful API with automatic OpenAPI/Swagger documentation generation

### Database Architecture
- **Database**: MongoDB - selected for its flexible document structure, ideal for storing varied legal case data with nested documents and arrays
- **ODM**: Motor (AsyncIOMotorClient) for async MongoDB operations
- **Indexing**: Text indexes on key searchable fields for efficient full-text search capabilities

### Application Structure
- **Modular Design**: Organized into routers, models, database layers, and utilities for clean separation of concerns
- **Configuration Management**: Environment-based configuration with sensible defaults
- **Lifecycle Management**: Proper startup/shutdown handling for database connections

## Key Components

### 1. Data Models (`models.py`)
- **LegalCase**: Main document model with comprehensive case information
- **Party**: Embedded document for case participants (plaintiffs, defendants, attorneys)
- **Document**: Embedded document for case-related files and records
- **PyObjectId**: Custom ObjectId handling for MongoDB integration
- **Validation**: Pydantic models provide automatic request/response validation

### 2. Database Layer (`database.py`)
- **Connection Management**: Async MongoDB connection with proper lifecycle handling
- **Index Creation**: Automatic text index creation for search optimization
- **Error Handling**: Comprehensive error handling with logging

### 3. Search Engine (`routers/search.py`)
- **Multi-field Search**: Support for text search across multiple fields
- **Advanced Filtering**: Case-specific filters (type, status, judge, county, parties, attorneys)
- **Date Range Filtering**: Support for filed date range queries
- **Pagination**: Configurable page size with limits

### 4. Case Management (`routers/cases.py`)
- **CRUD Operations**: Full create, read, update, delete operations for legal cases
- **Duplicate Prevention**: Case number uniqueness validation
- **Data Integrity**: Comprehensive validation and error handling

### 5. Utilities (`utils.py`)
- **Search Filter Builder**: Dynamic MongoDB query construction
- **Input Sanitization**: Protection against injection attacks
- **Pagination Helpers**: Offset/limit calculation utilities

## Data Flow

### 1. Case Creation Flow
1. Client sends case data via POST request
2. Pydantic models validate incoming data
3. System checks for duplicate case numbers
4. Case is inserted into MongoDB with generated ObjectId
5. Created case is returned to client

### 2. Search Flow
1. Client submits search parameters via GET request
2. Search parameters are validated and sanitized
3. MongoDB filter query is dynamically constructed
4. Text indexes are utilized for efficient searching
5. Results are paginated and returned with metadata

### 3. Case Retrieval Flow
1. Client requests specific case by ID or searches with filters
2. MongoDB queries are executed with proper error handling
3. Results are serialized through Pydantic models
4. Formatted response is returned to client

## External Dependencies

### Core Dependencies
- **FastAPI**: Web framework for building APIs
- **Motor**: Async MongoDB driver
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for running the application

### Database
- **MongoDB**: Primary data store requiring external MongoDB instance
- **Connection**: Configurable via MONGODB_URL environment variable

### Development Dependencies
- **Logging**: Built-in Python logging for application monitoring
- **CORS**: Configurable cross-origin resource sharing support

## Deployment Strategy

### Environment Configuration
- **Environment Variables**: All configuration externalized through environment variables
- **Defaults**: Sensible defaults provided for development environments
- **Database URL**: Configurable MongoDB connection string

### Application Lifecycle
- **Startup**: Database connection establishment and index creation
- **Shutdown**: Graceful database connection cleanup
- **Health Checks**: Database ping verification during startup

### Scalability Considerations
- **Async Operations**: Non-blocking I/O for high concurrency
- **Database Indexes**: Optimized for search performance
- **Pagination**: Controlled result set sizes to manage memory usage
- **Connection Pooling**: Motor handles connection pooling automatically

### Production Readiness
- **Error Handling**: Comprehensive exception handling with appropriate HTTP status codes
- **Logging**: Structured logging for monitoring and debugging
- **API Documentation**: Automatic OpenAPI documentation generation
- **Input Validation**: Robust data validation and sanitization