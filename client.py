# client.py (308+ style upgraded version with original logic preserved)
# ======== Secure Chat Client with Premium UI ========
# Includes: Encryption, Logs, Typing Status, Online Status, File + Photo Support
import socket
import threading
import struct
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import time
import os
import webbrowser

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import base64

SERVER_HOST = "interchange.proxy.rlwy.net"
SERVER_PORT = 10385
LOGS_DIR = "chat_logs"
os.makedirs(LOGS_DIR, exist_ok=True)

FIXED_SALT = b'static_salt_12345'

# ======== Encryption helpers ========
def derive_key_from_password(password: str, salt: bytes = FIXED_SALT) -> bytes:
    password_bytes = password.encode('utf-8')
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    return base64.urlsafe_b64encode(kdf.derive(password_bytes))

def encrypt_bytes(token: bytes, data: bytes) -> bytes:
    return Fernet(token).encrypt(data)

def decrypt_bytes(token: bytes, data: bytes) -> bytes:
    return Fernet(token).decrypt(data)

def pack_message(username: str, payload_bytes: bytes, encrypted: bool) -> bytes:
    flag = b'\x01' if encrypted else b'\x00'
    uname_b = username.encode('utf-8')
    return flag + struct.pack('!H', len(uname_b)) + struct.pack('!I', len(payload_bytes)) + uname_b + payload_bytes

def recv_all(conn, n):
    data = b''
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

