import sqlite3

DATABASE_NAME = "game_data.db"

def init_db():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                high_score INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

def save_score(username, score):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE players 
            SET high_score = MAX(high_score, ?) 
            WHERE username = ?
        ''', (score, username))
        conn.commit()

def get_leaderboard(limit=10):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, high_score 
            FROM players 
            ORDER BY high_score DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
