import os, cv2, re
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox, filedialog
from tkcalendar import Calendar
from PIL import ImageTk, Image
import numpy as np
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pyttsx3
import pytesseract
from ultralytics import YOLO

# Initialize GUI window
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)
top = tk.Tk()
top.geometry('1500x800')
top.title('Number Plate Recognition')
top.configure(bg='white')

# Background image
img = PhotoImage(file='bg.png', master=top)
img_label = Label(top, image=img)
img_label.place(x=0, y=0, relwidth=1, relheight=1)

# Styling
style = ttk.Style()
style.theme_use('clam')
style.configure('TButton', font=('Arial', 10), padding=6, background='#007acc', foreground='white')
style.configure('TCombobox', padding=6)

# Create directory for predicted images
save_dir = "predicted_image"
os.makedirs(save_dir, exist_ok=True)

# Load YOLO model
model = YOLO("best.pt")

np.set_printoptions(suppress=True)

# Complaints dropdown
complaints = ["Speeding", "Illegal Parking", "Signal Jumping", "Wrong Lane", "No Helmet"]
complaint_var = StringVar(top)
complaint_var.set("Select Complaint")
complaint_label = Label(top, text="Complaint:", bg='white', font=('Arial', 10, 'bold'))
complaint_label.place(relx=0.45, rely=0.65)
complaint_menu = ttk.Combobox(top, textvariable=complaint_var, values=complaints, state="readonly", width=30)
complaint_menu.place(relx=0.52, rely=0.65)

# Date selection
selected_date = StringVar(top)
date_label = Label(top, text="Date:", bg='white', font=('Arial', 10, 'bold'))
date_label.place(relx=0.45, rely=0.70)
date_button = ttk.Button(top, text="Choose Date", command=lambda: show_calendar())
date_button.place(relx=0.52, rely=0.70)

def show_calendar():
    top_calendar = Toplevel(top)
    cal = Calendar(top_calendar, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack(pady=20)
    def select_date():
        selected_date.set(cal.get_date())
        top_calendar.destroy()
    select_btn = ttk.Button(top_calendar, text="Select Date", command=select_date)
    select_btn.pack()

# Email function
def send_email(vemail, vnumber, complaint, date):
    sender_email = "ourprojectemails@gmail.com"
    sender_password = "oxipcucyayarblht"
    subject = "Violation Email"
    message = f"Complaint: {complaint}\nDate: {date}\nVehicle Number: {vnumber}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = vemail
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))
    engine.say(message)
    engine.runAndWait()
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        messagebox.showinfo("Alert", "Email sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Display vehicle information and send email
df = pd.read_csv('data.csv')

def display_info(vnumber):
    if vnumber in df['number'].values:
        row = df[df['number'] == vnumber].iloc[0]
        selected_complaint = complaint_var.get()
        if selected_complaint == "Select Complaint" or not selected_date.get():
            messagebox.showinfo("Alert", "Please select both a complaint and a date!")
            return
        send_email(row['email'], row['number'], selected_complaint, selected_date.get())
    else:
        messagebox.showinfo("Alert", "Vehicle number not found!")

def extract_letters_numbers(s):
    return ''.join(re.findall(r'[A-Za-z0-9]', s))

def browse_and_predict(file_path):
    if complaint_var.get() == "Select Complaint" or not selected_date.get():
        messagebox.showinfo("Alert", "Please select both a complaint and a date!")
        return
    if not file_path:
        return
    results = model.predict(source=file_path, conf=0.5, save=False)
    for result in results:
        img = cv2.imread(file_path)
        for i, box in enumerate(result.boxes.xyxy):
            x1, y1, x2, y2 = map(int, box)
            cropped_img = img[y1:y2, x1:x2]
            save_path = os.path.join(save_dir, f"cropped_{i}.jpg")
            cv2.imwrite(save_path, cropped_img)
    display_cropped_image()

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    filtered_image = cv2.medianBlur(binary_image, 3)
    return filtered_image

def extract_handwritten_text(image_path):
    preprocessed_image = preprocess_image(image_path)
    text = pytesseract.image_to_string(preprocessed_image, config='--psm 6')
    return text

def display_cropped_image():
    cropped_images = [f for f in os.listdir(save_dir) if f.endswith(".jpg")]
    if cropped_images:
        first_cropped_path = os.path.join(save_dir, cropped_images[0])
        img = Image.open(first_cropped_path)
        img = img.resize((350, 250), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        resultimg.configure(image=img_tk)
        resultimg.image = img_tk
        text = extract_handwritten_text(first_cropped_path)
        filtered_text = extract_letters_numbers(text)
        messagebox.showinfo("Extracted Number", filtered_text)
        display_info(filtered_text)

def show_classify_button(file_path):
    classify_b = ttk.Button(top, text="Detect Number Plate", command=lambda: browse_and_predict(file_path))
    classify_b.place(relx=0.30, rely=0.75)

def webcam_live():
    cap = cv2.VideoCapture(0)
    model = YOLO('best.pt')
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        results = model.predict(mode="predict", model="best.pt", conf=0.80, source=frame)
        annotatedimg = results[0].plot()
        cv2.imshow('Webcam Live Feed', annotatedimg)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def upload_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", ".mp4;.avi")])
    if not file_path:
        print("Error: No file selected.")
        return
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return
    model = YOLO('best.pt')
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_delay = int(1000 / fps)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("End of video or error reading frame.")
                break
            results = model.predict(source=frame, conf=0.80, save=False)
            annotatedimg = results[0].plot()
            cv2.imshow('Video Frame', annotatedimg)
            if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
                break
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Resources released successfully.")

def contactus():
    os.system("python contactus.py")

def upload_image():
    try:
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", ".jpg;.png")])
        uploaded = Image.open(file_path)
        uploaded.thumbnail(((top.winfo_width() / 3.25), (top.winfo_height() / 3.25)))
        im = ImageTk.PhotoImage(uploaded)
        sign_image.configure(image=im)
        sign_image.image = im
        label.configure(text='')
        show_classify_button(file_path)
    except:
        pass

label = Label(top, bg='white', font=('arial', 15, 'bold'))
sign_image = Label(top, bg='white')
sign_image.place(relx=0.10, rely=0.26)

resultimg = Label(top, bg='white')
resultimg.place(relx=0.60, rely=0.26)

upload = ttk.Button(top, text="Upload Vehicle Image", command=upload_image)
upload.place(relx=0.10, rely=0.75)

upload_video = ttk.Button(top, text="Upload Vehicle Video", command=upload_video)
upload_video.place(relx=0.10, rely=0.80)

live_video = ttk.Button(top, text="Live Webcam", command=webcam_live)
live_video.place(relx=0.30, rely=0.80)

contact = ttk.Button(top, text="Contact Us", command=contactus)
contact.place(relx=0.50, rely=0.80)

default_bg = Image.new("RGB", (250, 250), (200, 200, 200))
default_bg = ImageTk.PhotoImage(default_bg)

heading = Label(top, text="Number Plate Recognition", pady=20, font=('arial', 20, 'bold'), bg='white', fg='red')
heading.pack()

top.mainloop()