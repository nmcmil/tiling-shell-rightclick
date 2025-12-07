#!/bin/bash
#
# Tiling Shell Right-Click - Uninstall Script
#
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}Tiling Shell Right-Click Uninstaller${NC}"
echo "======================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run as root (sudo ./uninstall.sh)${NC}"
    exit 1
fi

INSTALL_DIR="/opt/tiling-rightclick"
SERVICE_NAME="tiling-rightclick.service"

echo -e "${YELLOW}[1/3]${NC} Stopping and disabling service..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl disable "$SERVICE_NAME" 2>/dev/null || true

echo -e "${YELLOW}[2/3]${NC} Removing service file..."
rm -f "/etc/systemd/system/$SERVICE_NAME"
systemctl daemon-reload

echo -e "${YELLOW}[3/3]${NC} Removing installed files..."
rm -rf "$INSTALL_DIR"

echo ""
echo -e "${GREEN}Uninstallation complete!${NC}"
echo ""
echo "The daemon has been removed and will no longer start on boot."
echo "Note: python3-evdev package was not removed (may be used by other software)."
echo ""
