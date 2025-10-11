import sqlite3

# This script is already set up for user_id = 1, which is correct for 'phani'.
student_id_to_enroll = 1
class_id_to_enroll = 1    # The sample teacher's class is ID 1.

print(f"--- Enrolling User ID: {student_id_to_enroll} into Class ID: {class_id_to_enroll} ---")

try:
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    # This command adds the enrollment only if it doesn't already exist.
    cursor.execute(
        "INSERT OR IGNORE INTO enrollments (user_id, class_id) VALUES (?, ?)",
        (student_id_to_enroll, class_id_to_enroll)
    )
    
    conn.commit()
    conn.close()
    print("\n✅ Enrollment successful!")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")