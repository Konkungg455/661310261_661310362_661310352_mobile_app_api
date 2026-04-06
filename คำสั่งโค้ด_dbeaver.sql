-- 1. สร้าง Database (ถ้าไม่มี)
CREATE DATABASE IF NOT EXISTS tutor_booking_system;

-- 2. ยืนยันการใช้งาน Database นี้ (สำคัญมาก)
USE tutor_booking_system;

-- 3. ลบตารางเก่า (ถ้ามี) เพื่อล้างค่าใหม่
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS rooms;

-- 4. สร้างตาราง Users
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(15) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 5. สร้างตาราง Rooms
CREATE TABLE rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    location VARCHAR(100)
) ENGINE=InnoDB;

-- 6. สร้างตาราง Bookings
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    room_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status ENUM('pending', 'confirmed', 'cancelled') DEFAULT 'confirmed',
    CONSTRAINT fk_booking_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_booking_room FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. เพิ่มข้อมูลตัวอย่าง
INSERT INTO rooms (room_name, capacity, is_available, location) VALUES 
('Room A01', 4, 1, 'IT Building Floor 1'),
('Room A02', 4, 1, 'IT Building Floor 1'),
('Meeting Room B', 8, 0, 'Library Floor 2'),
('Quiet Zone C', 2, 1, 'Library Floor 1');

INSERT INTO users (student_id, full_name, password) VALUES 
('6401001', 'Somchai IT', 'password123'),
('6401002', 'Somsak Dev', 'securepass');