@echo off
setlocal enabledelayedexpansion
title GitHub Release and Push Script

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

REM 最新のタグを取得
for /f "delims=" %%i in ('git describe --tags --abbrev=0 2^>nul') do set LATEST_TAG=%%i

REM バージョン番号を自動インクリメント
if "%LATEST_TAG%"=="" (
    set VERSION=0.1.0
) else (
    for /f "tokens=1,2,3 delims=." %%a in ("%LATEST_TAG%") do (
        set /a PATCH=%%c+1
        set VERSION=%%a.%%b.!PATCH!
    )
)

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