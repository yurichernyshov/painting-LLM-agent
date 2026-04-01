import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

class Database:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # User preferences table (favorite shapes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                shape_type TEXT NOT NULL,
                color TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                is_favorite BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, shape_type, color)
            )
        ''')
        
        # Shape drawing history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shape_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                shape_type TEXT NOT NULL,
                color TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username: str, password_hash: str) -> bool:
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET last_login = ? WHERE id = ?',
            (datetime.now(), user_id)
        )
        conn.commit()
        conn.close()
    
    def get_user_preferences(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's shape preferences"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM user_preferences WHERE user_id = ?',
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_shape_count(self, user_id: int, shape_type: str, color: str, 
                          increment: int = 1, is_favorite: bool = False):
        """Update shape count for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if preference exists
        cursor.execute(
            'SELECT id FROM user_preferences WHERE user_id = ? AND shape_type = ? AND color = ?',
            (user_id, shape_type, color)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                '''UPDATE user_preferences 
                   SET count = count + ?, is_favorite = ? 
                   WHERE user_id = ? AND shape_type = ? AND color = ?''',
                (increment, is_favorite, user_id, shape_type, color)
            )
        else:
            cursor.execute(
                '''INSERT INTO user_preferences 
                   (user_id, shape_type, color, count, is_favorite) 
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, shape_type, color, increment, is_favorite)
            )
        
        conn.commit()
        conn.close()
    
    def log_shape_action(self, user_id: int, shape_type: str, color: str, action: str):
        """Log shape drawing action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO shape_history 
               (user_id, shape_type, color, action) 
               VALUES (?, ?, ?, ?)''',
            (user_id, shape_type, color, action)
        )
        conn.commit()
        conn.close()
    
    def get_shape_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user's shape drawing statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Total shapes drawn
        cursor.execute(
            '''SELECT SUM(count) as total FROM user_preferences WHERE user_id = ?''',
            (user_id,)
        )
        total_row = cursor.fetchone()
        total_shapes = total_row['total'] if total_row['total'] else 0
        
        # Favorite shapes
        cursor.execute(
            '''SELECT shape_type, color, count FROM user_preferences 
               WHERE user_id = ? AND is_favorite = 1 
               ORDER BY count DESC''',
            (user_id,)
        )
        favorites = [dict(row) for row in cursor.fetchall()]
        
        # All shapes with counts
        cursor.execute(
            '''SELECT shape_type, color, count FROM user_preferences 
               WHERE user_id = ? ORDER BY count DESC''',
            (user_id,)
        )
        all_shapes = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_shapes': total_shapes,
            'favorites': favorites,
            'all_shapes': all_shapes
        }
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
