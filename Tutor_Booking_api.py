import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import mariadb
from typing import Generator, Optional, List
from datetime import datetime

# -------------------- Pydantic Models --------------------

class Room(BaseModel):
    room_id: Optional[int] = None
    room_name: str
    capacity: int
    is_available: bool = True
    location: Optional[str] = Field(None, max_length=100)

class BookingRequest(BaseModel):
    user_id: int
    room_id: int
    start_time: datetime
    end_time: datetime

class LoginRequest(BaseModel):
    student_id: str
    password: str

# เพิ่ม Model สำหรับสมัครสมาชิก (Sign Up)
class UserCreate(BaseModel):
    student_id: str
    full_name: str
    password: str
    created_at: Optional[str] = None # รองรับค่าวันเวลาที่ส่งมาจาก Flet

app = FastAPI()

# เพิ่ม CORS เพื่อให้แอป (Flet/Web) เชื่อมต่อได้ไม่ติดขัด
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Database Connection --------------------

def get_connection() -> mariadb.Connection:
    try:
        return mariadb.connect(
            host=os.getenv("DB_HOST", "192.168.1.188"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "P@ssword"),
            database=os.getenv("DB_NAME", "tutor_booking_system"),
        )
    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

def get_db() -> Generator[mariadb.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

# -------------------- Routes: Users (สมัครสมาชิก) --------------------

@app.post("/users")
def register_user(user: UserCreate, db: mariadb.Connection = Depends(get_db)):
    """ฟังก์ชันสำหรับสมัครสมาชิกใหม่ และบันทึกวันที่สร้างบัญชี"""
    try:
        cur = db.cursor()
        
        # 1. เช็คก่อนว่า Student ID นี้มีในระบบหรือยัง
        cur.execute("SELECT student_id FROM users WHERE student_id = ?", (user.student_id,))
        if cur.fetchone():
            cur.close()
            raise HTTPException(status_code=400, detail="รหัสนักศึกษานี้ถูกใช้งานแล้ว")
        
        # 2. บันทึกข้อมูลลงตาราง users (รวม created_at)
        sql = "INSERT INTO users (student_id, full_name, password, created_at) VALUES (?, ?, ?, ?)"
        # หากฝั่ง Flet ไม่ส่งเวลามา ให้ใช้เวลาปัจจุบันของ Server
        creation_time = user.created_at if user.created_at else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute(sql, (user.student_id, user.full_name, user.password, creation_time))
        db.commit()
        cur.close()
        
        return {
            "status": "success", 
            "message": "สมัครสมาชิกเรียบร้อยแล้ว", 
            "student_id": user.student_id
        }
    except mariadb.Error as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------- Routes: Rooms (จัดการห้องติว) --------------------

@app.get("/rooms", response_model=List[Room])
def get_rooms(db: mariadb.Connection = Depends(get_db)):
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT room_id, room_name, capacity, is_available, location FROM rooms")
        rooms = cur.fetchall()
        cur.close()
        return rooms
    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rooms/{room_id}", response_model=Room)
def get_room(room_id: int, db: mariadb.Connection = Depends(get_db)):
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT room_id, room_name, capacity, is_available, location FROM rooms WHERE room_id = ?", (room_id,))
        room = cur.fetchone()
        cur.close()
        if not room: raise HTTPException(status_code=404, detail="Room not found")
        return room
    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rooms", response_model=Room)
def add_room(room: Room, db: mariadb.Connection = Depends(get_db)):
    try:
        cur = db.cursor()
        cur.execute(
            "INSERT INTO rooms (room_name, capacity, is_available, location) VALUES (?, ?, ?, ?)",
            (room.room_name, room.capacity, room.is_available, room.location),
        )
        db.commit()
        room_id = cur.lastrowid
        cur.close()
        return {**room.dict(exclude={"room_id"}), "room_id": room_id}
    except mariadb.Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/rooms/{room_id}", response_model=Room)
def update_room(room_id: int, room: Room, db: mariadb.Connection = Depends(get_db)):
    try:
        cur = db.cursor()
        cur.execute(
            "UPDATE rooms SET room_name=?, capacity=?, is_available=?, location=? WHERE room_id=?",
            (room.room_name, room.capacity, room.is_available, room.location, room_id),
        )
        db.commit()
        cur.close()
        return {**room.dict(exclude={"room_id"}), "room_id": room_id}
    except mariadb.Error as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/rooms/{room_id}")
def delete_room(room_id: int, db: mariadb.Connection = Depends(get_db)):
    try:
        cur = db.cursor()
        cur.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
        db.commit()
        cur.close()
        return {"message": "Room deleted"}
    except mariadb.Error as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------- Booking API --------------------

@app.post("/bookings")
def create_booking(booking: BookingRequest, db: mariadb.Connection = Depends(get_db)):
    try:
        duration = booking.end_time - booking.start_time
        hours = duration.total_seconds() / 3600
        if hours <= 0: raise HTTPException(status_code=400, detail="เวลาสิ้นสุดต้องมากกว่าเวลาเริ่ม")
        if hours > 3: raise HTTPException(status_code=400, detail="จำกัดการจองไม่เกิน 3 ชั่วโมง")
        
        cur = db.cursor()
        cur.execute(
            "INSERT INTO bookings (user_id, room_id, start_time, end_time) VALUES (?, ?, ?, ?)",
            (booking.user_id, booking.room_id, booking.start_time, booking.end_time),
        )
        cur.execute("UPDATE rooms SET is_available = 0 WHERE room_id = ?", (booking.room_id,))
        db.commit()
        cur.close()
        return {"status": "success", "message": "Room booked successfully"}
    except mariadb.Error as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------- Login API --------------------

@app.post("/login")
def login(request: LoginRequest, db: mariadb.Connection = Depends(get_db)):
    try:
        cur = db.cursor(dictionary=True)
        sql = "SELECT user_id, student_id, full_name FROM users WHERE student_id=? AND password=?"
        cur.execute(sql, (request.student_id, request.password))
        user = cur.fetchone()
        cur.close()
        if user:
            return {"status": "success", "message": "Login successful", "user": user}
        else:
            raise HTTPException(status_code=401, detail="Invalid student_id or password")
    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# รัน Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)