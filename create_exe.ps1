# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$pythonFile = "clock"

python -m PyInstaller --onefile --windowed -w -i clock.ico "$pythonFile.py"

Copy-Item "dist\$pythonFile.exe" "C:\Users\cothc\Desktop"