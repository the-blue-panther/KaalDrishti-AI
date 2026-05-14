# 🚀 Astro Agent: Quick Start & Shutdown Guide

This guide provides step-by-step instructions on how to launch your **Astro Agent** application from scratch after restarting your Windows computer, and how to safely shut it down when you are finished.

---

## 🟢 Part 1: How to Start the Application

### 1. Open PowerShell
Press the `Windows Key`, type **PowerShell**, and press `Enter` to open your terminal window.

### 2. Navigate to the Project Folder
Type the following command to move into your Astro Agent project directory:
```powershell
cd "d:\Downloads\Projects\Astro Agent"
```

### 3. Activate the Virtual Environment
Activate your isolated Python environment to ensure all dependencies (like PySwissEph, FastAPI, and Neo4j) load correctly:
```powershell
.\venv\Scripts\Activate
```
*(You should see `(venv)` appear on the left side of your text prompt).*

### 4. Set the System Variables
To allow Python to find all your local engine files, set your PYTHONPATH:
```powershell
$env:PYTHONPATH="d:\Downloads\Projects\Astro Agent"
```
*Note: Make sure your `GEMINI_API_KEY` is either set as an environment variable or located in your system bindings so the LLM inference engine can operate!*

### 5. Boot the FastAPI Server
Launch the master backend routing architecture using Python:
```powershell
python main.py
```
*(Alternative manual boot command: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`)*

If successful, you will see a message saying: **`Application startup complete.`**

### 6. Open the Dashboard
Open your web browser (Chrome, Edge, Firefox, etc.) and go to the following address:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📱 Part 1.5: Mobile & Remote Access

To access the Astro Agent from your phone or another device:

### Option A: Local Network (Fastest)
1. Ensure your phone and laptop are on the same Wi-Fi.
2. Open your phone's browser and go to your laptop's local IP:
   👉 **`http://192.168.0.109:8000`**

### Option B: Remote Access (ngrok)
1. When you run `START_ASTRO_AGENT.bat`, it starts an **ngrok** tunnel.
2. Check the **FastAPI Server** console output; it will display a public `https://...` link.
3. You can open this link from anywhere in the world.

---

## 🔴 Part 2: How to Cleanly Shut Down the Application

Whenever you are done using the Astro Agent and want to free up your computer's memory, follow these steps to securely shut down the server:

### 1. Stop the Server Process
Go back to the **PowerShell** window where the server is currently running.
Press **`Ctrl + C`** on your keyboard. 
*(This sends a native interrupt signal to Uvicorn, safely unbinding the local port and closing the server).*

### 2. Deactivate the Virtual Environment (Optional)
If you want to cleanly exit the isolated Python environment, just type:
```powershell
deactivate
```

### 3. Close the Terminal
You can now safely type `exit` to close PowerShell, or just click the `X` in the top right corner.

---

*✨ The Astro Agent engine matrix is now safely resting until your next session.*
