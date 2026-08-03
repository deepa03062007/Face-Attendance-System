import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

print("----- Students Table -----")
cursor.execute("SELECT * FROM students")
for row in cursor.fetchall():
    print(row)

print("\n----- Attendance Table -----")
cursor.execute("SELECT * FROM attendance")
for row in cursor.fetchall():
    print(row)

conn.close()