#!/bin/bash
echo "Activating virtual environment.."
cd ~/dhaul_spirabot_env/bin

source activate

echo "Locating dhaul_spirabot repository"
cd ~/dhaul_spirabot

echo "Current directory: $(pwd)" 
echo "Locating esptool.py in virtual environment..."
esptool_path=$(which esptool.py)

echo "Checking esptool version..."
# $esptool_path --version >/dev/null 2>&1
esptool_version=$($esptool_path --version 2>&1)
echo "Esptool version: $esptool_version"

if [ $? -ne 0 ]; then
    echo "esptool.py not found! Please ensure it's installed in the virtual environment."
    exit 1
fi
echo "Esptool is installed and recognized in the virtual environment."
echo "Fetching updates from origin/main..."
git fetch origin main

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
BASE=$(git merge-base HEAD origin/main)

if [ $LOCAL = $REMOTE ]; then
    echo "Your branch is up-to-date with origin/main."
else
    echo "There are updates available in origin/main."
    while true; do
        read -p "Do you want to pull the latest changes? (yes/no): " choice
        case $choice in
            [Yy]*)
                git reset --hard HEAD
                git clean -fd
                git pull origin main
                break;;
            [Nn]*)
                echo "Skipping pulling latest changes."
                break;;
            *)
                echo "Please enter 'yes' or 'no'."
                ;;
        esac
    done
fi

read -p "Do you want to upgrade the firmware on the Spirabot? (yes/no): " choice
case $choice in
    [Yy]*)
        echo "USB connections: "
        ls /dev/ttyUSB*
        read -p "Enter the COM port for the Spirabot: " spirabot_port
        echo "Checking for esptool.py..."
        ~/dhaul_spirabot_env/bin/esptool.py --version >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "esptool.py not found! Please install it first."
        fi

        # Use Python to get the home directory
        home_dir=$(python3 -c "import os; print(os.path.expanduser('~'))")
        bootloader_path="$home_dir/dhaul_spirabot/API_tools/firmware/bootloader.bin"
        firmware_path="$home_dir/dhaul_spirabot/API_tools/firmware/firmware.bin"
        partitions_path="$home_dir/dhaul_spirabot/API_tools/firmware/partitions.bin"


        echo "Flashing the Spirabot..."
        ~/dhaul_spirabot_env/bin/esptool.py --chip esp32 --port "$spirabot_port" --baud 115200 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "$bootloader_path" 0x10000 "$firmware_path" 0x8000 "$partitions_path"

        if [ $? -ne 0 ]; then
            echo "Error occurred during flashing."
            exit 1
        fi

        echo "Flashing completed successfully."
        ;;
    [Nn]*)
        echo "Skipping firmware upgrade."
        ;;
    *)
        echo "Invalid choice."
        ;;
esac

read -p "Press enter to start command line tool"

echo "Locating API_tools"
cd API_tools

echo "Starting SpiraAPI_example.py"
python3 SpiraAPI_example.py