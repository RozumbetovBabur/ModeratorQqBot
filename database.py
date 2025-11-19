import psycopg2
from psycopg2 import pool
from datetime import datetime, timedelta

# 🔐 Postgres ulanish ma'lumotlari
DB_NAME = NAME
DB_USER = USERNAME
DB_PASSWORD = PASSWORD
DB_HOST = SERVER_HOST
DB_PORT = PORT

# ✅ Connection pool yaratish (global)
db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=50,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

def get_connection():
    """Connection pooldan bitta ulanishni olish."""
    return db_pool.getconn()

def release_connection(conn):
    """Connection poolga qaytarish."""
    db_pool.putconn(conn)


def add_user(user_id, full_name, username, group_id):
    if username:
        username = f"@{username}" if not username.startswith("@") else username

    joined_at = datetime.now()  # PostgreSQL TIMESTAMP uchun bu yetarli

    conn = None
    try:
        conn = get_connection()  # 🔁 Ulanishni bu yerda chaqiramiz
        cursor = conn.cursor()

        # print("✅ [add_user] Bog‘lanish muvaffaqiyatli")

        cursor.execute("""
            INSERT INTO users (user_id, full_name, username, group_id, joined_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, group_id) DO NOTHING
        """, (user_id, full_name, username, group_id, joined_at))

        conn.commit()
        # print(f"✅ [add_user] Ma’lumot yozildi: {user_id=}, {full_name=}, {username=}, {group_id=}, {joined_at=}")
        cursor.close()
    except Exception as e:
        print(f"[add_user] Xatolik: {e}")

    finally:
        if conn:
            release_connection(conn)


def increment_invite(user_id, count=1):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET invited_count = invited_count + %s WHERE user_id = %s", (count, user_id))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"[increment_invite] Xatolik: {e}")
    finally:
        if conn:
            release_connection(conn)


