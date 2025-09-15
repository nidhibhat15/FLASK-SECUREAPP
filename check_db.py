import sqlite3

conn = sqlite3.connect("instance/security.db")
cursor = conn.cursor()

# See all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# Inspect the users table
cursor.execute("PRAGMA table_info(users);")
print("Users table columns:", cursor.fetchall())

# Show any existing users
cursor.execute("SELECT * FROM users;")
print("Users:", cursor.fetchall())

conn.close()
