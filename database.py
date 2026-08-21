import sqlite3
from datetime import datetime

DB_NAME = "hazards.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS potholes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            confidence REAL,
            image_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_pothole(lat: float, lng: float, confidence: float, image_path: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO potholes (latitude, longitude, confidence, image_path, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (lat, lng, confidence, image_path, datetime.now()))
    conn.commit()
    conn.close()

def get_all_hazards():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT latitude, longitude, confidence, image_path, timestamp FROM potholes')
    rows = cursor.fetchall()
    conn.close()
    
    hazards = []
    for row in rows:
        hazards.append({
            "latitude": row[0],
            "longitude": row[1],
            "confidence": row[2],
            "image_path": row[3],
            "timestamp": row[4]
        })
    return hazards
