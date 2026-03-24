import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from tkcalendar import Calendar
from PIL import Image, ImageTk
import os, cv2, re, numpy as np, pandas as pd
import pytesseract, pyttsx3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
from ultralytics import YOLO
from customtkinter import CTkImage
import threading

# Initialize
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("1200x700")
app.title("Number Plate Recognition")

# Set background image
# Load and resize background once
bg_image = Image.open("background2.jpg")
bg_resized = bg_image.resize((1200, 700))  # Match initial window size

bg_ctk = ctk.CTkImage(light_image=bg_resized, size=(1600, 800))
bg_label = ctk.CTkLabel(app, text="", image=bg_ctk)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

def speak_message(text):
    def run_speech():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run_speech).start()

model = YOLO("best.pt")
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

save_dir = "predicted_image"
os.makedirs(save_dir, exist_ok=True)

df = pd.read_csv('data.csv')

def send_email(vemail, vnumber, complaint, date):
    sender_email = "myprojectemails4u@gmail.com"
    sender_password = "cyaoslrmrystypcm"
    subject = "Violation Email"

    plain_message = f"Complaint: {complaint}\nDate: {date}\nVehicle Number: {vnumber}"

    html_message = f"""
    <html>
        <body>
            <p><strong>Complaint:</strong> {complaint}<br>
               <strong>Date:</strong> {date}<br>
               <strong>Vehicle Number:</strong> {vnumber}</p>
            <p><strong>Detected Number Plate Image:</strong><br>
               <img src="cid:image1" width="300"></p>
        </body>
    </html>
    """

    msg = MIMEMultipart('related')
    msg['From'] = sender_email
    msg['To'] = vemail
    msg['Subject'] = subject

    alt_part = MIMEMultipart('alternative')
    alt_part.attach(MIMEText(plain_message, 'plain'))
    alt_part.attach(MIMEText(html_message, 'html'))
    msg.attach(alt_part)

    speak_message(plain_message)

    cropped_images = [f for f in os.listdir(save_dir) if f.endswith(".jpg")]
    if cropped_images:
        image_path = os.path.join(save_dir, cropped_images[0])
        with open(image_path, 'rb') as f:
            img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(image_path))
            image.add_header('Content-ID', '<image1>')
            image.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_path))
            msg.attach(image)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        messagebox.showinfo("Alert", "Email sent successfully!")
        reset_page()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def display_info(vnumber):
    if vnumber in df['number'].values:
        row = df[df['number'] == vnumber].iloc[0]
        if complaint_var.get() == "Select Complaint" or not selected_date.get():
            messagebox.showinfo("Alert", "Please select both a complaint and a date!")
            return
        send_email(row['email'], row['number'], complaint_var.get(), selected_date.get())
    else:
        messagebox.showinfo("Alert", "Vehicle number not found!")

def reset_page():
    # Clear image previews
    sign_image.configure(image=None, text="Upload Image")
    sign_image.image = None
    resultimg.configure(image=None, text="Detected Plate")
    resultimg.image = None

    # Reset complaint and date
    complaint_var.set("Select Complaint")
    selected_date.set("")

    # Clear cropped image folder
    for f in os.listdir(save_dir):
        if f.endswith(".jpg"):
            os.remove(os.path.join(save_dir, f))


def extract_letters_numbers(s):
    return ''.join(re.findall(r'[A-Za-z0-9]', s))

def preprocess_image(image_path):
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return cv2.medianBlur(binary_image, 3)

def extract_handwritten_text(image_path):
    preprocessed_image = preprocess_image(image_path)
    return pytesseract.image_to_string(preprocessed_image, config='--psm 6')

def browse_and_predict(file_path):
    results = model.predict(source=file_path, conf=0.5, save=False)
    for result in results:
        img = cv2.imread(file_path)
        for i, box in enumerate(result.boxes.xyxy):
            x1, y1, x2, y2 = map(int, box)
            cropped_img = img[y1:y2, x1:x2]
            save_path = os.path.join(save_dir, f"cropped_{i}.jpg")
            cv2.imwrite(save_path, cropped_img)
    display_cropped_image()

def display_cropped_image():
    cropped_images = [f for f in os.listdir(save_dir) if f.endswith(".jpg")]
    if cropped_images:
        first_cropped_path = os.path.join(save_dir, cropped_images[0])
        img = Image.open(first_cropped_path).resize((300, 150))
        ctk_img = CTkImage(light_image=img, size=(300, 150))
        resultimg.configure(image=ctk_img)
        resultimg.image = ctk_img
        text = extract_handwritten_text(first_cropped_path)
        filtered_text = extract_letters_numbers(text)
        messagebox.showinfo("Extracted Number", filtered_text)
        display_info(filtered_text)

def upload_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", ".jpg;.png")])
    if not file_path:
        return
    uploaded = Image.open(file_path)
    resized = uploaded.resize((350, 250))
    ctk_img = CTkImage(light_image=resized, size=(350, 250))
    sign_image.configure(image=ctk_img)
    sign_image.image = ctk_img
    classify_button.configure(command=lambda: browse_and_predict(file_path))

