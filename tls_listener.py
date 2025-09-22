#!/usr/bin/env python3
import socket, ssl, threading, os

HOST = '127.0.0.1'
PORT = 444
CERTFILE = 'cert.pem'
KEYFILE = 'key.pem'

def read_from_agent(connstream):
    try:
        while True:
            data = connstream.recv(4096)
            if not data:
                break
            print(data.decode(errors='ignore'), end="")
    except Exception as e:
        print(f"[-] Agent disconnected: {e}")

def main():
    if not os.path.exists(CERTFILE) or not os.path.exists(KEYFILE):
        print("[!] Generate cert first: openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes")
        return

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        sock.bind((HOST, PORT))
        sock.listen(5)
        print(f"[+] Listening on {HOST}:{PORT} (TLS)")

        conn, addr = sock.accept()
        connstream = context.wrap_socket(conn, server_side=True)
        print(f"[+] Connection from {addr}")

        threading.Thread(target=read_from_agent, args=(connstream,), daemon=True).start()

        try:
            while True:
                cmd = input("$ ")
                if cmd.strip() == "":
                    continue
                connstream.write((cmd + '\n').encode())
        except KeyboardInterrupt:
            print("\n[!] Shutting down listener")
        finally:
            connstream.shutdown(socket.SHUT_RDWR)
            connstream.close()

if __name__ == "__main__":
    main()
