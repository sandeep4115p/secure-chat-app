import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os
import random
import smtplib
from email.mime.text import MIMEText
import subprocess

USER_FILE = "users.json"

EMAIL_ADDRESS = "sk9682398781@gmail.com"
EMAIL_PASSWORD = "tlnt fegy tkpi avhl"


# ================= USER FUNCTIONS =================
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as file:
            return json.load(file)
    return {}


def save_users(users):
    with open(USER_FILE, "w") as file:
        json.dump(users, file)


users = load_users()


# ================= EMAIL OTP =================
def send_otp_email(receiver_email, otp):
    try:
        msg = MIMEText(f"Your signup OTP is: {otp}")
        msg["Subject"] = "Signup OTP Verification"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = receiver_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, receiver_email, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        messagebox.showerror("Email Error", str(e))
        return False


# ================= SERVER / CHAT =================
def start_server():
    subprocess.Popen(["python", "server.py"])


def open_chat():
    subprocess.Popen(["python", "client.py"])


# ================= DASHBOARD =================
def open_launcher():
    launcher = tk.Toplevel()
    launcher.title("Secure Chat Dashboard")
    launcher.geometry("500x500")
    launcher.configure(bg="#121212")

    tk.Label(
        launcher,
        text="Welcome to Secure Chat",
        font=("Arial", 20, "bold"),
        fg="white",
        bg="#121212"
    ).pack(pady=40)

    tk.Button(
        launcher,
        text="Start Server",
        width=20,
        height=2,
        bg="#00BFFF",
        fg="white",
        font=("Arial", 14, "bold"),
        command=start_server
    ).pack(pady=20)

    tk.Button(
        launcher,
        text="Open Chat",
        width=20,
        height=2,
        bg="#00BFFF",
        fg="white",
        font=("Arial", 14, "bold"),
        command=open_chat
    ).pack(pady=20)

    tk.Button(
        launcher,
        text="Exit",
        width=20,
        height=2,
        command=launcher.destroy
    ).pack(pady=20)


# ================= LOGIN =================
def login():
    email = email_entry.get().strip()
    password = password_entry.get().strip()

    if email in users and users[email] == password:
        messagebox.showinfo("Success", "Login Successful")
        root.withdraw()
        open_launcher()
    else:
        messagebox.showerror("Error", "Invalid email or password")


# ================= REGISTER =================
def register():
    email = simpledialog.askstring("Register", "Enter email")
    password = simpledialog.askstring("Register", "Enter password", show="*")

    if not email or not password:
        return

    if email in users:
        messagebox.showerror("Error", "Email already registered")
        return

    otp = str(random.randint(100000, 999999))

    if send_otp_email(email, otp):
        entered_otp = simpledialog.askstring(
            "OTP Verification",
            "Enter OTP sent to your email"
        )

        if entered_otp == otp:
            users[email] = password
            save_users(users)
            messagebox.showinfo("Success", "Account created successfully")
        else:
            messagebox.showerror("Error", "Invalid OTP")


# ================= FORGOT PASSWORD =================
def forgot_password():
    email = simpledialog.askstring(
        "Forgot Password",
        "Enter registered email"
    )

    if email in users:
        password = users[email]
        messagebox.showinfo("Password", f"Your password is: {password}")
    else:
        messagebox.showerror("Error", "Email not found")


# ================= MAIN UI =================
root = tk.Tk()
root.title("Secure Chat Login")
root.geometry("420x800")
root.configure(bg="#121212")
root.resizable(False, False)

tk.Label(
    root,
    text="English (US)",
    fg="white",
    bg="#121212",
    font=("Arial", 12)
).pack(pady=20)

tk.Label(
    root,
    text="🔐",
    fg="white",
    bg="#121212",
    font=("Arial", 50)
).pack(pady=10)

email_entry = tk.Entry(
    root,
    font=("Arial", 14),
    width=30,
    bg="#1e1e1e",
    fg="white",
    insertbackground="white",
    relief="flat"
)
email_entry.pack(pady=15, ipady=12)
email_entry.insert(0, "Email")

password_entry = tk.Entry(
    root,
    font=("Arial", 14),
    width=30,
    bg="#1e1e1e",
    fg="white",
    insertbackground="white",
    relief="flat",
    show="*"
)
password_entry.pack(pady=10, ipady=12)

tk.Button(
    root,
    text="Log in",
    bg="#1877F2",
    fg="white",
    font=("Arial", 16, "bold"),
    width=28,
    height=2,
    bd=0,
    command=login
).pack(pady=20)

tk.Button(
    root,
    text="Forgot password?",
    bg="#121212",
    fg="white",
    font=("Arial", 12),
    bd=0,
    command=forgot_password
).pack(pady=10)

tk.Label(root, bg="#121212").pack(pady=50)

tk.Button(
    root,
    text="Create new account",
    bg="#121212",
    fg="#00BFFF",
    font=("Arial", 14, "bold"),
    width=28,
    height=2,
    highlightbackground="#00BFFF",
    highlightthickness=2,
    bd=0,
    command=register
).pack(pady=20)

tk.Label(
    root,
    text="Meta",
    fg="white",
    bg="#121212",
    font=("Arial", 16, "bold")
).pack(side="bottom", pady=20)

root.mainloop()