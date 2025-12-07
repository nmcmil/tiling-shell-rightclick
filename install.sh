#!/bin/bash
#
# Tiling Shell Right-Click - Install Script
#
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Tiling Shell Right-Click Installer${NC}"
echo "===================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run as root (sudo ./install.sh)${NC}"
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/tiling-rightclick"
SERVICE_NAME="tiling-rightclick.service"

echo -e "${YELLOW}[1/5]${NC} Installing dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3 python3-evdev
elif command -v dnf &> /dev/null; then
    dnf install -y -q python3 python3-evdev
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm python python-evdev
else
    echo -e "${YELLOW}Warning: Could not detect package manager. Please install python3-evdev manually.${NC}"
fi

echo -e "${YELLOW}[2/5]${NC} Creating install directory..."
mkdir -p "$INSTALL_DIR"

echo -e "${YELLOW}[3/5]${NC} Copying files..."
cp "$SCRIPT_DIR/tiling-rightclick.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/tiling-rightclick.py"

echo -e "${YELLOW}[4/5]${NC} Installing systemd service..."
cat > "/etc/systemd/system/$SERVICE_NAME" << EOF
[Unit]
Description=Tiling Shell Right-Click Activation Daemon
After=graphical.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/tiling-rightclick.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
EOF

echo -e "${YELLOW}[5/5]${NC} Enabling and starting service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "The daemon is now running and will start automatically on boot."
echo ""
echo "Usage:"
echo "  1. Drag a window (hold left-click)"
echo "  2. Press right-click while dragging"
echo "  3. Snap zones appear!"
echo "  4. Release right-click to snap"
echo ""
echo "Commands:"
echo "  sudo systemctl status $SERVICE_NAME   # Check status"
echo "  sudo systemctl stop $SERVICE_NAME     # Stop daemon"
echo "  sudo systemctl restart $SERVICE_NAME  # Restart daemon"
echo ""
