@echo off
chcp 65001 >nul
title Koyun Sayaci - Kurulum
cd /d "%~dp0"
echo.
echo  ======================================
echo   KOYUN SAYACI - Windows kurulumu
echo  ======================================
echo.
echo  Bu islem interneti kullanir ve 5-15 dakika surer.
echo  (Python ve yapay zeka kutuphaneleri indirilir.)
echo.

where uv >nul 2>nul
if errorlevel 1 (
  echo  [1/4] Paket yoneticisi (uv) indiriliyor...
  powershell -ExecutionPolicy ByPass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
) else (
  echo  [1/4] uv zaten kurulu.
)

echo  [2/4] Python 3.12 ortami kuruluyor...
uv venv --python 3.12 .venv -q
if errorlevel 1 goto hata

echo  [3/4] Kutuphaneler kuruluyor (torch, ultralytics, flask)...
where nvidia-smi >nul 2>nul
if errorlevel 1 (
  echo        NVIDIA ekran karti bulunamadi: islemci surumu kurulacak.
  uv pip install --python .venv\Scripts\python.exe -q torch torchvision --index-url https://download.pytorch.org/whl/cpu
) else (
  echo        NVIDIA ekran karti bulundu: CUDA surumu kurulacak.
  rem cu128: RTX 50 serisi (Blackwell) dahil; eski kartlarda da calisir
  uv pip install --python .venv\Scripts\python.exe -q torch torchvision --index-url https://download.pytorch.org/whl/cu128
)
if errorlevel 1 goto hata
uv pip install --python .venv\Scripts\python.exe -q ultralytics lap pyyaml requests flask
if errorlevel 1 goto hata

echo  [4/4] Masaustu kisayolu olusturuluyor...
powershell -NoProfile -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Koyun Sayaci.lnk');" ^
  "$s.TargetPath='wscript.exe'; $s.Arguments='\"%~dp0baslat.vbs\"'; $s.WorkingDirectory='%~dp0';" ^
  "$s.IconLocation='%SystemRoot%\System32\shell32.dll,13'; $s.Save()"

set /p OTO="  Bilgisayar acilinca program kendiliginden baslasin mi? (E/H): "
if /i "%OTO%"=="E" (
  powershell -NoProfile -Command ^
    "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Startup')+'\Koyun Sayaci.lnk');" ^
    "$s.TargetPath='wscript.exe'; $s.Arguments='\"%~dp0baslat.vbs\"'; $s.WorkingDirectory='%~dp0'; $s.Save()"
  echo        Baslangica eklendi.
)

echo.
echo  ======================================
echo   KURULUM TAMAM.
echo   Masaustundeki "Koyun Sayaci" kisayoluna cift tiklayin.
echo  ======================================
echo.
pause
exit /b 0

:hata
echo.
echo  !!! Kurulumda hata oldu. Internet baglantisini kontrol edip kur.bat'i tekrar calistirin.
pause
exit /b 1
