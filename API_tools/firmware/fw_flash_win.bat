@echo off
SET /P esp_port="Enter the COM port for the ESP32 (e.g., COM3): "

echo Checking for esptool.py...
python -m esptool --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo esptool.py not found! Please install it first.
    exit /b
)

echo Flashing the ESP32...
python -m esptool --chip esp32 --port %esp_port% --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 bootloader.bin 0x10000 firmware.bin 0x8000 partitions.bin

IF %ERRORLEVEL% NEQ 0 (
    echo Error occurred during flashing.
    exit /b
)

echo Flashing completed successfully!
pause
