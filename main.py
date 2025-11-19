import os
from datetime import date
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Room as RoomSchema, Booking as BookingSchema

app = FastAPI(title="La Luna Resort API", description="Luxurious booking system backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "La Luna Resort API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Utility
class RoomOut(RoomSchema):
    id: str

class BookingOut(BookingSchema):
    id: str


def _to_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


# Rooms
@app.post("/rooms", response_model=dict)
def create_room(room: RoomSchema):
    room_id = create_document("room", room)
    return {"id": room_id}

@app.get("/rooms", response_model=List[RoomOut])
def list_rooms():
    docs = get_documents("room")
    rooms: List[RoomOut] = []
    for d in docs:
        d["id"] = str(d.pop("_id"))
        rooms.append(RoomOut(**d))
    return rooms


# Availability
class AvailabilityRequest(BaseModel):
    check_in: date
    check_out: date
    guests: int = 1

@app.post("/availability", response_model=List[RoomOut])
def check_availability(payload: AvailabilityRequest):
    if payload.check_out <= payload.check_in:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")
    # Find rooms that fit capacity
    candidate_rooms = list(get_documents("room", {"capacity": {"$gte": payload.guests}}))

    # Get bookings that overlap the requested date range
    overlapping = list(db["booking"].find({
        "$or": [
            {"check_in": {"$lt": payload.check_out.isoformat()}, "check_out": {"$gt": payload.check_in.isoformat()}},
        ],
        "status": {"$ne": "cancelled"}
    }))
    booked_ids = {str(b["room_id"]) if isinstance(b.get("room_id"), str) else str(b.get("room_id")) for b in overlapping}

    available = []
    for r in candidate_rooms:
        rid = str(r.pop("_id"))
        if rid not in booked_ids:
            r["id"] = rid
            available.append(RoomOut(**r))
    return available


# Bookings
@app.post("/bookings", response_model=dict)
def create_booking(booking: BookingSchema):
    # Validate room exists
    room_oid = _to_id(booking.room_id)
    room = db["room"].find_one({"_id": room_oid})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check overlapping
    overlap = db["booking"].find_one({
        "room_id": booking.room_id,
        "$or": [
            {"check_in": {"$lt": booking.check_out.isoformat()}, "check_out": {"$gt": booking.check_in.isoformat()}},
        ],
        "status": {"$ne": "cancelled"}
    })
    if overlap:
        raise HTTPException(status_code=409, detail="Room not available for selected dates")

    booking_id = create_document("booking", booking)
    return {"id": booking_id}

@app.get("/bookings", response_model=List[BookingOut])
def list_bookings(email: Optional[str] = None):
    filter_q = {"email": email} if email else None
    docs = get_documents("booking", filter_q)
    bookings: List[BookingOut] = []
    for d in docs:
        d["id"] = str(d.pop("_id"))
        bookings.append(BookingOut(**d))
    return bookings


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
