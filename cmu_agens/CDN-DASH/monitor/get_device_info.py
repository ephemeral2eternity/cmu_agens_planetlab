## Do Traceroute to a CDN host and gets detailed info on each hop.
# get_device_info.py
# Chen Wang, Oct. 23, 2015
# chenw@cmu.edu
import random

def get_device_info():
    device_info = {}
    device_types = ["Tablet", "Phone", "Laptop", "Desktop", "TV"]
    player_versions = ["v1.0", "v1.2", "v1.5", "v2.0"]
    device_info["device"] = random.choice(device_types)

    if (device_info["device"] == "Tablet") or (device_info["device"] == "Phone"):
        device_info["os"] = random.choice(["Google Android", "Apple iOS", "Microsoft Windows 8", "Amazon Fire OS"])
        device_info["browser"] = "app"
    elif (device_info["device"] == "Laptop") or (device_info["device"] == "Desktop"):
        device_info["os"] = random.choice(["Mac OS X", "Microsoft Windows 10", "Linux"])
        device_info["browser"] = random.choice(["Chrome", "Firefox", "IE"])
    else:
        device_info["os"] = random.choice(["Android TV", "Firefox OS", "Google TV", "Fire TV", "Apple TV OS"])
        device_info["browser"] = random.choice(["Chrome", "Firefox", "IE", "app"])

    device_info["player"] = random.choice(player_versions)

    return device_info