from flask import Flask, render_template, request, send_file, flash, redirect
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 最大10MB

# ---------- ISBN変換ロジック ----------
def convert_isbn(isbn10):
    isbn10 = isbn10.strip().replace("-", "")
    if len(isbn10) != 10:
        raise ValueError("10桁のISBNではありません")
    if not isbn10.startswith("4"):
        raise ValueError("4で始まるISBNではありません")
    core = isbn10[:9]
    digits_str = "978" + core
    digits = [int(ch) for ch in digits_str]
    total = sum(d if i % 2 == 0 else d * 3 for i, d in enumerate(digits))
    check_digit = (10 - (total % 10)) % 10
    return digits_str + str(check_digit)

# ---------- フォーム入力 ----------
@app.route("/", methods=["GET", "POST"])
def index():
    result = []
    errors = []
    input_text = ""

    if request.method == "POST":
        input_text = request.form.get("input_text", "")
        lines = input_text.strip().splitlines()

        if len(lines) > 1000:
            flash("最大1000件まで入力できます")
        else:
            for line in lines:
                isbn = line.strip()
                if isbn == "":
                    continue
                try:
                    isbn13 = convert_isbn(isbn)
                    result.append(isbn13)
                except Exception as e:
                    errors.append(f"{isbn}：{e}")

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

        for row in reader:
            if not row:
                continue
            isbn10 = row[0].strip()
            try:
                isbn13 = convert_isbn(isbn10)
                result.append(isbn13)
            except Exception:
                continue  # エラーがあっても無視

        if not result:
            flash("変換可能なデータが見つかりませんでした")
            return redirect("/")

        output = io.StringIO()
        output.write("\n".join(result))
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/plain",
            as_attachment=True,
            download_name=f"isbn_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

    except Exception as e:
        flash(f"アップロード処理中にエラーが発生しました: {e}")
        return redirect("/")

# ---------- 実行 ----------
if __name__ == "__main__":
    app.run(debug=True)