def get_invited_count(user_id):
    conn = None
    try:
        conn = get_connection()  # 🔁 Pooldan ulanishni olish
        cursor = conn.cursor()
        cursor.execute("SELECT invited_count FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"[get_invited_count] Xatolik: {e}")
        return 0
    finally:
        if conn:
            release_connection(conn)  # 🔁 Poolga ulanishni qaytarish


def get_all_users():
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, invited_count FROM users")
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"[get_all_users] Xatolik: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)


def init_db():
    conn = None
    cursor = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()

        # user yaratish
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT,
                        full_name TEXT,
                        username TEXT,
                        group_id BIGINT,
                        invited_count INTEGER DEFAULT 0,
                        joined_at TIMESTAMP,
                        PRIMARY KEY(user_id, group_id)
                    )
                ''')

        # Jadval yaratish
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id BIGINT PRIMARY KEY,
                group_name TEXT,
                created_at TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                user_id BIGINT,
                username TEXT,
                phone_number TEXT,
                group_id BIGINT,
                PRIMARY KEY (user_id, group_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planned_invites (
                group_id BIGINT PRIMARY KEY,
                planned_count INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS imtiyozli_users (
                user_id BIGINT,
                username TEXT,
                group_id BIGINT,
                granted_at TIMESTAMP,
                PRIMARY KEY(user_id, group_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT,
                full_name TEXT,
                username TEXT,
                group_id BIGINT,
                invited_count INTEGER DEFAULT 0,
                joined_at TIMESTAMP,
                PRIMARY KEY(user_id, group_id)
            )
        ''')

        conn.commit()
        # print("✅ [init_db] Barcha jadvallar muvaffaqiyatli yaratildi.")

    except Exception as e:
        print(f"[init_db] Xatolik: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)



def is_admin_from_db(user_id):
    conn = None
    cursor = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM admin WHERE user_id = %s", (user_id,))
        exists = cursor.fetchone() is not None
        return exists
    except Exception as e:
        print(f"[is_admin_from_db] Xatolik: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)


def save_group(group_id, group_name):
    conn = None
    cursor = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO groups (group_id, group_name, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (group_id) DO NOTHING
        ''', (group_id, group_name, datetime.now()))
        conn.commit()
    except Exception as e:
        print(f"[save_group] Xatolik: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)


def save_admin(user_id, username, phone_number, group_id):
    conn = None
    cursor = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO admin (user_id, username, phone_number, group_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, group_id) DO UPDATE
            SET username = EXCLUDED.username,
                phone_number = EXCLUDED.phone_number
        ''', (user_id, username, phone_number, group_id))
        conn.commit()
    except Exception as e:
        print(f"[save_admin] Xatolik: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)



def is_admin(user_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM admin WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        return [row[0] for row in rows] if rows else []
    except Exception as e:
        print(f"[is_admin] Xatolik: {e}")
        return []
    finally:
        if conn:
            release_connection(conn)


def get_group_names(group_ids):
    conn = None
    cursor = None
    group_names = []
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        for gid in group_ids:
            cursor.execute("SELECT group_name FROM groups WHERE group_id = %s", (gid,))
            row = cursor.fetchone()
            if row:
                group_names.append(row[0])
    except Exception as e:
        print(f"[get_group_names] Xatolik: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)
    return group_names




def get_users_by_date_range(group_ids, days):
    conn = None
    cursor = None
    users = []

    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)
        format_strings = ','.join(['%s'] * len(group_ids))
        query = f'''
            SELECT full_name, username, invited_count, joined_at FROM users
            WHERE group_id IN ({format_strings}) AND joined_at >= %s
        '''
        cursor.execute(query, (*group_ids, cutoff_date))
        users = cursor.fetchall()

    except Exception as e:
        print(f"[get_users_by_date_range] Xatolik: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)

    return users




def get_users_by_exact_range(group_ids, from_days_ago, to_days_ago):
    conn = None
    cursor = None
    users = []

    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()

        now = datetime.now()
        start_date = now - timedelta(days=to_days_ago)
        end_date = now - timedelta(days=from_days_ago)

        format_strings = ','.join(['%s'] * len(group_ids))
        query = f'''
            SELECT full_name, username, invited_count, joined_at FROM users
            WHERE group_id IN ({format_strings})
            AND joined_at >= %s AND joined_at < %s
        '''
        cursor.execute(query, (*group_ids, start_date, end_date))
        users = cursor.fetchall()

    except Exception as e:
        print(f"[get_users_by_exact_range] Xatolik: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)

    return users



def get_group_users(group_ids):
    conn = None
    cursor = None
    users = []

    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()

        format_strings = ','.join(['%s'] * len(group_ids))
        query = f'''
            SELECT full_name, username, invited_count FROM users
            WHERE group_id IN ({format_strings})
        '''
        cursor.execute(query, group_ids)
        users = cursor.fetchall()

    except Exception as e:
        print(f"[get_group_users] Xatolik: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)

    return users



def clear_invited_counts_by_group_ids(group_ids):
    if not group_ids:
        return

    conn = None
    cursor = None

    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()

        for group_id in group_ids:
            cursor.execute("UPDATE users SET invited_count = 0 WHERE group_id = %s", (group_id,))

        conn.commit()

    except Exception as e:
        print(f"[clear_invited_counts_by_group_ids] Xatolik: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)



def get_planned_count_by_group_id(group_id):
    conn = None
    cursor = None

    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()

        cursor.execute("SELECT planned_count FROM planned_invites WHERE group_id = %s", (group_id,))
        result = cursor.fetchone()

        return result[0] if result else 10  # Default qiymat 10

    except Exception as e:
        print(f"[get_planned_count_by_group_id] Xatolik: {e}")
        return 10

    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)




def is_privileged_user(user_id, group_id):
    conn = None
    cursor = None

    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM imtiyozli_users WHERE user_id = %s AND group_id = %s",
            (user_id, group_id)
        )
        result = cursor.fetchone()
        return result is not None

    except Exception as e:
        print(f"[is_privileged_user] Xatolik: {e}")
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)


