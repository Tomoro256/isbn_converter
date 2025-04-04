# ISBN変換ツール（Web & GUI）

このプロジェクトは、10桁の ISBN を 13桁に変換するツールです。  
デスクトップアプリ（GUI）と Web アプリ（Flask）の2種類があります。

---

## 📁 フォルダ構成（整理済）

2025年4月現在、以下のように `gui/` と `web/` に機能別で整理されました：

```
isbn_converter/
├── gui/                  # デスクトップアプリ（FreeSimpleGUI 使用）
│   ├── isbn_gui.py       # GUI本体
│   ├── init_db.py        # DB初期化スクリプト
│   ├── build_menu.bat    # ビルドバッチ
│   ├── isbn_converter.py # 自動更新ランチャー
│   ├── isbn_gui.spec     # ビルド設定
│   ├── app/
│   │   ├── isbn_icon.ico
│   │   └── version.txt
│   └── logs/             # 一般ユーザーの変換ログ

├── web/                  # Webアプリ（Flask 使用）
│   ├── app.py            # Flaskアプリ本体
│   ├── auth.py           # 共通認証モジュール
│   ├── README.md         # このファイル
│   ├── .cursor.json      # Cursor用設定
│   ├── templates/        # HTMLテンプレート
│   └── static/           # CSS/JS/画像 など

```

---

## 🚀 Webアプリの起動

```bash
cd web
python app.py
```

---

## 🧩 開発環境

- Python 3.10+
- Flask
- FreeSimpleGUI（GUI版）
- SQLite3
- Render（Webホスティング予定）

---

## 🔐 認証・ログイン機能

現在、メールアドレスによるログイン／ユーザー管理を追加予定です。

---

## 🧹 バージョン管理と構成管理

- `.bat` ファイルで自動整理済み
- `dist/` や `build/` フォルダも自動削除対応済み


---

## 🔄 GUI版 → Web版への機能移植について

現在、GUI版（`gui/isbn_gui.py`）に実装されている以下の機能を、順次 Web版にも移植予定です：

- ユーザーログイン（メールアドレス・パスワードによる認証）
- サインアップ（新規ユーザー登録と確認）
- ログイン履歴の保存と表示（管理者専用）
- ISBN変換履歴の記録・閲覧（管理者専用）
- 一般ユーザーのログを Google ドライブに送信
- 管理者によるログの一括集約（logs/*.db → data.db）

これらの機能は、`gui/isbn_gui.py` 内の関数・処理を参照して実装を進めています。

Web版の対応状況については今後の開発ログやコミット履歴で追っていきます。


---

## 🗂 Web版でのログ保存方針

GUI版では、一般ユーザーの変換ログをローカルで `.db` に保存し、Googleドライブへ送信する設計でしたが、Web版では以下のように設計方針を変更しています：

### ✅ Web版のログ保存の方針

- **一般ユーザーの変換ログ** は Webサーバー上の SQLite DB に直接保存
- **管理者** は同じ DB を参照して変換履歴を閲覧・管理（統合処理は不要）

この方式により、Google Drive 連携や OAuth 認証を避けつつ、安定したログ保存・一元管理が可能になります。

### 🔧 想定構成例

```
web/
├── data/
│   └── conversions.db  ← 全ユーザーの変換ログを保存
```

今後の運用次第では、SQLite から PostgreSQL（Render や Supabase）への移行も視野に入れています。
