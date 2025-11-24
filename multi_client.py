import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Jumlah session yang mau dijalankan (1-10 recommended)
MAX_SESSIONS = 10

async def start_session(session_num: int):
    suffix = "" if session_num == 1 else str(session_num)
    
    api_id = os.getenv(f"API_ID{suffix}")
    api_hash = os.getenv(f"API_HASH{suffix}")
    session_string = os.getenv(f"SESSION{suffix}")  # atau SESSION1, SESSION2, dst
    
    if not all([api_id, api_hash, session_string]):
        print(f"[SESSION {session_num}] Missing env vars, skipped.")
        return
    
    print(f"[SESSION {session_num}] Starting...")
    
    # Cara paling stabil untuk Ultroid terbaru
    cmd = [
        sys.executable, "-m", "pyUltroid",
        "--id", api_id,
        "--hash", api_hash,
        "-s", session_string
    ]
    
    # Kalau Ultroid kamu hanya nerima session string saja (cukup 1 env SESSION1, SESSION2, dst)
    # gunakan cara ini aja:
    # cmd = [sys.executable, "-m", "pyUltroid", session_string]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    
    # Optional: pantau prosesnya
    while True:
        if process.poll() is not None:
            print(f"[SESSION {session_num}] Stopped with code {process.returncode}")
            break
        await asyncio.sleep(5)

async def main():
    tasks = []
    for i in range(1, MAX_SESSIONS + 1):
        tasks.append(start_session(i))
        await asyncio.sleep(8)  # delay antar session biar nggak flood login
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user")
