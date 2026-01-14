@echo off
REM Banana Slides Backend Startup Script for Windows

echo ╔══════════════════════════════════════╗
echo ║   🍌 Banana Slides API Server 🍌   ║
echo ╚══════════════════════════════════════╝
echo.

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo ✅ .env file created. Please edit it with your API keys.
    echo.
)

REM Check if pixi is installed
where pixi >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Pixi is not installed.
    echo 📦 Please install Pixi first from: https://pixi.sh
    echo.
    exit /b 1
)

REM Install dependencies using Pixi (run from project root)
echo 📥 Installing dependencies with Pixi...
cd /d "%~dp0.."
pixi install

REM Create instance folder if not exists
if not exist backend\instance mkdir backend\instance
if not exist uploads mkdir uploads

echo.
echo ✅ Setup complete!
echo.
echo 🚀 Starting server...
echo.

REM Run database migrations and start the application
cd backend
pixi run alembic upgrade head && pixi run python app.py
