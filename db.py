# db.py
import sqlite3
from datetime import datetime
import os

# データベースの初期化
# logs.dbに変換履歴を保存するためのテーブルを作成

def init_db():
    # ディレクトリが存在しない場合は作成
    if not os.path.exists('web'):
        os.makedirs('web')
    
    conn = sqlite3.connect('web/logs.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT,
            isbn10 TEXT,
            isbn13 TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# 変換履歴を保存する関数
def save_conversion_log(uuid, isbn10, isbn13):
    conn = sqlite3.connect('web/logs.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO conversion_logs (uuid, isbn10, isbn13, timestamp) VALUES (?, ?, ?, ?)',
              (uuid, isbn10, isbn13, timestamp))
    conn.commit()
    conn.close()