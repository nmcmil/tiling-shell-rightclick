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
CONFIG_DIR="/etc/tiling-rightclick"
SERVICE_NAME="tiling-rightclick.service"

echo -e "${YELLOW}[1/7]${NC} Installing dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3 python3-evdev python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-appindicator3-0.1
elif command -v dnf &> /dev/null; then
    dnf install -y -q python3 python3-evdev python3-gobject gtk4 libadwaita libappindicator-gtk3
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm python python-evdev python-gobject gtk4 libadwaita libappindicator-gtk3
else
    echo -e "${YELLOW}Warning: Could not detect package manager. Please install dependencies manually.${NC}"
fi

echo -e "${YELLOW}[2/7]${NC} Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"

echo -e "${YELLOW}[3/7]${NC} Copying daemon..."
cp "$SCRIPT_DIR/tiling-rightclick.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/tiling-rightclick.py"

echo -e "${YELLOW}[4/7]${NC} Copying configuration GUI..."
cp "$SCRIPT_DIR/tiling-rightclick-config.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/tiling-rightclick-config.py"

echo -e "${YELLOW}[5/7]${NC} Installing desktop entry..."
cp "$SCRIPT_DIR/tiling-rightclick-config.desktop" "/usr/share/applications/"

echo -e "${YELLOW}[6/7]${NC} Creating default configuration..."
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cat > "$CONFIG_DIR/config.json" << 'CONFIGEOF'
{
  "device_name": "",
  "modifier_key": "KEY_LEFTMETA",
  "show_indicator": true
}
CONFIGEOF
fi

echo -e "${YELLOW}[7/9]${NC} Copying system tray indicator..."
cp "$SCRIPT_DIR/tiling-rightclick-indicator.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/tiling-rightclick-indicator.py"

echo -e "${YELLOW}[8/9]${NC} Installing autostart entry..."
mkdir -p /etc/xdg/autostart
cp "$SCRIPT_DIR/tiling-rightclick-indicator.desktop" "/etc/xdg/autostart/"

echo -e "${YELLOW}[9/9]${NC} Installing and starting systemd service..."
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
echo "Configuration:"
echo "  Look for the mouse icon in your top bar for quick Start/Stop"
echo "  Or search for 'Tiling Rightclick Config' in your app menu"
echo ""
echo "Commands:"
echo "  sudo systemctl status $SERVICE_NAME   # Check status"
echo "  sudo systemctl stop $SERVICE_NAME     # Stop daemon"
echo "  sudo systemctl restart $SERVICE_NAME  # Restart daemon"
echo ""

