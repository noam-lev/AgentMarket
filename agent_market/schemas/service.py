from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal, Annotated
from datetime import datetime

class APIConfig(BaseModel):
    """
    Schema for describing the technical configuration of an API.
    This helps AI agents understand how to interact with the API.
    """
    endpoint: HttpUrl = Field(..., description="The base URL endpoint for the API service.")
    method: Literal['GET', 'POST', 'PUT', 'DELETE'] = Field(..., description="The primary HTTP method for this API operation.")
    input_schema: Optional[dict] = Field(None, description="Optional: JSON schema of expected input parameters for the API call.")
    output_schema: Optional[dict] = Field(None, description="Optional: JSON schema of expected output structure for the API response.")

    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "https://api.example.com/translate",
                "method": "POST",
                "input_schema": {"text": "string", "from_lang": "string", "to_lang": "string"},
                "output_schema": {"translated_text": "string"}
            }
        }

class ServiceCreate(BaseModel):
    """
    Pydantic schema for creating a new API service listing.
    This is the data a provider submits when adding an API.
    """
    provider_id: str = Field(..., description="The ID of the provider uploading this service.")
    name: str = Field(..., min_length=3, max_length=100, description="Name of the service (e.g., 'Text Translation API').")
    description: str = Field(
        ...,
        min_length=50,
        max_length=1000,
        description="Detailed description of the API's functionality. CRITICAL for semantic search."
    )
    categories: List[str] = Field(..., description="List of categories this service belongs to (e.g., 'NLP', 'Data Analysis').")
    tags: Optional[List[str]] = Field(None, description="Optional list of keywords or tags for the service.")
    api: APIConfig = Field(..., description="Technical configuration details for the API.")
    openapi_spec: Optional[str] = Field(None, description="Full OpenAPI/Swagger JSON specification string for the API.")

    class Config:
        json_schema_extra = {
            "example": {
                "provider_id": "65b7d9c0e1a2b3c4d5f6e7a8",
                "name": "Weather Forecast API",
                "description": "Provides real-time weather forecasts and historical data for any global location, including temperature, humidity, and wind speed. Integrates with various weather stations worldwide.",
                "categories": ["Weather", "Data"],
                "tags": ["forecast", "temperature", "humidity", "location", "climate"],
                "api": {
                    "endpoint": "https://api.weatherpro.com/v1",
                    "method": "GET",
                    "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}},
                    "output_schema": {"type": "object", "properties": {"temperature": {"type": "number"}, "conditions": {"type": "string"}}}
                },
                "openapi_spec": '{"openapi": "3.0.0", "info": {"title": "Weather Forecast API", "version": "1.0.0"}, "paths": {"/current": {"get": {"parameters": [{"name": "location", "in": "query", "schema": {"type": "string"}, "required": true}], "responses": {"200": {"description": "Current weather data", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/WeatherResponse"}}}}}}}}, "components": {"schemas": {"WeatherResponse": {"type": "object", "properties": {"temperature": {"type": "number"}, "conditions": {"type": "string"}}}}}}'
            }
        }

class ServiceInDB(BaseModel):
    """
    Pydantic schema representing a Service document as stored in MongoDB.
    Includes database-specific fields like _id and generated embedding.
    """
    id: Optional[str] = Field(alias="_id", default=None, description="MongoDB ObjectId as a string.")
    provider_id: str
    name: str
    description: str
    categories: List[str]
    tags: Optional[List[str]]
    api: APIConfig
    openapi_spec: Optional[str]
    embedding: List[float] = Field(..., description="Vector embedding of the service description for semantic search.")
    usage_count: int = Field(default=0, description="Count of times the service has been reported as used.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of service creation.")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last update.")

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        arbitrary_types_allowed = True

class ServiceOut(BaseModel):
    """
    Pydantic schema for Service data returned in API responses.
    Excludes sensitive/internal fields if any.
    """
    id: str = Field(..., description="Unique identifier of the service.")
    provider_id: str = Field(..., description="The ID of the provider of this service.")
    name: str
    description: str
    categories: List[str]
    tags: Optional[List[str]]
    api: APIConfig
    openapi_spec: Optional[str]
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class ServiceUpdate(BaseModel):
    """
    Pydantic schema for updating an existing API service listing.
    All fields are Optional, allowing for partial updates (e.g., only updating description).
    
    Guidance for AI Programmer:
    - This schema is designed specifically for PUT requests where not all fields are present.
    - Fields are made Optional to allow selective updates.
    - Note that 'provider_id' is included as Optional, but your API logic will prevent
      its actual change for security (as you already implemented).
    """
    provider_id: Optional[str] = Field(None, description="The ID of the provider uploading this service (should match authenticated provider).")
    name: Optional[str] = Field(None, min_length=3, max_length=100, description="Name of the service.")
    description: Optional[str] = Field(
        None,
        min_length=50,
        max_length=1000,
        description="Detailed description of the API's functionality. CRITICAL for semantic search."
    )
    categories: Optional[List[str]] = Field(..., description="List of categories this service belongs to.")
    tags: Optional[List[str]] = Field(None, description="Optional list of keywords or tags for the service.")
    
    api: Optional[APIConfig] = Field(None, description="Technical configuration details for the API.")
    
    openapi_spec: Optional[str] = Field(None, description="Full OpenAPI/Swagger JSON specification string for the API.")

    class Config:
        # Example data for OpenAPI documentation (for the update request)
        json_schema_extra = {
            "example": {
                "description": "An even more advanced API for booking haircuts. Now with 3D barber previews!",
                "tags": ["haircut", "barber", "appointments", "booking", "AI-powered", "3D-preview"]
            }
        }
