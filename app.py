from flask import Flask, render_template, request, send_file, flash, redirect, make_response, Response
import csv
import io
from datetime import datetime
import uuid
import sqlite3
from db import init_db, save_conversion_log
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 最大10MB

# データベースの初期化
conn = sqlite3.connect('isbn_results.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        isbn13 TEXT
    )
''')
conn.commit()
conn.close()

@app.before_request
def identify_user():
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        response = make_response()
        response.set_cookie('user_id', user_id)
        return response

# ---------- ISBN変換ロジック ----------
def convert_isbn(isbn10):
    # ISBN10をトリムしてハイフンを削除
    isbn10 = isbn10.strip().replace("-", "")
    # ISBN10が10桁であることを確認
    if len(isbn10) != 10:
        raise ValueError("10桁のISBNではありません")
    # ISBN10が4で始まることを確認
    if not isbn10.startswith("4"):
        raise ValueError("4で始まるISBNではありません")
    # ISBN13のコア部分を生成
    core = isbn10[:9]
    digits_str = "978" + core
    # チェックディジットを計算
    digits = [int(ch) for ch in digits_str]
    total = sum(d if i % 2 == 0 else d * 3 for i, d in enumerate(digits))
    check_digit = (10 - (total % 10)) % 10
    # 完全なISBN13を返す
    return digits_str + str(check_digit)

# ---------- フォーム入力 ----------
@app.route("/", methods=["GET", "POST"])
def index():
    user_id = request.cookies.get('user_id')
    result = []  # 変換結果を格納するリスト
    errors = []  # エラーメッセージを格納するリスト
    input_text = ""  # ユーザー入力を格納

    if request.method == "POST":
        # フォームから入力テキストを取得
        input_text = request.form.get("input_text", "")
        lines = input_text.strip().splitlines()

        logs = []  # 変換履歴を保存するリスト

        # 各行を処理
        for line in lines:
            isbn = line.strip()
            if isbn == "":
                continue  # 空行はスキップ
            try:
                # ISBN10をISBN13に変換
                isbn13 = convert_isbn(isbn)
                result.append(isbn13)  # 結果をリストに追加
                # 変換履歴をリストに追加
                logs.append((user_id, isbn, isbn13))
            except Exception as e:
                errors.append(f"{isbn}：{e}")  # エラーをリストに追加

        # まとめてデータベースに保存
        if logs:
            save_conversion_logs(logs)

        # logs.dbを削除
        try:
            if os.path.exists('web/logs.db'):
                os.remove('web/logs.db')
                init_db()  # データベースを再初期化
        except OSError as e:
            flash(f"logs.dbの削除中にエラーが発生しました: {e}")

    # テンプレートをレンダリング
    return render_template("index.html", result=result, errors=errors, input_text=input_text)

# ---------- ダウンロード ----------
@app.route("/download", methods=["POST"])
def download():
    result_data = request.form.get("result_data", "")
    if not result_data.strip():
        flash("変換結果が空です")
        return redirect("/")

    output = io.StringIO()
    output.write(result_data)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/plain",
        as_attachment=True,
        download_name=f"isbn_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )

# ---------- ファイルアップロード ----------
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("ファイルが選択されていません")
        return redirect("/")

    file = request.files["file"]
    if file.filename == "":
        flash("ファイルが選択されていません")
        return redirect("/")

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.reader(stream)

        result = []
        user_id = request.cookies.get('user_id')  # ユーザーIDを取得
        logs = []  # 変換履歴を保存するリスト

        for row in reader:
            if not row:
                continue
            isbn10 = row[0].strip()
            try:
                isbn13 = convert_isbn(isbn10)
                result.append(isbn13)
                # 変換履歴をリストに追加
                logs.append((user_id, isbn10, isbn13))
            except Exception:
                continue  # エラーがあっても無視

        if not result:
            flash("変換可能なデータが見つかりませんでした")
            return redirect("/")

        # まとめてデータベースに保存
        save_conversion_logs(logs)

        output = io.StringIO()
        output.write("\n".join(result))
        output.seek(0)

        response = send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/plain",
            as_attachment=True,
            download_name=f"isbn_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        # logs.dbを削除し、再初期化
        try:
            if os.path.exists('web/logs.db'):
                os.remove('web/logs.db')
                init_db()  # データベースを再初期化
        except OSError as e:
            flash(f"logs.dbの削除中にエラーが発生しました: {e}")

        return response

    except Exception as e:
        flash(f"アップロード処理中にエラーが発生しました: {e}")
        return redirect("/")

# 変換履歴をまとめて保存する関数
def save_conversion_logs(logs):
    conn = sqlite3.connect('web/logs.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.executemany('INSERT INTO conversion_logs (uuid, isbn10, isbn13, timestamp) VALUES (?, ?, ?, ?)',
                  [(log[0], log[1], log[2], timestamp) for log in logs])
    conn.commit()
    conn.close()

# ---------- データベース保存 ----------
def save_results_to_db(user_id, isbn13_list):
    # データベースに接続
    conn = sqlite3.connect('isbn_results.db')
    c = conn.cursor()
    # 変換結果をまとめて挿入
    c.executemany('INSERT INTO results (user_id, isbn13) VALUES (?, ?)', [(user_id, isbn13) for isbn13 in isbn13_list])
    conn.commit()  # 変更をコミット
    conn.close()  # 接続を閉じる

# BASIC認証の設定
def check_auth(username, password):
    """認証情報を確認する関数"""
    return username == 'admin' and password == 'secret'


def authenticate():
    """認証が必要な場合のレスポンス"""
    return Response(
        'ログインが必要です', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    """認証を要求するデコレータ"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ---------- 管理画面 ----------
@app.route("/admin")
@requires_auth
def admin():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    filter_uuid = request.args.get('filter_uuid')
    show_admin = request.args.get('show_admin', 'yes')
    exclude_uuid = '0a693b15-74a5-49d1-8317-bd6152a079fc' if show_admin == 'no' else None
    
    conn = sqlite3.connect('web/logs.db')
    c = conn.cursor()
    
    query = 'SELECT * FROM conversion_logs WHERE 1=1'
    params = []
    
    if start_date and end_date:
        query += ' AND date(timestamp) BETWEEN ? AND ?'
        params.extend([start_date, end_date])
    
    if filter_uuid:
        query += ' AND uuid = ?'
        params.append(filter_uuid)
    
    if exclude_uuid:
        query += ' AND uuid != ?'
        params.append(exclude_uuid)
    
    c.execute(query, params)
    logs = c.fetchall()
    conn.close()
    
    return render_template("admin.html", logs=logs)

@app.route("/download_csv")
@requires_auth  # 管理者のみアクセス可能
def download_csv():
    conn = sqlite3.connect('web/logs.db')
    c = conn.cursor()
    c.execute('SELECT * FROM conversion_logs')
    logs = c.fetchall()
    conn.close()

    # CSVファイルを生成
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'UUID', 'ISBN10', 'ISBN13', 'Timestamp'])  # ヘッダー
    writer.writerows(logs)

    # CSVファイルをクライアントに送信
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=conversion_logs.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

@app.route("/delete_log", methods=["POST"])
@requires_auth
def delete_log():
    log_id = request.form.get('log_id')
    conn = sqlite3.connect('web/logs.db')
    c = conn.cursor()
    c.execute('DELETE FROM conversion_logs WHERE id = ?', (log_id,))
    conn.commit()
    conn.close()
    flash('ログが削除されました')
    return redirect("/admin")

@app.route("/delete_filtered_logs", methods=["POST"])
@requires_auth
def delete_filtered_logs():
    filter_date = request.args.get('filter_date')
    filter_uuid = request.args.get('filter_uuid')
    show_admin = request.args.get('show_admin', 'yes')
    exclude_uuid = '0a693b15-74a5-49d1-8317-bd6152a079fc' if show_admin == 'no' else None
    
    conn = sqlite3.connect('web/logs.db')
    c = conn.cursor()
    
    query = 'DELETE FROM conversion_logs WHERE 1=1'
    params = []
    
    if filter_date:
        query += ' AND date(timestamp) = ?'
        params.append(filter_date)
    
    if filter_uuid:
        query += ' AND uuid = ?'
        params.append(filter_uuid)
    
    if exclude_uuid:
        query += ' AND uuid != ?'
        params.append(exclude_uuid)
    
    c.execute(query, params)
    conn.commit()
    conn.close()
    
    flash('絞り込み結果が削除されました')
    return redirect("/admin")

# ---------- 実行 ----------
if __name__ == "__main__":
    init_db()  # アプリケーションの起動時にデータベースを初期化
    app.run(debug=True)  # デバッグモードでアプリを実行
