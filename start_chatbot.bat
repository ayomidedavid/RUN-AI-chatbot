@echo off
title Academic Query Chatbot Launcher
color 0A

echo ==================================================
echo      Starting ACADEMIC QUERY AI Chatbot...
echo ==================================================
echo.

echo [1/3] Starting the Python Backend Server...
:: Start the backend in a new command prompt window
start "Chatbot Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001"

echo [2/3] Starting the Frontend Web Server...
:: Start the frontend server in a new command prompt window
cd frontend
start "Chatbot Frontend" cmd /k "python -m http.server 8080"

echo [3/3] Waiting for servers to wake up and load AI models...
:: Wait 5 seconds to give the backend time to start pre-loading
timeout /t 5 /nobreak >nul

echo.
echo Opening the Chatbot in your default web browser...
start http://localhost:8080

echo.
echo ==================================================
echo  DONE! You can close this launcher window now.
echo  Keep the two other black windows open to keep 
echo  the chatbot running.
echo ==================================================
timeout /t 5 >nul
