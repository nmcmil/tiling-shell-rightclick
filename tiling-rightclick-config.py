#!/usr/bin/env python3
"""
Tiling Rightclick Configuration GUI

A GTK4/libadwaita application for configuring the tiling-rightclick daemon.
Allows users to select which mouse device to grab and which modifier key to send.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import json
import os
import subprocess
import sys

# Try to import evdev for device listing
try:
    import evdev
    from evdev import ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False

CONFIG_PATH = "/etc/tiling-rightclick/config.json"
SERVICE_NAME = "tiling-rightclick.service"

# Modifier key options
MODIFIER_KEYS = {
    "Super (Left)": "KEY_LEFTMETA",
    "Super (Right)": "KEY_RIGHTMETA",
    "Ctrl (Left)": "KEY_LEFTCTRL",
    "Ctrl (Right)": "KEY_RIGHTCTRL",
    "Alt (Left)": "KEY_LEFTALT",
    "Alt (Right)": "KEY_RIGHTALT",
}

class TilingRightclickConfig(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.tiling-rightclick-config",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.config = {
            "device_name": "",  # Empty means all devices
            "modifier_key": "KEY_LEFTMETA",
            "show_indicator": True
        }
        self.load_config()
        
    def load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    self.config.update(json.load(f))
        except (PermissionError, json.JSONDecodeError) as e:
            print(f"Could not load config: {e}")
    
    def save_config(self):
        """Save configuration to file (requires sudo)."""
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except PermissionError:
            # Try with pkexec
            try:
                config_json = json.dumps(self.config, indent=2)
                subprocess.run([
                    'pkexec', 'bash', '-c',
                    f'mkdir -p /etc/tiling-rightclick && echo \'{config_json}\' > {CONFIG_PATH}'
                ], check=True)
                return True
            except subprocess.CalledProcessError:
                return False
    
    def get_mouse_devices(self):
        """Get list of available mouse devices."""
        devices = [("(All Devices)", "")]
        if not EVDEV_AVAILABLE:
            return devices
        
        try:
            for path in evdev.list_devices():
                try:
                    dev = evdev.InputDevice(path)
                    caps = dev.capabilities()
                    # Check for relative movement (mouse)
                    if evdev.ecodes.EV_REL in caps:
                        # Skip virtual/proxy devices
                        if "Tiling Shell Proxy" not in dev.name:
                            devices.append((dev.name, dev.name))
                except (PermissionError, OSError):
                    pass
        except Exception as e:
            print(f"Error listing devices: {e}")
        
        return devices
    
    def get_service_status(self):
        """Get the current service status."""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', SERVICE_NAME],
                capture_output=True, text=True
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False
    
    def control_service(self, action):
        """Start, stop, or restart the service."""
        try:
            subprocess.run(
                ['pkexec', 'systemctl', action, SERVICE_NAME],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def do_activate(self):
        """Create and show the main window."""
        win = Adw.ApplicationWindow(application=self)
        win.set_title("Tiling Rightclick Configuration")
        win.set_default_size(450, 500)
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        win.set_content(main_box)
        
        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Content with clamp for proper sizing
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        clamp.set_margin_top(20)
        clamp.set_margin_bottom(20)
        clamp.set_margin_start(20)
        clamp.set_margin_end(20)
        main_box.append(clamp)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        clamp.set_child(content_box)
        
        # === Device Selection Group ===
        device_group = Adw.PreferencesGroup()
        device_group.set_title("Mouse Device")
        device_group.set_description("Select which mouse device to use for right-click tiling")
        content_box.append(device_group)
        
        # Device dropdown row
        device_row = Adw.ComboRow()
        device_row.set_title("Device")
        
        # Populate device list
        devices = self.get_mouse_devices()
        device_model = Gtk.StringList()
        selected_idx = 0
        for i, (name, value) in enumerate(devices):
            device_model.append(name)
            if value == self.config.get("device_name", ""):
                selected_idx = i
        
        device_row.set_model(device_model)
        device_row.set_selected(selected_idx)
        device_row.connect("notify::selected", self.on_device_changed, devices)
        device_group.add(device_row)
        self.device_row = device_row
        self.devices = devices
        
        # Refresh button
        refresh_row = Adw.ActionRow()
        refresh_row.set_title("Refresh Devices")
        refresh_row.set_subtitle("Rescan for connected mouse devices")
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.set_valign(Gtk.Align.CENTER)
        refresh_btn.connect("clicked", self.on_refresh_clicked)
        refresh_row.add_suffix(refresh_btn)
        device_group.add(refresh_row)
        
        # === Modifier Key Group ===
        key_group = Adw.PreferencesGroup()
        key_group.set_title("Modifier Key")
        key_group.set_description("Key to send when right-clicking while dragging")
        content_box.append(key_group)
        
        # Modifier key dropdown
        key_row = Adw.ComboRow()
        key_row.set_title("Key")
        
        key_model = Gtk.StringList()
        key_names = list(MODIFIER_KEYS.keys())
        selected_key_idx = 0
        current_key = self.config.get("modifier_key", "KEY_LEFTMETA")
        for i, name in enumerate(key_names):
            key_model.append(name)
            if MODIFIER_KEYS[name] == current_key:
                selected_key_idx = i
        
        key_row.set_model(key_model)
        key_row.set_selected(selected_key_idx)
        key_row.connect("notify::selected", self.on_key_changed, key_names)
        key_group.add(key_row)
        self.key_row = key_row
        self.key_names = key_names
        
        # Restart notice (hidden by default)
        self.restart_notice = Adw.ActionRow()
        self.restart_notice.set_title("⚠️ Restart Required")
        self.restart_notice.set_subtitle("Click Restart below to apply the new modifier key")
        self.restart_notice.set_visible(False)
        key_group.add(self.restart_notice)
        
        # === Service Control Group ===
        service_group = Adw.PreferencesGroup()
        service_group.set_title("Service Control")
        content_box.append(service_group)
        
        # Status row
        self.status_row = Adw.ActionRow()
        self.status_row.set_title("Service Status")
        self.update_status_display()
        service_group.add(self.status_row)
        
        # Control buttons row
        control_row = Adw.ActionRow()
        control_row.set_title("Controls")
        
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        control_box.set_valign(Gtk.Align.CENTER)
        
        start_btn = Gtk.Button(label="Start")
        start_btn.connect("clicked", lambda b: self.on_service_action("start"))
        control_box.append(start_btn)
        
        stop_btn = Gtk.Button(label="Stop")
        stop_btn.connect("clicked", lambda b: self.on_service_action("stop"))
        control_box.append(stop_btn)
        
        restart_btn = Gtk.Button(label="Restart")
        restart_btn.connect("clicked", lambda b: self.on_service_action("restart"))
        control_box.append(restart_btn)
        
        control_row.add_suffix(control_box)
        service_group.add(control_row)
        
        # === Indicator Settings Group ===
        indicator_group = Adw.PreferencesGroup()
        indicator_group.set_title("System Tray Indicator")
        indicator_group.set_description("Control the indicator icon in the top bar")
        content_box.append(indicator_group)
        
        # Indicator toggle
        indicator_row = Adw.SwitchRow()
        indicator_row.set_title("Show Indicator")
        indicator_row.set_subtitle("Display status icon in system tray")
        indicator_row.set_active(self.config.get("show_indicator", True))
        indicator_row.connect("notify::active", self.on_indicator_toggled)
        indicator_group.add(indicator_row)
        self.indicator_row = indicator_row
        
        win.present()
    
    def on_device_changed(self, row, param, devices):
        """Handle device selection change."""
        idx = row.get_selected()
        if idx < len(devices):
            self.config["device_name"] = devices[idx][1]
    
    def on_key_changed(self, row, param, key_names):
        """Handle modifier key selection change."""
        idx = row.get_selected()
        if idx < len(key_names):
            new_key = MODIFIER_KEYS[key_names[idx]]
            if new_key != self.config.get("modifier_key"):
                self.config["modifier_key"] = new_key
                self.restart_notice.set_visible(True)
                # Auto-save when modifier changes
                self.save_config()
    
    def on_refresh_clicked(self, button):
        """Refresh the device list."""
        self.devices = self.get_mouse_devices()
        device_model = Gtk.StringList()
        for name, _ in self.devices:
            device_model.append(name)
        self.device_row.set_model(device_model)
        self.device_row.set_selected(0)
    
    def on_indicator_toggled(self, row, param):
        """Handle indicator toggle change."""
        if not row.get_active():
            # Show warning dialog before disabling
            self.show_indicator_warning(row)
        else:
            self.config["show_indicator"] = True
            self.save_config()
            # Try to launch the indicator
            self.launch_indicator()
    
    def launch_indicator(self):
        """Launch the indicator process."""
        indicator_path = "/opt/tiling-rightclick/tiling-rightclick-indicator.py"
        # Fall back to dev path
        import os.path
        if not os.path.exists(indicator_path):
            indicator_path = os.path.expanduser("~/tiling-shell-rightclick/tiling-rightclick-indicator.py")
        try:
            subprocess.Popen(['python3', indicator_path], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        except Exception as e:
            self.show_message("Error", f"Failed to launch indicator: {e}")
    
    def kill_indicator(self):
        """Kill running indicator processes."""
        try:
            subprocess.run(['pkill', '-f', 'tiling-rightclick-indicator'], check=False)
        except Exception:
            pass
    
    def show_indicator_warning(self, row):
        """Show warning when disabling indicator."""
        dialog = Adw.MessageDialog(
            transient_for=self.get_active_window(),
            heading="Disable System Tray Indicator?",
            body="Without the indicator, you'll need to use terminal commands to control the service:\n\nsudo systemctl start/stop tiling-rightclick.service\n\nOr re-open this app from the application menu."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("disable", "Disable")
        dialog.set_response_appearance("disable", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_indicator_warning_response, row)
        dialog.present()
    
    def on_indicator_warning_response(self, dialog, response, row):
        """Handle indicator warning dialog response."""
        if response == "disable":
            self.config["show_indicator"] = False
            self.save_config()
            self.kill_indicator()
            self.show_message("Indicator Disabled", "The indicator has been closed and will not appear on next login.")
        else:
            # User cancelled - restore toggle to ON
            row.set_active(True)
    
    def on_service_action(self, action):
        """Handle service control button click."""
        if self.control_service(action):
            GLib.timeout_add(500, self.update_status_display)
            if action == "restart":
                self.restart_notice.set_visible(False)
        else:
            self.show_message("Error", f"Failed to {action} service")
    
    def update_status_display(self):
        """Update the service status display."""
        is_active = self.get_service_status()
        status_text = "Running" if is_active else "Stopped"
        
        # Update existing label if we have one, otherwise create it
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.set_label(status_text)
            # Update CSS classes
            if is_active:
                self.status_label.remove_css_class("error")
                self.status_label.add_css_class("success")
            else:
                self.status_label.remove_css_class("success")
                self.status_label.add_css_class("error")
        else:
            # Create new label
            self.status_label = Gtk.Label(label=status_text)
            self.status_label.add_css_class("success" if is_active else "error")
            self.status_row.add_suffix(self.status_label)
        
        return False
    

    
    def show_message(self, title, message):
        """Show a message dialog."""
        dialog = Adw.MessageDialog(
            transient_for=self.get_active_window(),
            heading=title,
            body=message
        )
        dialog.add_response("ok", "OK")
        dialog.present()


def main():
    app = TilingRightclickConfig()
    return app.run(sys.argv)


if __name__ == "__main__":
    main()
