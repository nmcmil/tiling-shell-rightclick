#!/usr/bin/env python3
"""
Tiling Rightclick System Tray Indicator

Lives in the Ubuntu/GNOME top bar and provides quick access to:
- Service status
- Start/Stop toggle
- Open configuration GUI
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GLib
import subprocess
import os
import signal
import json

SERVICE_NAME = "tiling-rightclick.service"
CONFIG_GUI_PATH = "/opt/tiling-rightclick/tiling-rightclick-config.py"
CONFIG_PATH = "/etc/tiling-rightclick/config.json"

def should_show_indicator():
    """Check config to see if indicator should be shown."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                return config.get("show_indicator", True)
    except (PermissionError, json.JSONDecodeError):
        pass
    return True  # Default to showing

class TilingRightclickIndicator:
    def __init__(self):
        # Create the indicator
        self.indicator = AppIndicator3.Indicator.new(
            "tiling-rightclick-indicator",
            "input-mouse",  # Icon name from system theme
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title("Tiling Rightclick")
        
        # Build menu
        self.menu = Gtk.Menu()
        
        # Status item (non-clickable header)
        self.status_item = Gtk.MenuItem(label="Status: Checking...")
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)
        
        self.menu.append(Gtk.SeparatorMenuItem())
        
        # Toggle service item
        self.toggle_item = Gtk.MenuItem(label="Start Service")
        self.toggle_item.connect("activate", self.on_toggle_service)
        self.menu.append(self.toggle_item)
        
        # Open config item
        config_item = Gtk.MenuItem(label="Open Configuration...")
        config_item.connect("activate", self.on_open_config)
        self.menu.append(config_item)
        
        self.menu.show_all()
        self.indicator.set_menu(self.menu)
        
        # Update status periodically
        self.update_status()
        GLib.timeout_add_seconds(5, self.update_status)
    
    def get_service_status(self):
        """Check if the service is running."""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', SERVICE_NAME],
                capture_output=True, text=True
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False
    
    def update_status(self):
        """Update the status display."""
        is_active = self.get_service_status()
        
        if is_active:
            self.status_item.set_label("● Service Running")
            self.toggle_item.set_label("Stop Service")
            self.indicator.set_icon("input-mouse")
        else:
            self.status_item.set_label("○ Service Stopped")
            self.toggle_item.set_label("Start Service")
            self.indicator.set_icon("input-mouse-symbolic")
        
        return True  # Continue timer
    
    def on_toggle_service(self, widget):
        """Toggle the service on/off."""
        is_active = self.get_service_status()
        action = "stop" if is_active else "start"
        
        try:
            subprocess.run(
                ['pkexec', 'systemctl', action, SERVICE_NAME],
                check=True
            )
            # Update status after action
            GLib.timeout_add(500, self.update_status)
        except subprocess.CalledProcessError:
            pass
    
    def on_open_config(self, widget):
        """Open the configuration GUI."""
        try:
            subprocess.Popen(['python3', CONFIG_GUI_PATH])
        except Exception as e:
            print(f"Failed to open config: {e}")
    
    def on_quit(self, widget):
        """Quit the indicator."""
        Gtk.main_quit()


def main():
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Check if indicator should be shown
    if not should_show_indicator():
        return  # Exit silently
    
    indicator = TilingRightclickIndicator()
    Gtk.main()


if __name__ == "__main__":
    main()
