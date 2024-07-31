# SpiraBot Firmware Flashing Guide

This guide provides instructions on how to use the provided scripts to flash firmware onto the SpiraBot. Two separate scripts, one for Windows and one for Mac, are available to facilitate the firmware flashing process.


- API_tools/
    - firmware/
        - bootloader.bin
        - firmware.bin
        - partitions.bin
        - fw_flash_mac.sh
        - fw_flash_win.bat
        - README.md
    - SpiraAPI.py
    - config.json
    - SpiraAPI_example.py
    - API_test.py
    - requirments.txt
    - hub_main.sh
    - README.md


## Prerequisites

Before proceeding, ensure the following prerequisites are met:

- Python installed (version 3.9 or above recommended)
- Spirabot connected to your Windows machine via a COM port (e.g., COM3)
- Install esptool:
````
pip install esptool
````
## Instructions

### For Windows:

1. Open the provided `flash_windows.bat` script.
2. When prompted, enter the COM port for the Spirabot (e.g., COM3).
3. The script will automatically check for the presence of `esptool.py`. If not found, it will prompt you to install it.
4. Upon successful detection of `esptool.py`, the flashing process will start.
5. Once the flashing completes successfully, the script will display a message indicating successful completion.

### For Mac:

1. Locate the `fw_flash_mac.sh` and run the following command to grant execution permission `chmod +x fw_flash_mac.sh`.
2. Run the script by executing `./fw_flash_mac.sh` in the terminal.
3. Enter the name of the port where the Spirabot is connected.
4. The script will check for `esptool.py`. If not found, it will prompt you to install it.
5. Upon successful detection, the flashing process will start.
6. Once flashing completes successfully, a message indicating successful completion will be displayed.

## Important Notes:
- Ensure the Spirabot is properly connected to the correct port before running the scripts.
- Always confirm the correct port to avoid flashing errors or data loss.

