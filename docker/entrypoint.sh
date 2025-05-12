#!/bin/bash
set -e

# Ensure this script is executable
chmod +x /usr/local/bin/setup_canable 2>/dev/null || true

# Reload udev rules to ensure our CANable rules are active
# (Commented out: udev is not running in container, host udev is used)
# echo "Reloading udev rules..."
# udevadm control --reload-rules
# udevadm trigger

# Set permissions on USB devices
echo "Setting permissions on USB devices..."
chmod 666 /dev/ttyACM* 2>/dev/null || true
chmod 666 /dev/ttyUSB* 2>/dev/null || true

# Setup CANable device
echo "Setting up CANable device..."
if [ -e /dev/ttyACM0 ] || [ -e /dev/ttyUSB0 ]; then
    # Wait for device to be ready
    sleep 1
    
    # Run the setup script
    if command -v setup_canable &> /dev/null; then
        echo "Running CANable setup..."
        setup_canable
    else
        echo "CANable setup script not found, using manual setup..."
        # Fallback manual setup
        if [ -e /dev/ttyACM0 ]; then
            slcand -o -c -s3 /dev/ttyACM0 can0
            ip link set can0 up type can bitrate 500000
        fi
    fi
    
    # Verify CAN interface
    echo "CAN interfaces:"
    ip -details link show can0 || true
else
    echo "No CANable device found. Make sure it's connected and permissions are set."
fi

# Execute the command passed to the container
echo "Starting application..."
exec "$@"
