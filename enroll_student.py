import sqlite3

# --- CONFIGURE THIS ---
student_username_to_enroll = "phani"  # <-- IMPORTANT: Change this to your student's username
class_id_to_enroll = 1                # (The sample teacher's class has ID 1)


print(f"--- Attempting to enroll user '{student_username_to_enroll}' ---")
conn = None # Initialize conn to None
try:
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # 1. Find the student's ID from their username
    user_row = cursor.execute("SELECT id FROM users WHERE username = ?", (student_username_to_enroll,)).fetchone()

    if not user_row:
        print(f"❌ ERROR: Student with username '{student_username_to_enroll}' was not found in the database.")
        print("Please make sure you have registered this user through the app first.")
        exit()

    student_id = user_row[0]
    print(f"Found student '{student_username_to_enroll}' with ID: {student_id}")

    # 2. Insert the enrollment link into the database
    print(f"Enrolling User ID {student_id} into Class ID {class_id_to_enroll}...")
    cursor.execute(
        "INSERT OR IGNORE INTO enrollments (user_id, class_id) VALUES (?, ?)",
        (student_id, class_id_to_enroll)
    )

    conn.commit()
    print("✅ Enrollment successful or already exists!")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")
finally:
    if conn:
        conn.close()