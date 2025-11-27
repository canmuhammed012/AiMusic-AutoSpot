@echo off
setlocal
echo ========================================
echo Ai Music AutoSpot - Setup Olusturma
echo ========================================
echo.

REM PyInstaller ile uygulamayi derle
echo [1/2] PyInstaller ile uygulama derleniyor...
echo.

pyinstaller --clean --noconfirm AiMusicAutoSpot_New.spec

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo HATA: PyInstaller derlemesi basarisiz oldu!
    echo Lutfen yukaridaki hataya bakin.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] PyInstaller derlemesi basariyla tamamlandi.
echo.

REM Inno Setup'i calistir
echo [2/2] Inno Setup ile kurulum dosyasi olusturuluyor...
echo.

REM Inno Setup yolunu kontrol et
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_PATH% (
    set INNO_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist %INNO_PATH% (
    echo.
    echo UYARI: Inno Setup bulunamadi!
    echo Lutfen Inno Setup 6'yi kurun veya yolunu manuel olarak belirtin.
    echo.
    echo PyInstaller ciktisi hazir: %cd%\dist\AiMusicAutoSpot
    echo.
    pause
    exit /b 1
)

%INNO_PATH% "Kurulum\setup.iss"

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo HATA: Inno Setup derlemesi basarisiz oldu!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================
echo BASARILI!
echo ========================================
echo.
echo Kurulum dosyasi olusturuldu: %cd%\Setup
echo.
pause

