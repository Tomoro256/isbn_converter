@echo off
setlocal enabledelayedexpansion
title GitHub Release and Push Script

REM �s�v�ȃt�@�C����f�B���N�g�����폜
echo Deleting unnecessary files and directories...
if exist __pycache__ rmdir /s /q __pycache__
if exist venv rmdir /s /q venv
if exist app_data.db del /q app_data.db

REM GitHub���|�W�g����URL
set REPO_URL=https://github.com/Tomoro256/isbn_converter.git

REM �����[�gURL�̊m�F
echo Checking remote URL...
git remote -v

REM �ŐV�̃^�O���擾
for /f "delims=" %%i in ('git describe --tags --abbrev=0 2^>nul') do set LATEST_TAG=%%i

REM �o�[�W�����ԍ��������C���N�������g
if "%LATEST_TAG%"=="" (
    set VERSION=0.1.0
) else (
    for /f "tokens=1,2,3 delims=." %%a in ("%LATEST_TAG%") do (
        set /a PATCH=%%c+1
        set VERSION=%%a.%%b.!PATCH!
    )
)

REM GitHub CLI�ł̃����[�X���b�Z�[�W
set RELEASE_MSG="Release version %VERSION%"

REM Git�̐ݒ�
git add .
git commit --allow-empty -m "Update for version %VERSION%"

REM �����̃^�O���폜���ĐV�����^�O���쐬
git tag -d %VERSION%
git push origin :refs/tags/%VERSION%
git tag %VERSION%

REM �u�����`�̃v�b�V��
echo Pushing to remote repository...
git push origin master

REM �^�O�̃v�b�V��
echo Pushing tags to remote repository...
git push origin --tags

REM GitHub CLI���g�p���ĐV���������[�X���쐬
gh release create %VERSION% --title "Version %VERSION%" --notes %RELEASE_MSG%

echo �����[�X %VERSION% ���쐬����AGitHub�Ƀv�b�V������܂����B
pause