#!/bin/bash

echo "USB connections: "
ls /dev/cu.*
read -p "Enter the COM port for the Spirabot: " spirabot_port
echo "Checking for esptool.py..."
python3 -m esptool --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "esptool.py not found! Please install it first."
fi

echo "Flashing the ESP32..."
python3 -m esptool --chip esp32 --port "$spirabot_port" --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 bootloader.bin 0x10000 firmware.bin 0x8000 partitions.bin

if [ $? -ne 0 ]; then
    echo "Error occurred during flashing."
    exit 1
fi

echo "Flashing completed successfully!"
