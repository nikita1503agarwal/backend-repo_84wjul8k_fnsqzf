"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date

# La Luna Resort Schemas

class Room(BaseModel):
    """
    Rooms collection schema
    Collection name: "room"
    """
    name: str = Field(..., description="Display name, e.g., 'Ocean Suite'")
    room_type: str = Field(..., description="Type/category, e.g., 'Suite', 'Villa', 'Deluxe'")
    description: Optional[str] = Field(None, description="Short description")
    beds: int = Field(1, ge=1, le=6, description="Number of beds")
    capacity: int = Field(2, ge=1, le=12, description="Maximum guests")
    price_per_night: float = Field(..., ge=0, description="Base price per night in USD")
    amenities: List[str] = Field(default_factory=list, description="List of amenities")
    images: List[str] = Field(default_factory=list, description="Image URLs")

class Booking(BaseModel):
    """
    Bookings collection schema
    Collection name: "booking"
    """
    room_id: str = Field(..., description="ID of the room being booked")
    guest_name: str = Field(..., description="Primary guest full name")
    email: EmailStr = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    check_in: date = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out: date = Field(..., description="Check-out date (YYYY-MM-DD)")
    guests: int = Field(1, ge=1, le=12, description="Number of guests")
    special_requests: Optional[str] = Field(None, description="Optional notes from guest")
    status: str = Field("confirmed", description="Booking status: pending|confirmed|cancelled")

# Example schemas (kept for reference; not used by app directly)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True

# Note: The Flames database viewer can read these schemas from the backend.
