import sqlite3

conn = sqlite3.connect('mydatabase.db')
cursor = conn.cursor()

# --- Student & Score Tables ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    subject TEXT NOT NULL,
    score INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)''')

# --- Teacher & Class Tables ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT NOT NULL,
    teacher_id INTEGER,
    FOREIGN KEY (teacher_id) REFERENCES teachers (id)
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS enrollments (
    user_id INTEGER,
    class_id INTEGER,
    PRIMARY KEY (user_id, class_id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (class_id) REFERENCES classes (id)
)''')

# --- Gamification Tables ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    icon TEXT
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_badges (
    user_id INTEGER,
    badge_id INTEGER,
    PRIMARY KEY (user_id, badge_id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (badge_id) REFERENCES badges (id)
)''')

# --- New Quiz Creation & Assignment Tables ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    teacher_id INTEGER,
    FOREIGN KEY (teacher_id) REFERENCES teachers (id)
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER,
    question_text TEXT NOT NULL,
    options TEXT NOT NULL, -- Storing options as a JSON string
    correct_answer TEXT NOT NULL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER,
    class_id INTEGER,
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
    FOREIGN KEY (class_id) REFERENCES classes (id)
)''')

# --- Re-populating all essential sample data ---
try:
    cursor.execute("INSERT OR IGNORE INTO teachers (username, password) VALUES (?, ?)", ('teacher1', 'pass'))
    cursor.execute("INSERT OR IGNORE INTO classes (class_name, teacher_id) VALUES (?, ?)", ('Grade 5 Physics', 1))
    cursor.execute("INSERT OR IGNORE INTO badges (name, description, icon) VALUES (?, ?, ?)", ('Maths Master', 'Score 100% in a Maths quiz', '🧮'))
    cursor.execute("INSERT OR IGNORE INTO badges (name, description, icon) VALUES (?, ?, ?)", ('Physics Phenom', 'Score 100% in a Physics quiz', '⚛️'))
    cursor.execute("INSERT OR IGNORE INTO badges (name, description, icon) VALUES (?, ?, ?)", ('Quiz Enthusiast', 'Complete 3 quizzes', '🌟'))
except sqlite3.Error as e:
    print(f"An error occurred while inserting sample data: {e}")

conn.commit()
conn.close()

print("Database and all tables created successfully.")