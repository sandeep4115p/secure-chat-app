# server.py
import socket
import threading
import struct

HOST = '127.0.0.1'   # listen on all interfaces
PORT = 5000

clients = []  # list of (conn, addr)

lock = threading.Lock()

def recv_all(conn, n):
    data = b''
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def handle_client(conn, addr):
    print(f"[+] New connection from {addr}")
    try:
        while True:
            header = recv_all(conn, 1 + 2 + 4)  # flag(1) + uname_len(2) + payload_len(4)
            if not header:
                break
            flag = header[0]
            uname_len = struct.unpack('!H', header[1:3])[0]
            payload_len = struct.unpack('!I', header[3:7])[0]

            uname_bytes = recv_all(conn, uname_len)
            if uname_bytes is None:
                break
            uname = uname_bytes.decode('utf-8', errors='replace')

            payload = recv_all(conn, payload_len)
            if payload is None:
                break

            # Forward the full packet as-is to all other clients
            packet = header + uname_bytes + payload
            with lock:
                for c, a in clients:
                    if c is not conn:
                        try:
                            c.sendall(packet)
                        except Exception:
                            pass
    except Exception as e:
        print(f"[!] Exception for {addr}: {e}")
    finally:
        with lock:
            for i, (c, a) in enumerate(clients):
                if c is conn:
                    clients.pop(i)
                    break
        conn.close()
        print(f"[-] Connection closed: {addr}")

def accept_loop(server_sock):
    while True:
        conn, addr = server_sock.accept()
        with lock:
            clients.append((conn, addr))
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

def main():
    print(f"Starting server on {HOST}:{PORT}")
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(100)
    accept_loop(server_sock)

if __name__ == '__main__':
    main()
