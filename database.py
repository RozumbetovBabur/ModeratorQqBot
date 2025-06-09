import sqlite3
from datetime import datetime

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
    full_name TEXT,
    username TEXT,
    group_id INTEGER,
    invited_count INTEGER DEFAULT 0,
    PRIMARY KEY(user_id, group_id)
)
""")
conn.commit()

# def add_user(user_id, full_name):
#     cursor.execute("INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", (user_id, full_name))
#     conn.commit()

def add_user(user_id, full_name, username=None, group_id=None):
    if username:
        username = f"@{username}" if not username.startswith("@") else username
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, full_name, username, group_id) VALUES (?, ?, ?, ?)",
        (user_id, full_name, username, group_id)
    )
    conn.commit()


def increment_invite(user_id, count=1):
    cursor.execute("UPDATE users SET invited_count = invited_count + ? WHERE user_id = ?", (count, user_id,))
    conn.commit()

def get_invited_count(user_id):
    cursor.execute("SELECT invited_count FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_all_users():
    cursor.execute("SELECT full_name, invited_count FROM users")
    return cursor.fetchall()

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Guruhlar jadvali
    c.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                group_name TEXT,
                created_at TEXT
            )
        ''')

    # Adminlar jadvali (har adminga group_id biriktiriladi)
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            user_id INTEGER,
            username TEXT,
            phone_number TEXT,
            group_id INTEGER,
            PRIMARY KEY (user_id, group_id)
        )
    ''')
    conn.commit()
    conn.close()

# def save_admin(user_id, username, phone_number):
#     conn = sqlite3.connect("users.db")
#     c = conn.cursor()
#     c.execute('''
#         INSERT OR REPLACE INTO admin (user_id, username, phone_number)
#         VALUES (?, ?, ?)
#     ''', (user_id, username, phone_number))
#     conn.commit()
#     conn.close()

def is_admin_from_db(user_id):
    cursor.execute("SELECT user_id FROM admin WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def save_group(group_id, group_name):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute('''
        INSERT OR IGNORE INTO groups (group_id, group_name, created_at)
        VALUES (?, ?, ?)
    ''', (group_id, group_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()
    conn.close()

def save_admin(user_id, username, phone_number, group_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute('''
        INSERT OR REPLACE INTO admin (user_id, username, phone_number, group_id)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, phone_number, group_id))

    conn.commit()
    conn.close()

def is_admin(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT group_id FROM admin WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows] if rows else None

def get_group_names(group_ids):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    group_names = []
    for gid in group_ids:
        cursor.execute("SELECT group_name FROM groups WHERE group_id = ?", (gid,))
        row = cursor.fetchone()
        if row:
            group_names.append(row[0])
    conn.close()
    return group_names

def get_group_users(group_ids):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    format_strings = ",".join(["?"] * len(group_ids))
    cursor.execute(f'''
        SELECT full_name, username, invited_count FROM users
        WHERE group_id IN ({format_strings})
    ''', group_ids)

    users = cursor.fetchall()
    conn.close()
    return users

def clear_invited_counts_by_group_ids(group_ids):
    """
    Faqat berilgan group_id lar bo‘yicha users jadvalidagi invited_count ni 0 ga tenglashtiradi
    """
    if not group_ids:
        return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    for group_id in group_ids:
        cursor.execute("UPDATE users SET invited_count = 0 WHERE group_id = ?", (group_id,))
    conn.commit()
    conn.close()

def get_planned_count_by_group_id(group_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT planned_count FROM planned_invites WHERE group_id = ?", (group_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]  # planned_count ni qaytaradi
    else:
        return 10  # agar yo'q bo‘lsa default 10 qaytariladi