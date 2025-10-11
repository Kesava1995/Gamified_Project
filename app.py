from flask import Flask, request, jsonify, render_template
import sqlite3
from transformers import pipeline
import json


print("Loading English to French translation model...")
translator_en_fr = pipeline("translation_en_to_fr", model="Helsinki-NLP/opus-mt-en-fr")
print("Translation model loaded successfully.")

# You can add more models for other languages here
# print("Loading English to German translation model...")
# translator_en_de = pipeline("translation_en_to_de", model="Helsinki-NLP/opus-mt-en-de")
# print("German model loaded.")
app = Flask(__name__, static_folder='static', static_url_path='')

def db_connection():
    """Helper function to connect to the database."""
    conn = sqlite3.connect('mydatabase.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Main Page ---
@app.route('/')
def index():
    """Serve the main HTML file from the 'static' folder."""
    return app.send_static_file('index.html')

# --- API for User Registration ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']

    password = data['password']

    conn = db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return jsonify({"success": True, "message": "User registered!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already taken."}), 409
    finally:
        conn.close()

# --- API for User Login ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    ).fetchone()
    conn.close()

    if user:
        return jsonify({"success": True, "user_id": user['id'], "username": user['username']})
    else:
        return jsonify({"success": False, "message": "Invalid credentials."}), 401


def check_and_award_badges(user_id, subject, score):
    """Checks achievements and awards badges to a user."""
    conn = db_connection()
    cursor = conn.cursor()

    # Rule 1: Award subject master badge for a perfect score
    if score == 20: # Assuming 20 questions
        badge_name = f"{subject} Master" if subject != "Physics" else "Physics Phenom"
        cursor.execute("SELECT id FROM badges WHERE name = ?", (badge_name,))
        badge = cursor.fetchone()
        if badge:
            cursor.execute("INSERT OR IGNORE INTO user_badges (user_id, badge_id) VALUES (?, ?)", (user_id, badge['id']))

    # Rule 2: Award enthusiast badge after 3 quizzes
    total_quizzes = cursor.execute("SELECT COUNT(*) FROM scores WHERE user_id = ?", (user_id,)).fetchone()[0]
    if total_quizzes >= 3:
        cursor.execute("SELECT id FROM badges WHERE name = 'Quiz Enthusiast'")
        badge = cursor.fetchone()
        if badge:
            cursor.execute("INSERT OR IGNORE INTO user_badges (user_id, badge_id) VALUES (?, ?)", (user_id, badge['id']))

    conn.commit()
    conn.close()

# --- API to Save Score ---
@app.route('/api/scores', methods=['POST'])
def save_score():
    data = request.get_json()
    user_id = data['user_id']
    subject = data['subject']
    score = data['score']

    conn = db_connection()
    conn.execute(
        "INSERT INTO scores (user_id, subject, score) VALUES (?, ?, ?)",
        (user_id, subject, score)
    )
    conn.commit()
    conn.close()
    
    check_and_award_badges(user_id, subject, score) # Check for new badges
    
    return jsonify({"success": True, "message": "Score saved!"})


@app.route('/api/get_badges/<int:user_id>', methods=['GET'])
def get_user_badges(user_id):
    conn = db_connection()
    badges = conn.execute("""
        SELECT b.name, b.description, b.icon
        FROM badges b
        JOIN user_badges ub ON b.id = ub.badge_id
        WHERE ub.user_id = ?
    """, (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in badges])

@app.route('/api/get_scores/<int:user_id>', methods=['GET'])
def get_scores(user_id):
    conn = db_connection()
    scores = conn.execute(
        "SELECT subject, score, timestamp FROM scores WHERE user_id = ? ORDER BY timestamp DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    # Convert the database rows to a list of dictionaries
    scores_list = [dict(row) for row in scores]
    return jsonify(scores_list)

# ===============================================
# ========== TEACHER DASHBOARD ROUTES ===========
# ===============================================

@app.route('/teacher')
def teacher_portal():
    """Serves the main teacher dashboard HTML file."""
    return app.send_static_file('teacher.html')

@app.route('/api/teacher/login', methods=['POST'])
def teacher_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = db_connection()
    teacher = conn.execute(
        "SELECT * FROM teachers WHERE username = ? AND password = ?",
        (username, password)
    ).fetchone()

    if teacher:
        # Fetch classes managed by this teacher
        classes = conn.execute(
            "SELECT id, class_name FROM classes WHERE teacher_id = ?",
            (teacher['id'],)
        ).fetchall()
        conn.close()
        return jsonify({
            "success": True,
            "teacher_id": teacher['id'],
            "username": teacher['username'],
            "classes": [dict(c) for c in classes]
        })
    else:
        conn.close()
        return jsonify({"success": False, "message": "Invalid credentials"}), 401


@app.route('/api/teacher/analytics/<int:class_id>', methods=['GET'])
def get_class_analytics(class_id):
    conn = db_connection()
    analytics_data = conn.execute("""
        SELECT
            u.username,
            s.subject,
            AVG(s.score) as average_score
        FROM scores s
        JOIN users u ON s.user_id = u.id
        JOIN enrollments e ON u.id = e.user_id
        WHERE e.class_id = ?
        GROUP BY u.username, s.subject
        ORDER BY u.username
    """, (class_id,)).fetchall()
    conn.close()

    if not analytics_data:
        return jsonify({"error": "No data found for this class."}), 404

    # Format the data for Chart.js
    labels = []
    datasets = {} # Using a dict to group scores by subject
    
    for row in analytics_data:
        if row['username'] not in labels:
            labels.append(row['username'])
        
        if row['subject'] not in datasets:
            datasets[row['subject']] = {
                'label': row['subject'],
                'data': [],
                'backgroundColor': f'rgba({hash(row["subject"]) % 255}, {hash(row["subject"]*2) % 255}, {hash(row["subject"]*3) % 255}, 0.5)'
            }
    
    # Fill in the data for each student
    for label in labels:
        for subject in datasets:
            # Find the score for this student and subject, or default to 0
            score_row = next((r for r in analytics_data if r['username'] == label and r['subject'] == subject), None)
            score = score_row['average_score'] if score_row else 0
            datasets[subject]['data'].append(score)

    chart_data = {
        'labels': labels,
        'datasets': list(datasets.values())
    }
    
    return jsonify(chart_data)


# ====== QUIZ CREATION & ASSIGNMENT ROUTES ======
# ===============================================
import json

@app.route('/api/teacher/quizzes', methods=['GET', 'POST'])
def handle_quizzes():
    # POST: Create a new quiz
    if request.method == 'POST':
        data = request.get_json()
        conn = db_connection()
        cursor = conn.execute(
            "INSERT INTO quizzes (name, teacher_id) VALUES (?, ?)",
            (data['name'], data['teacher_id'])
        )
        conn.commit()
        new_quiz_id = cursor.lastrowid
        conn.close()
        return jsonify({"success": True, "quiz_id": new_quiz_id, "name": data['name']}), 201
    
    # GET: Fetch all quizzes for a teacher
    else:
        teacher_id = request.args.get('teacher_id')
        conn = db_connection()
        quizzes = conn.execute("SELECT id, name FROM quizzes WHERE teacher_id = ?", (teacher_id,)).fetchall()
        conn.close()
        return jsonify([dict(q) for q in quizzes])

@app.route('/api/teacher/questions', methods=['POST'])
def add_question():
    data = request.get_json()
    # Convert options list to a JSON string for storage
    options_json = json.dumps(data['options'])
    
    conn = db_connection()
    conn.execute(
        "INSERT INTO questions (quiz_id, question_text, options, correct_answer) VALUES (?, ?, ?, ?)",
        (data['quiz_id'], data['question_text'], options_json, data['correct_answer'])
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Question added successfully."})

@app.route('/api/teacher/assign', methods=['POST'])
def assign_quiz():
    data = request.get_json()
    conn = db_connection()
    conn.execute("INSERT INTO assignments (quiz_id, class_id) VALUES (?, ?)", (data['quiz_id'], data['class_id']))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Quiz assigned successfully."})

# --- Student-facing routes for custom quizzes ---

@app.route('/api/student/assignments/<int:user_id>', methods=['GET'])
def get_student_assignments(user_id):
    print(f"\n--- DEBUG: Fetching assignments for user_id: {user_id} ---")
    conn = db_connection()
    assignments = conn.execute("""
        SELECT q.id, q.name
        FROM quizzes q
        JOIN assignments a ON q.id = a.quiz_id
        JOIN enrollments e ON a.class_id = e.class_id
        WHERE e.user_id = ?
    """, (user_id,)).fetchall()
    conn.close()
    
    assignments_list = [dict(a) for a in assignments]
    
    if assignments_list:
        print(f"--- DEBUG: Found {len(assignments_list)} assignments: {assignments_list} ---")
    else:
        print("--- DEBUG: Found NO assignments for this user. ---")
        
    return jsonify(assignments_list)

@app.route('/api/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz_questions(quiz_id):

    target_lang = request.args.get('lang', 'en')
    
    conn = db_connection()
    questions_raw = conn.execute("SELECT question_text, options, correct_answer FROM questions WHERE quiz_id = ?", (quiz_id,)).fetchall()
    conn.close()

    if target_lang == 'en':
        questions_processed = []
        for q in questions_raw:
            questions_processed.append({
                "q": q['question_text'],
                "o": json.loads(q['options']),
                "a": q['correct_answer']
            })
        return jsonify(questions_processed)

    # --- AI TRANSLATION LOGIC ---
    print(f"--- AI: Translating custom quiz ID {quiz_id} to '{target_lang}' ---")
    
    # 1. Collect all texts to be translated
    texts_to_translate = []
    original_questions = []
    for q in questions_raw:
        question_data = {
            "q": q['question_text'],
            "o": json.loads(q['options']),
            "a": q['correct_answer']
        }
        original_questions.append(question_data)
        texts_to_translate.append(question_data['q'])
        texts_to_translate.extend(question_data['o'])

    # 2. Use the AI translator model
    if target_lang == 'fr' and 'translator_en_fr' in globals():
        translated = translator_en_fr(texts_to_translate)
    else:
        # If model for the target lang doesn't exist, return English
        return jsonify(original_questions) 
        
    translated_texts = [item['translation_text'] for item in translated]
    
    # 3. Reconstruct the quiz with translated text
    text_index = 0
    translated_quiz = []
    for original_q in original_questions:
        translated_q_text = translated_texts[text_index]
        text_index += 1
        
        translated_options = []
        for _ in original_q['o']:
            translated_options.append(translated_texts[text_index])
            text_index += 1
            
        correct_index = original_q['o'].index(original_q['a'])
        translated_correct_answer = translated_options[correct_index]
        
        translated_quiz.append({
            "q": translated_q_text,
            "o": translated_options,
            "a": translated_correct_answer
        })
        
    return jsonify(translated_quiz)

@app.route('/api/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    text_to_translate = data.get('text')
    target_lang = data.get('target_lang', 'fr') # Default to French

    if not text_to_translate:
        return jsonify({"error": "No text provided"}), 400

    if target_lang == 'fr':
        translator = translator_en_fr
    # elif target_lang == 'de':
    #     translator = translator_en_de
    else:
        return jsonify({"error": f"Translation to '{target_lang}' not supported."}), 400


    texts = text_to_translate if isinstance(text_to_translate, list) else [text_to_translate]
    
    translated = translator(texts)    
    translated_texts = [item['translation_text'] for item in translated]
    
    return jsonify({"translated_texts": translated_texts})


# ======== CLASS ENROLLMENT MANAGEMENT ========
@app.route('/api/teacher/unassigned_students/<int:class_id>', methods=['GET'])
def get_unassigned_students(class_id):
    """Fetches all students who are NOT already in the specified class."""
    conn = db_connection()
    students = conn.execute("""
        SELECT id, username FROM users
        WHERE id NOT IN (SELECT user_id FROM enrollments WHERE class_id = ?)
    """, (class_id,)).fetchall()
    conn.close()
    return jsonify([dict(s) for s in students])

@app.route('/api/teacher/enroll', methods=['POST'])
def enroll_student_api():
    """Enrolls a student into a class."""
    data = request.get_json()
    user_id = data.get('user_id')
    class_id = data.get('class_id')
    
    conn = db_connection()
    try:
        conn.execute("INSERT INTO enrollments (user_id, class_id) VALUES (?, ?)", (user_id, class_id))
        conn.commit()
        return jsonify({"success": True, "message": "Student enrolled successfully."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Student is already in this class."}), 409
    finally:
        conn.close()

if __name__ == '__main__':
    # Use 0.0.0.0 to make it accessible outside the VM/container
    app.run(host='0.0.0.0', port=8000, debug=True)