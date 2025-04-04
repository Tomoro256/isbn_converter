# auth.py
# サインアップ・ログイン・ログアウトを管理
# SQLiteを使い、ユーザー情報を users テーブルに保存
# メールアドレスをユーザー名として使用


import sqlite3
import bcrypt
import secrets
from datetime import datetime, timedelta

# --- DB接続と初期化 ---
def init_db(db_path='users.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # users テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ログイン履歴テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            success INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # パスワードリセットトークンテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reset_tokens (
            email TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# --- ユーザー登録 ---
def register_user(email, password, is_admin=False, db_path='users.db'):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute('''
            INSERT INTO users (email, password_hash, is_admin)
            VALUES (?, ?, ?)
        ''', (email, password_hash, int(is_admin)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# --- ログイン認証（＋ログ記録） ---
def check_login(email, password, db_path='users.db'):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
    result = cursor.fetchone()

    success = False
    if result and bcrypt.checkpw(password.encode(), result[0].encode()):
        success = True

    # ログイン履歴記録
    cursor.execute('''
        INSERT INTO login_logs (email, success)
        VALUES (?, ?)
    ''', (email, int(success)))
    conn.commit()
    conn.close()

    return success

# --- 管理者かどうか判定 ---
def is_admin(email, db_path='users.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE email = ?', (email,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

# --- パスワード変更 ---
def change_password(email, old_password, new_password, db_path='users.db'):
    if not check_login(email, old_password, db_path):
        return False

    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?', (new_hash, email))
    conn.commit()
    conn.close()
    return True

# --- ユーザー一覧取得（管理者用） ---
def get_all_users(db_path='users.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT email, is_admin, created_at FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

# --- ログイン履歴の取得（管理者用） ---
def get_login_logs(db_path='users.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT email, success, timestamp FROM login_logs ORDER BY timestamp DESC')
    logs = cursor.fetchall()
    conn.close()
    return logs

# --- パスワードリセット用トークン生成（ワンタイム） ---
def generate_reset_token(email, db_path='users.db', expires_minutes=15):
    init_db(db_path)
    token = secrets.token_urlsafe(16)
    expires_at = (datetime.now() + timedelta(minutes=expires_minutes)).isoformat()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO reset_tokens (email, token, expires_at)
        VALUES (?, ?, ?)
    ''', (email, token, expires_at))
    conn.commit()
    conn.close()

    return token  # Flask側でこのトークンをメール送信に利用

# --- トークンの有効性チェック ---
def verify_reset_token(email, token, db_path='users.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT token, expires_at FROM reset_tokens WHERE email = ?', (email,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return False

    stored_token, expires_at = result
    if stored_token != token:
        return False

    return datetime.now() <= datetime.fromisoformat(expires_at)

# --- パスワードリセット実行 ---
def reset_password(email, token, new_password, db_path='users.db'):
    if not verify_reset_token(email, token, db_path):
        return False

    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?', (new_hash, email))
    cursor.execute('DELETE FROM reset_tokens WHERE email = ?', (email,))
    conn.commit()
    conn.close()
    return True

# --- 動作テスト用メインブロック ---
if __name__ == '__main__':
    # 初回用テスト（任意）
    email = "admin@example.com"
    password = "admin123"

    print("=== 登録 ===")
    if register_user(email, password, is_admin=True):
        print("登録成功")
    else:
        print("既に登録済み")

    print("\n=== ログイン ===")
    if check_login(email, password):
        print("ログイン成功")
        if is_admin(email):
            print("管理者です")
    else:
        print("ログイン失敗")

    print("\n=== トークン生成 → パスワード再設定 ===")
    token = generate_reset_token(email)
    print("生成されたトークン:", token)
    if reset_password(email, token, "newpass123"):
        print("パスワードリセット成功")
    else:
        print("パスワードリセット失敗")

    print("\n=== 全ユーザー一覧 ===")
    for user in get_all_users():
        print(user)

    print("\n=== ログイン履歴 ===")
    for log in get_login_logs():
        print(log)