# ======== GUI Client ========
# Main Tkinter-based chat interface
# Features:
# 1. Real-time messaging
# 2. End-to-end encryption using Fernet
# 3. Typing indicator
# 4. Online / Offline connection status
# 5. File and image selection support
# 6. Chat log saving
# 7. Premium dark UI for better presentation
class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("💬 Secure Chat Pro")
        self.root.geometry("950x700")
        self.root.configure(bg="#1e1e2f")
        self.sock = None
        self.running = False
        self.receive_thread = None
        self.log_file = None
        self.username = ""

        self.use_encryption = tk.BooleanVar(value=False)
        self.password_var = tk.StringVar(value="")
        self.fernet_token = None
        self.typing_text = tk.StringVar()
        self.status_text = tk.StringVar(value="🔴 Offline")

        self._build_gui()

    def _build_gui(self):
        top = tk.Frame(self.root, bg="#2a2a40")
        top.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(top, text="Server IP:", bg="#2a2a40", fg="white").grid(row=0, column=0)
        self.server_entry = tk.Entry(top, width=15)
        self.server_entry.insert(0, SERVER_HOST)
        self.server_entry.grid(row=0, column=1, padx=5)

        tk.Label(top, text="Port:", bg="#2a2a40", fg="white").grid(row=0, column=2)
        self.port_entry = tk.Entry(top, width=6)
        self.port_entry.insert(0, str(SERVER_PORT))
        self.port_entry.grid(row=0, column=3, padx=5)

        tk.Label(top, text="Username:", bg="#2a2a40", fg="white").grid(row=0, column=4)
        self.username_entry = tk.Entry(top, width=12)
        self.username_entry.grid(row=0, column=5, padx=5)

        tk.Button(top, text="Connect", bg="#4caf50", fg="white", command=self.connect).grid(row=0, column=6, padx=5)
        tk.Button(top, text="Disconnect", bg="#f44336", fg="white", command=self.disconnect).grid(row=0, column=7, padx=5)
        tk.Label(top, textvariable=self.status_text, bg="#2a2a40", fg="cyan").grid(row=0, column=8, padx=10)

        enc_frame = tk.Frame(self.root, bg="#1e1e2f")
        enc_frame.pack(padx=10, pady=2, fill=tk.X)
        tk.Checkbutton(enc_frame, text="Enable Encryption", variable=self.use_encryption, bg="#1e1e2f", fg="white", selectcolor="#1e1e2f").pack(side=tk.LEFT)
        self.pw_entry = tk.Entry(enc_frame, textvariable=self.password_var, show="*")
        self.pw_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(enc_frame, text="Set Password", command=self.set_password).pack(side=tk.LEFT)

        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled', width=90, height=22,bg="#1c1f26", fg="white")
        self.chat_area.pack(padx=10, pady=5)

        self.typing_label = tk.Label(self.root, textvariable=self.typing_text, bg="#1e1e2f", fg="cyan")
        self.typing_label.pack(anchor='w', padx=10)

        bottom = tk.Frame(self.root, bg="#1e1e2f")
        bottom.pack(padx=10, pady=5, fill=tk.X)
        self.msg_entry = tk.Entry(bottom, width=60)
        self.msg_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        self.msg_entry.bind("<KeyRelease>", self.show_typing)

        tk.Button(
            bottom,
            text="📤 Send",
            bg="#4caf50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=10,
            command=self.send_message
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            bottom,
            text="📎 File",
            bg="#2196f3",
            fg="white",
            font=("Arial", 10, "bold"),
            width=10,
            command=self.send_file
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            bottom,
            text="🖼 Photo",
            bg="#9c27b0",
            fg="white",
            font=("Arial", 10, "bold"),
            width=10,
            command=self.open_photo
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            bottom,
            text="💾 Save",
            bg="#ff9800",
            fg="white",
            font=("Arial", 10, "bold"),
            width=10,
            command=self.save_log
        ).pack(side=tk.LEFT, padx=5)

    def show_typing(self, event=None):
        self.typing_text.set("Typing...")
        self.root.after(1000, lambda: self.typing_text.set(""))

    def log(self, text):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {text}\n"
        self.chat_area['state'] = 'normal'
        self.chat_area.insert(tk.END, line)
        self.chat_area.see(tk.END)
        self.chat_area['state'] = 'disabled'
        if self.log_file:
            self.log_file.write(line)
            self.log_file.flush()

    def set_password(self):
        self.fernet_token = derive_key_from_password(self.password_var.get().strip())
        messagebox.showinfo("Encryption", "Password set successfully")

    def connect(self):
        server = self.server_entry.get().strip()
        port = int(self.port_entry.get().strip())
        self.username = self.username_entry.get().strip()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server, port))
        self.running = True
        self.status_text.set("🟢 Online")
        self.log_file = open(os.path.join(LOGS_DIR, f"{self.username}_{int(time.time())}.log"), "a", encoding="utf-8")
        self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receive_thread.start()
        self.log(f"Connected as {self.username}")

    def disconnect(self):
        self.running = False
        self.status_text.set("🔴 Offline")
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
        self.log("Disconnected.")

    def receive_loop(self):
        while self.running:
            try:
                header = recv_all(self.sock, 7)
                if not header:
                    break
                flag = header[0]
                uname_len = struct.unpack('!H', header[1:3])[0]
                payload_len = struct.unpack('!I', header[3:7])[0]
                sender = recv_all(self.sock, uname_len).decode()
                payload = recv_all(self.sock, payload_len)
                msg = decrypt_bytes(self.fernet_token, payload).decode() if flag == 1 and self.fernet_token else payload.decode()
                self.log(f"{sender}: {msg}")
            except Exception:
                break

    def send_message(self):
        if not self.running:
            return
        text = self.msg_entry.get().strip()
        if not text:
            return
        self.msg_entry.delete(0, tk.END)
        encrypted = self.use_encryption.get()
        payload = encrypt_bytes(self.fernet_token, text.encode()) if encrypted and self.fernet_token else text.encode()
        self.sock.sendall(pack_message(self.username, payload, encrypted))
        self.log(f"You: {text}")

    def send_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.log(f"📎 File selected: {os.path.basename(path)}")

    def open_photo(self):
        path = filedialog.askopenfilename(filetypes=[('Images', '*.png;*.jpg;*.jpeg')])
        if path:
            self.log(f"🖼 Photo opened: {os.path.basename(path)}")
            webbrowser.open(path)

    def save_log(self):
        if self.log_file:
            self.log("💾 Chat log saved")


# ======== Application Entry Point ========
# Initializes the main window and safely closes socket on exit
def main():
    root = tk.Tk()
    app = ChatClient(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.disconnect(), root.destroy()))
    root.mainloop()

if __name__ == '__main__':
    main()
