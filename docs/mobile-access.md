# Mobile access on the same network

GitHub stores source code. Your laptop runs the Python model and retains the local database. This is not GitHub Pages hosting. The gateway adds HTTPS and a shared demonstration password, and forwards requests to the existing loopback server without starting another model worker.

1. Run `start.ps1` on the laptop as usual.
2. Install the optional dependency: `.\.venv\Scripts\python.exe -m pip install -r requirements-mobile.txt`.
3. In a second terminal run `.\start-mobile.ps1`. Use `-Address YOUR_LAN_IP` for Ethernet or a different network adapter.
4. Transfer only `.local/mobile/attend-root.cer` to your own phone using USB or another trusted method. This is the public certificate. Never share `.key` files or commit `.local`.
5. Install this certificate as a trusted CA on the phone. Android certificate settings vary by manufacturer. On iOS install the certificate profile, then enable its trust under Settings > General > About > Certificate Trust Settings. The phone owner must complete trust changes. Remove the certificate when testing ends.
6. Open the HTTPS address printed by the launcher. Use the username/password in `.local/mobile/PHONE-SETUP.txt`. Allow camera access when prompted. Everyone holding this shared password has full prototype administration access.

Both devices must share a network that allows communication. Campus/guest Wi-Fi can isolate clients. If unreachable, use a home router or phone hotspot and rerun the launcher for the laptop's new IP. If Windows Firewall blocks the gateway, allow inbound TCP 8443 only for the appropriate trusted local subnet/profile. Do not configure router port forwarding. Do not bypass certificate warnings: verify the address and install the correct certificate first.

Keep the laptop awake and both terminals running. Stop the gateway with Ctrl+C when finished. Local HTTPS does not add liveness detection or establish recognition accuracy. Camera frames travel from the phone to this laptop for processing.
