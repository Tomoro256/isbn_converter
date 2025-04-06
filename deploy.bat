@echo off
setlocal enabledelayedexpansion
title GitHub Release and Push Script

REM ブラウザでリリースページを開く
start https://github.com/Tomoro256/isbn_converter/releases

REM 不要なファイルやディレクトリを削除
echo Deleting unnecessary files and directories...
if exist __pycache__ rmdir /s /q __pycache__
if exist venv rmdir /s /q venv
if exist app_data.db del /q app_data.db

REM GitHubリポジトリのURL
set REPO_URL=https://github.com/Tomoro256/isbn_converter.git

REM リモートURLの確認
echo Checking remote URL...
git remote -v

REM ユーザーにバージョン番号を入力させる
set /p VERSION="バージョンを入力してください: "

REM GitHub CLIでのリリースメッセージ
set RELEASE_MSG="Release version %VERSION%"

REM Gitの設定
git add .
git commit --allow-empty -m "Update for version %VERSION%"

REM 既存のタグを削除して新しいタグを作成
git tag -d %VERSION%
git push origin :refs/tags/%VERSION%
git tag %VERSION%

REM ブランチのプッシュ
echo Pushing to remote repository...
git push origin master

REM タグのプッシュ
echo Pushing tags to remote repository...
git push origin --tags

REM GitHub CLIを使用して新しいリリースを作成
gh release create %VERSION% --title "Version %VERSION%" --notes %RELEASE_MSG%

echo リリース %VERSION% が作成され、GitHubにプッシュされました。
pause