# Tiling Shell Right-Click

Activate [Tiling Shell](https://github.com/domferr/tilingshell)'s snapping view by **right-clicking while dragging a window**, instead of holding a keyboard key.

![Demo](demo.gif)

## How It Works

This daemon runs at the Linux input layer (below Wayland) to:
1. Intercept mouse events when you're dragging a window (left-click held)
2. Convert right-click into a Super key press
3. Tiling Shell sees the Super key and shows snap zones
4. Releasing right-click drops the window into the selected zone

## Requirements

- Ubuntu 22.04+ (or any Linux distro with systemd)
- GNOME Shell with [Tiling Shell extension](https://extensions.gnome.org/extension/7065/tiling-shell/) installed
- Python 3 with `python3-evdev` package

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/tiling-shell-rightclick.git
cd tiling-shell-rightclick
sudo ./install.sh
```

## Uninstallation

```bash
cd tiling-shell-rightclick
sudo ./uninstall.sh
```

## Configuration

By default, the daemon simulates the **Super (Meta)** key. Make sure Tiling Shell is configured to use Super as the activation key:

```bash
gsettings --schemadir ~/.local/share/gnome-shell/extensions/tilingshell@ferrarodomenico.com/schemas \
  set org.gnome.shell.extensions.tilingshell tiling-system-activation-key "['<Super>']"
```

## Usage

1. **Click and hold** on a window title bar to start dragging
2. **Press and hold Right-Click** while dragging
3. Snap zones appear — move to desired zone
4. **Release Right-Click** to snap the window

## Service Management

```bash
# Check status
sudo systemctl status tiling-rightclick.service

# Stop the daemon
sudo systemctl stop tiling-rightclick.service

# Restart the daemon
sudo systemctl restart tiling-rightclick.service

# Disable autostart
sudo systemctl disable tiling-rightclick.service

# View logs
sudo journalctl -u tiling-rightclick.service -f
```

## How It Works (Technical)

The daemon uses Python's `evdev` library to:
1. **Grab** all mouse devices exclusively (so raw events don't reach Wayland)
2. **Proxy** all events through a virtual device (uinput)
3. **Intercept** right-click when left-click is held, converting it to Super key
4. **Release** both keys with proper timing to trigger the snap

This bypasses Wayland's security restrictions because `evdev` operates at the kernel input layer.

## Troubleshooting

### Mouse stops working
If the daemon crashes, your mouse may become unresponsive. Reboot to restore normal operation, or use keyboard to run:
```bash
sudo systemctl stop tiling-rightclick.service
```

### Snap not triggering
Make sure Tiling Shell is set to use Super as the activation key (see Configuration above).

### Permission denied
The service must run as root to access `/dev/input/` devices.

## License

MIT License - Feel free to modify and share!

## Credits

- [Tiling Shell](https://github.com/domferr/tilingshell) by Domenico Ferraro
- Inspired by the desire for more intuitive window snapping
