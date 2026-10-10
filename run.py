"""
Main entry point for SteamSeparator.
Starts local web server and automatically opens the browser.
"""
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def find_free_port(start_port: int = 8765) -> int:
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
        port += 1
    return start_port


def open_browser_after_delay(url: str, delay: float = 1.2):
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    import uvicorn

    port = find_free_port(8765)
    url = f"http://localhost:{port}"

    print("=" * 60)
    print("  SteamSeparator")
    print(f"  Web UI running at: {url}")
    print("  (Press Ctrl+C in terminal to stop)")
    print("=" * 60)

    # Open browser in a separate thread
    threading.Thread(target=open_browser_after_delay, args=(url,), daemon=True).start()

    # Run uvicorn with reload so changes to code are instantly live
    uvicorn.run("steam_rater.app:app", host="127.0.0.1", port=port, reload=True, log_level="info")


if __name__ == "__main__":
    main()
