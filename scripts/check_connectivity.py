import socket
import requests
import json
import os

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def check_ngrok():
    print("🔍 Checking ngrok status...")
    try:
        res = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        if res.status_code == 200:
            data = res.json()
            tunnels = data.get("tunnels", [])
            if tunnels:
                url = tunnels[0].get("public_url")
                print(f"✅ Ngrok is ONLINE: {url}")
                return url
        print("❌ Ngrok is not running or no tunnels active.")
    except:
        print("❌ Ngrok API not reachable (localhost:4040).")
    return None

def check_server():
    print("🔍 Checking FastAPI server status...")
    try:
        res = requests.get("http://localhost:8000/api/me", timeout=2) # Should return 401 but be reachable
        if res.status_code in [200, 401]:
            print("✅ FastAPI Server is REACHABLE on port 8000.")
            return True
        print(f"⚠️ Server returned status code: {res.status_code}")
    except:
        print("❌ FastAPI Server is NOT reachable on port 8000.")
    return False

if __name__ == "__main__":
    print("========================================")
    print("🔮 ASTRO AGENT CONNECTIVITY DIAGNOSTIC")
    print("========================================\n")
    
    local_ip = get_local_ip()
    server_ok = check_server()
    ngrok_url = check_ngrok()
    
    print("\n----------------------------------------")
    if server_ok:
        print(f"📲 LOCAL MOBILE ACCESS: http://{local_ip}:8000")
        if ngrok_url:
            print(f"🌐 PUBLIC MOBILE ACCESS: {ngrok_url}")
        else:
            print("🌐 PUBLIC MOBILE ACCESS: Offline (Ngrok not running)")
        
        print("\n💡 INSTRUCTIONS:")
        print(f"1. Connect your mobile to the same Wi-Fi as this laptop.")
        print(f"2. Open your mobile browser and type the Local IP or Public URL.")
    else:
        print("❌ Please start the server using START_ASTRO_AGENT.bat first.")
    print("----------------------------------------")
