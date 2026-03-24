#pip install mysql-connector-python
import sys
import tkinter as tk
from tkinter import messagebox
import mysql.connector
import os
from PIL import ImageTk, Image
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Connect to MySQL
conn = mysql.connector.connect(
    host='localhost',
    port=3308,
    user='root',
    password='root',
    database='numberplate',
    charset='utf8'
)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(255) NOT NULL,
                    email VARCHAR(255) PRIMARY KEY,
                    password VARCHAR(255) NOT NULL
                )''')
conn.commit()

# Main Window
root = tk.Tk()
root.title("License Plate Monitoring - Login")
root.geometry("600x400")
root.configure(bg='#F0F4F8')


def center_window(window):
    window.update_idletasks()
    w = window.winfo_width()
    h = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (w // 2)
    y = (window.winfo_screenheight() // 2) - (h // 2)
    window.geometry(f'{w}x{h}+{x}+{y}')


def register():
    register_screen = tk.Toplevel(root)
    register_screen.title("Register")
    register_screen.geometry("350x300")
    register_screen.configure(bg='white')
    center_window(register_screen)

    tk.Label(register_screen, text="Sign Up", font=('Helvetica', 16, 'bold'), bg='white').pack(pady=10)

    frame = tk.Frame(register_screen, bg='white')
    frame.pack(pady=10)

    tk.Label(frame, text="Username", bg='white').grid(row=0, column=0, sticky='e', padx=5, pady=5)
    username_entry = tk.Entry(frame)
    username_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame, text="Email", bg='white').grid(row=1, column=0, sticky='e', padx=5, pady=5)
    email_entry = tk.Entry(frame)
    email_entry.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(frame, text="Password", bg='white').grid(row=2, column=0, sticky='e', padx=5, pady=5)
    password_entry = tk.Entry(frame, show='*')
    password_entry.grid(row=2, column=1, padx=5, pady=5)

    def register_user():
        username = username_entry.get()
        email = email_entry.get()
        password = password_entry.get()
        if username and password and email:
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                messagebox.showerror("Error", "Email already exists.")
            else:
                cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
                conn.commit()
                messagebox.showinfo("Success", "Registered successfully.")
                register_screen.destroy()
        else:
            messagebox.showerror("Error", "All fields are required.")

    tk.Button(register_screen, text="Register", command=register_user, bg='#007ACC', fg='white',
              font=('Helvetica', 10), width=20).pack(pady=20)

def login():
    login_screen = tk.Toplevel(root)
    login_screen.title("Login")
    login_screen.geometry("350x320")
    login_screen.configure(bg='white')
    center_window(login_screen)

    # Load and show the car logo
    logo_path = "blue_car_logo.png"  # Replace with your actual filename
    try:
        img = Image.open(logo_path)
        img = img.resize((60, 60), Image.Resampling.LANCZOS)
        logo_img = ImageTk.PhotoImage(img)
        logo_label = tk.Label(login_screen, image=logo_img, bg='white')
        logo_label.image = logo_img  # Keep reference
        logo_label.pack(pady=(10, 0))
    except Exception as e:
        print("Error loading logo:", e)

    tk.Label(login_screen, text="Login", font=('Helvetica', 16, 'bold'), bg='white').pack(pady=10)

    frame = tk.Frame(login_screen, bg='white')
    frame.pack(pady=10)

    tk.Label(frame, text="Email", bg='white').grid(row=0, column=0, sticky='e', padx=5, pady=5)
    email_entry = tk.Entry(frame)
    email_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame, text="Password", bg='white').grid(row=1, column=0, sticky='e', padx=5, pady=5)
    password_entry = tk.Entry(frame, show='*')
    password_entry.grid(row=1, column=1, padx=5, pady=5)

    # Load the eye icon for show/hide password
    eye_icon_path = "eye_icon.jpg"  # Update path if necessary
    eye_icon = Image.open(eye_icon_path)
    eye_icon = eye_icon.resize((20, 20), Image.Resampling.LANCZOS)
    eye_icon_image = ImageTk.PhotoImage(eye_icon)

    # Function to toggle password visibility
    def toggle_password():
        if password_entry.cget('show') == '*':
            password_entry.config(show='')
            eye_button.config(image=eye_icon_image)
        else:
            password_entry.config(show='*')
            eye_button.config(image=eye_icon_image)

    # Add the eye icon as a button
    eye_button = tk.Button(frame, image=eye_icon_image, bg='white', bd=0, command=toggle_password)
    eye_button.grid(row=1, column=2, padx=5)

    def send_email(password):
        sender_email = "ourprojectemails@gmail.com"
        sender_password = "oxipcucyayarblht"
        receiver_email = email_entry.get()
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = "Forgot password"
        msg.attach(MIMEText(password + " is your password", 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            messagebox.showinfo("Success", "Password sent to your email.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def forgot_password():
        email = email_entry.get()
        if email:
            cursor.execute("SELECT password FROM users WHERE email=%s", (email,))
            result = cursor.fetchone()
            if result:
                send_email(result[0])
            else:
                messagebox.showerror("Error", "Email not found.")
        else:
            messagebox.showinfo("Alert", "Email field cannot be blank")

    def login_user():
        email = email_entry.get()
        password = password_entry.get()
        if email and password:
            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
            if cursor.fetchone():
                messagebox.showinfo("Success", "Login successful!")
                login_screen.destroy()
                root.withdraw()
                os.system("python newGUI.py")
            else:
                messagebox.showerror("Error", "Invalid credentials")
        else:
            messagebox.showerror("Error", "All fields are required")

    tk.Button(login_screen, text="Login", command=login_user, bg='#007ACC', fg='white',
              font=('Helvetica', 10), width=20).pack(pady=10)

    tk.Button(login_screen, text="Forgot Password", command=forgot_password, bg='gray85',
              font=('Helvetica', 9), width=20).pack(pady=5)


# Main UI Buttons
tk.Label(root, text="Automated License Plate Monitoring", bg='#F0F4F8', font=('Helvetica', 18, 'bold')).pack(pady=40)

tk.Button(root, text="Login", command=login, bg='#007ACC', fg='white',
          font=('Helvetica', 12), width=20).pack(pady=10)

tk.Button(root, text="Register", command=register, bg='gray90',
          font=('Helvetica', 12), width=20).pack(pady=10)

center_window(root)
root.mainloop()

conn.close()