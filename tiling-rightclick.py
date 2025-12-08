#!/usr/bin/env python3
"""
Tiling Shell Right-Click Activation Daemon (Proxy Mode)

Intercepts mouse events using exclusive GRAB.
Passes through all events to a virtual mouse, EXCEPT:
- When dragging (Left Click held), Right Click is converted to SUPER key.
- This prevents the OS from seeing the original Right Click (which cancels drags).
"""

import evdev
from evdev import UInput, ecodes as e
import selectors
import sys
import os
import time
import json

CONFIG_PATH = "/etc/tiling-rightclick/config.json"

def load_config():
    """Load configuration from file."""
    config = {
        "device_name": "",  # Empty means all devices
        "modifier_key": "KEY_LEFTMETA"
    }
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                config.update(json.load(f))
    except (PermissionError, json.JSONDecodeError) as e:
        print(f"Could not load config, using defaults: {e}")
    return config

def find_mouse_devices(device_filter=""):
    """Find all mouse devices that support relative movement."""
    devices = []
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            caps = dev.capabilities()
            if e.EV_REL in caps:
                # If filter is set, only include matching device
                if device_filter and device_filter not in dev.name:
                    continue
                devices.append(dev)
        except (PermissionError, OSError):
            pass
    return devices


def main():
    # Load configuration
    config = load_config()
    device_filter = config.get("device_name", "")
    modifier_key_name = config.get("modifier_key", "KEY_LEFTMETA")
    modifier_key = getattr(e, modifier_key_name, e.KEY_LEFTMETA)
    
    print(f"Configuration: device_filter='{device_filter}', modifier_key={modifier_key_name}")
    
    mice = find_mouse_devices(device_filter)
    if not mice:
        print("No mouse devices found!", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(mice)} mouse device(s). Grabbing them...")

    # Combine capabilities of all mice for the virtual output
    # This ensures the virtual mouse can do everything the real ones can
    combined_caps = {
        e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE, e.BTN_SIDE, e.BTN_EXTRA],
        e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
        e.EV_MSC: [e.MSC_SCAN],
    }
    
    # Add the configured modifier key to capabilities
    combined_caps[e.EV_KEY].append(modifier_key)

    # Create Virtual Mouse+Keyboard COMBO device
    try:
        vkbdmouse = UInput(combined_caps, name="Tiling Shell Proxy Device", version=0x3)
    except Exception as err:
        print(f"Failed to create virtual device: {err}", file=sys.stderr)
        sys.exit(1)

    # State
    left_held = False
    right_held = False
    super_sent = False
    
    # Selector for reading multiple devices
    sel = selectors.DefaultSelector()

    # Grab devices
    # WARNING: If this script crashes, the mouse might be unresponsive until reboot or ungrab
    grabbed_devices = []
    for mouse in mice:
        try:
            mouse.grab()
            grabbed_devices.append(mouse)
            sel.register(mouse, selectors.EVENT_READ)
            print(f"Grabbed {mouse.name}")
        except Exception as err:
            print(f"Could not grab {mouse.name}: {err}", file=sys.stderr)

    if not grabbed_devices:
        print("Could not grab any devices. Exiting.", file=sys.stderr)
        sys.exit(1)

    print("Proxy running. Press Ctrl+C to stop (and ungrab).")

    try:
        while True:
            for key, mask in sel.select():
                device = key.fileobj
                try:
                    for event in device.read():
                        
                        # Handle Keys (Buttons)
                        if event.type == e.EV_KEY:
                            if event.code == e.BTN_LEFT:
                                left_held = (event.value == 1)
                                vkbdmouse.write_event(event) # Passthrough Left Click
                                
                            elif event.code == e.BTN_RIGHT:
                                right_held = (event.value == 1)
                                
                                # Logic: If Left is held, treat Right as Super
                                if left_held:
                                    if right_held:
                                        if not super_sent:
                                            # Send Super Down instead of Right Down
                                            vkbdmouse.write(e.EV_KEY, modifier_key, 1)
                                            super_sent = True
                                            print("Proxy: Swapped Right->Super (Active)")
                                    else: # Right released
                                        if super_sent:
                                            # User released Right Click while in "Snap Mode"
                                            # We must Drop the window (Left Up) WHILE Super is still held.
                                            
                                            # 1. Force release Left Click (Drop window into zone)
                                            vkbdmouse.write(e.EV_KEY, e.BTN_LEFT, 0)
                                            vkbdmouse.syn()
                                            
                                            # 2. Give Tiling Shell time to process the drop
                                            time.sleep(0.05)  # 50ms delay
                                            
                                            # 3. Release SUPER (Deactivate tiling mode)
                                            vkbdmouse.write(e.EV_KEY, modifier_key, 0)
                                            vkbdmouse.syn()
                                            
                                            super_sent = False
                                            left_held = False # We forced it up
                                            
                                            print("Proxy: Dropped Window & Released Super (Snap Committed)")
                                        else:
                                            # If we never sent super (maybe left wasn't held when right started?), pass through
                                            vkbdmouse.write_event(event)
                                else:
                                    # Left not held, normal Right Click behavior
                                    # BUT if we were sending super, we should probably stop? 
                                    # e.g. User releases left before right.
                                    if super_sent and not right_held: # Released right while super was active
                                         vkbdmouse.write(e.EV_KEY, modifier_key, 0)
                                         super_sent = False
                                    elif not super_sent:
                                         vkbdmouse.write_event(event) # Normal pass through
                                    
                            else:
                                # Other buttons passed through
                                vkbdmouse.write_event(event)
                                
                            vkbdmouse.syn()

                        # Pass through Movement and everything else
                        else:
                            vkbdmouse.write_event(event)
                            vkbdmouse.syn()
                            
                except OSError:
                    # Device lost
                    sel.unregister(device)
                    try:
                        device.ungrab()
                    except:
                        pass
                    device.close()

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Ungrab everything to restore mouse
        for dev in grabbed_devices:
            try:
                dev.ungrab()
            except:
                pass
        vkbdmouse.close()

if __name__ == "__main__":
    main()