def upload_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", ".mp4;.avi")])
    cap = cv2.VideoCapture(file_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = int(1000 / fps)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model.predict(source=frame, conf=0.80, save=False)
        cv2.imshow('Video Frame', results[0].plot())
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def webcam_live():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        results = model.predict(source=frame, conf=0.80, save=False)
        cv2.imshow('Webcam Live', results[0].plot())
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def show_calendar():
    top_calendar = ctk.CTkToplevel(app)
    top_calendar.grab_set()
    top_calendar.lift()
    top_calendar.attributes('-topmost', True)
    cal = Calendar(top_calendar, selectmode="day", date_pattern="yyyy-mm-dd")
    cal.pack(pady=10)

    def select_date():
        selected_date.set(cal.get_date())
        top_calendar.destroy()

    ctk.CTkButton(top_calendar, text="Select Date", command=select_date).pack(pady=10)

def show_contact_us():
    contact_window = ctk.CTkToplevel(app)
    contact_window.title("Information")
    contact_window.geometry("450x400")
    contact_window.resizable(False, False)
    contact_window.grab_set()
    contact_window.attributes('-topmost', True)

    tab_view = ctk.CTkTabview(contact_window, width=430, height=360)
    tab_view.pack(pady=10, padx=10)

    # Tabs
    tab_view.add("Home")
    tab_view.add("About")
    tab_view.add("Contact Us")

    # Home Tab Content
    ctk.CTkLabel(tab_view.tab("Home"), text="Welcome to AutoPlate Monitoring System!",
                 font=("Helvetica", 16, "bold")).pack(pady=10)
    ctk.CTkLabel(tab_view.tab("Home"),
                 text="This system automatically detects vehicle number plates and sends reports for violations.",
                 font=("Helvetica", 13), wraplength=400, justify="left").pack(pady=5)

    # About Tab Content
    ctk.CTkLabel(tab_view.tab("About"), text="About the Project",
                 font=("Helvetica", 16, "bold")).pack(pady=10)
    ctk.CTkLabel(tab_view.tab("About"),
                 text="Developed by the AutoPlate Monitors team using computer vision (YOLOv8) and OCR technologies. "
                      "Designed for smart city surveillance.",
                 font=("Helvetica", 13), wraplength=400, justify="left").pack(pady=5)

    # Contact Us Tab Content
    ctk.CTkLabel(tab_view.tab("Contact Us"), text="Get in Touch",
                 font=("Helvetica", 16, "bold")).pack(pady=10)
    ctk.CTkLabel(tab_view.tab("Contact Us"), text="Email: ourprojectemails@gmail.com", font=("Helvetica", 13)).pack()
    ctk.CTkLabel(tab_view.tab("Contact Us"), text="Phone: +91-9876543210", font=("Helvetica", 13)).pack()
    ctk.CTkLabel(tab_view.tab("Contact Us"), text="Address: XYZ Institute, City, Country", font=("Helvetica", 13)).pack()

    # Close Button
    ctk.CTkButton(tab_view.tab("Contact Us"), text="Close", command=contact_window.destroy, width=180, height=40).pack(pady=15)

# GUI Elements
header = ctk.CTkLabel(app, text="Number Plate Recognition System", font=("Helvetica", 24, "bold"))
header.place(relx=0.5, rely=0.05, anchor=tk.CENTER)

frame = ctk.CTkFrame(app)
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

image_frame = ctk.CTkFrame(frame, width=350, height=250, fg_color="gray20", corner_radius=12)
image_frame.grid(row=0, column=0, padx=20, pady=10)
sign_image = ctk.CTkLabel(image_frame, text="Upload Image")
sign_image.pack()

result_frame = ctk.CTkFrame(frame, width=300, height=150, fg_color="gray20", corner_radius=12)
result_frame.grid(row=0, column=1, padx=20, pady=10)
resultimg = ctk.CTkLabel(result_frame, text="Detected Plate")
resultimg.pack()

ctk.CTkButton(frame, text="Upload Vehicle Image", command=upload_image, width=200).grid(row=1, column=0, pady=5)
ctk.CTkButton(frame, text="Upload Vehicle Video", command=upload_video, width=200).grid(row=2, column=0, pady=5)
ctk.CTkButton(frame, text="Live Webcam", command=webcam_live, width=200).grid(row=3, column=0, pady=5)

classify_button = ctk.CTkButton(frame, text="Detect Number Plate", width=200)
classify_button.grid(row=4, column=0, pady=5)

complaints = ["Signal Jumping",
    "Illegal Parking",
    "Speeding",
    "Wrong Lane",
    "No Helmet",
    "Unregistered Vehicle",
    "Overtaking in No-Overtake Zone",
    "Driving Without License",
    "Using Mobile While Driving",
    "Overloading",
    "Running a Stop Sign"]
complaint_var = ctk.StringVar(value="Select Complaint")
ctk.CTkLabel(frame, text="Complaint Type:").grid(row=1, column=1, sticky="w")
ctk.CTkComboBox(frame, values=complaints, variable=complaint_var, width=200).grid(row=1, column=2, padx=10)

selected_date = ctk.StringVar()
ctk.CTkLabel(frame, text="Violation Date:").grid(row=2, column=1, sticky="w")
ctk.CTkButton(frame, text="Choose Date", command=show_calendar, width=200).grid(row=2, column=2, padx=10)

ctk.CTkButton(frame, text="Contact Us", command=show_contact_us, width=200).grid(row=3, column=2, padx=10, pady=10)

app.mainloop()