@echo off
title Univote Dev Server
cd /d "C:\ONLINE VOTING NEW\univote"
echo.
echo  ============================================
echo   Univote - Starting Development Server...
echo  ============================================
echo.
echo   Admin Panel : http://localhost:8000/admin-panel/login/
echo   USC Voting  : http://localhost:8000/vote/usc-election-2026/
echo   CCS Voting  : http://localhost:8000/vote/ccs-department-election-2026/
echo.
echo   Press CTRL+C to stop the server.
echo  ============================================
echo.
python manage.py runserver
pause
