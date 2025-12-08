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
git clone https://github.com/nmcmil/tiling-shell-rightclick.git
cd tiling-shell-rightclick
sudo ./install.sh
```

## Uninstallation

```bash
cd tiling-shell-rightclick
sudo ./uninstall.sh
```

## Configuration

After installation, look for the **mouse icon** in your system tray, or search for **"Tiling Rightclick Config"** in your application menu.

The GUI lets you:
- **Select Mouse Device** — Choose which mouse to use (or all devices)
- **Choose Modifier Key** — Super, Ctrl, or Alt (left/right variants)
- **Start/Stop/Restart** the service
- **Show/Hide** the system tray indicator

### Why the Modifier Key Option?

If you've swapped your Super and Ctrl keys (e.g., using GNOME Tweaks for a Mac-like layout), you'll need to change the modifier key to match your setup. The daemon sends raw keycodes, so if your keys are remapped at the system level, you may need to select a different key in the config.

**Example:** If you swapped Super ↔ Ctrl in GNOME Tweaks and Tiling Shell expects Super, try setting the modifier to "Ctrl (Left)" — it will send Ctrl which your system sees as Super.

### Manual Tiling Shell Configuration

Make sure Tiling Shell is configured to use the same activation key:

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

You can control the service from the GUI or via terminal:

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

### Snap not triggering

1. **Check your key mapping** — If you've swapped Super/Ctrl keys in GNOME Tweaks, open the config GUI and try a different modifier key
2. **Verify Tiling Shell settings** — Make sure Tiling Shell's activation key matches what the daemon sends

### Mouse stops working
If the daemon crashes, your mouse may become unresponsive. Reboot to restore normal operation, or use keyboard to run:
```bash
sudo systemctl stop tiling-rightclick.service
```

### Permission denied
The service must run as root to access `/dev/input/` devices.

### System tray indicator not showing
Make sure you have the [AppIndicator extension](https://extensions.gnome.org/extension/615/appindicator-support/) installed and enabled.

## License

MIT License - Feel free to modify and share!

## Credits

- [Tiling Shell](https://github.com/domferr/tilingshell) by Domenico Ferraro
- Inspired by the desire for more intuitive window snapping
