import sqlite3

print("--- Running Database Diagnostics ---")
try:
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    print("\n[1] USERS table (Students):")
    users = list(cursor.execute("SELECT id, username FROM users"))
    if users:
        for row in users: print(f"  - ID: {row[0]}, Username: {row[1]}")
    else: print("  - (No students registered)")

    print("\n[2] CLASSES table:")
    classes = list(cursor.execute("SELECT id, class_name, teacher_id FROM classes"))
    if classes:
        for row in classes: print(f"  - Class ID: {row[0]}, Name: '{row[1]}', Teacher ID: {row[2]}")
    else: print("  - (No classes created)")

    print("\n[3] ENROLLMENTS table (Which student is in which class):")
    enrollments = list(cursor.execute("SELECT user_id, class_id FROM enrollments"))
    if enrollments:
        for row in enrollments: print(f"  - User ID: {row[0]} is enrolled in Class ID: {row[1]}")
    else: print("  - (No students are enrolled in any classes)")

    print("\n[4] QUIZZES table (Created by Teacher):")
    quizzes = list(cursor.execute("SELECT id, name, teacher_id FROM quizzes"))
    if quizzes:
        for row in quizzes: print(f"  - Quiz ID: {row[0]}, Name: '{row[1]}', Teacher ID: {row[2]}")
    else: print("  - (No quizzes have been created by the teacher)")

    print("\n[5] ASSIGNMENTS table (Which quiz is assigned to which class):")
    assignments = list(cursor.execute("SELECT quiz_id, class_id FROM assignments"))
    if assignments:
        for row in assignments: print(f"  - Quiz ID: {row[0]} is assigned to Class ID: {row[1]}")
    else: print("  - (No quizzes have been assigned to any classes)")

    conn.close()
    print("\n--- Diagnostics Complete ---")

except Exception as e:
    print(f"\nAn error occurred: {e}")