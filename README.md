# Project IDentify – Facial Recognition Attendance System

Project IDentify is a local web application that automates classroom attendance using facial recognition. It replaces manual roll calls by identifying students through a standard webcam and recording their attendance in real time.

Built with Python, Streamlit, OpenCV, face_recognition, dlib, and MySQL.

---

## 👥 Team & Roles

| Member                     | Role                             |
| -------------------------- | -------------------------------- |
| **Siddhartha Raj Awasthi** | Team Lead · Recognition Back-end |
| **Aayush Dahal**           | Front-end Developer              |
| **Sriya Adhikari**         | Database Back-end                |
| **Aayush Pradhan**         | Business Analyst                 |
| **Sundar Suwal**           | Tester                           |

**Supervisor:** Mr. Sanjog Sigdel
**Course:** COM 244 – Project Work
**Institution:** Kathmandu University School of Management

---

## 🚀 Features

* Admin login with SHA-256 password hashing
* Student management (add, list, and delete students)
* Face enrollment using webcam capture
* Stores an averaged facial encoding from 30 face samples
* Real-time facial landmark detection with 68-point overlay
* MySQL database for secure offline storage
* Streamlit-based dashboard for easy administration
* CSV export support for attendance records

---

## 🛠️ Technology Stack

| Layer              | Technology                             |
| ------------------ | -------------------------------------- |
| Front-end          | Streamlit                              |
| Back-end           | Python, OpenCV, face_recognition, dlib |
| Database           | MySQL                                  |
| Face Recognition   | face_recognition (dlib)                |
| Landmark Detection | dlib 68-point Facial Landmark Model    |
| Data Export        | Pandas, CSV                            |

---

## 📦 Setup Instructions

### 1. Prerequisites

Before running the application, ensure the following are installed:

* Python 3.9 or higher
* MySQL Server
* Webcam

---

### 2. Clone the Repository

```bash
git clone https://github.com/SidAwasthi88/project-identify.git
cd project-identify
```

### 3. Create and Activate a Virtual Environment

#### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Set Up the MySQL Database

Log in to MySQL and run:

```sql
CREATE DATABASE identify_db;

CREATE USER 'identify_user'@'localhost'
IDENTIFIED BY 'identify123';

GRANT ALL PRIVILEGES
ON identify_db.*
TO 'identify_user'@'localhost';

FLUSH PRIVILEGES;
```

### 6. Create the First Admin Account

```bash
python create_first_admin.py
```

Enter the requested information:

* Username
* Full Name
* Password

Example:

```text
Username: admin1
Full Name: Administrator
Password: password1
```

### 7. Run the Application

```bash
streamlit run src/app.py
```

Open your browser and navigate to:

```text
http://localhost:8501
```

Log in using the administrator credentials you created.

---

## 📁 Project Structure

```text
project-identify/
├── data/
│   └── embeddings/
│       └── *.pkl
│
├── src/
│   ├── app.py
│   │
│   ├── database/
│   │   ├── db.py
│   │   └── db_queries.py
│   │
│   ├── enrollment/
│   │   └── enroll_face.py
│   │
│   ├── recognition/
│   │   ├── camera_test.py
│   │   ├── recognize.py
│   │   └── landmark_test.py
│   │
│   └── dashboard/
│       ├── session.py
│       └── export.py
│
├── tests/
│   └── test_database.py
│
├── create_first_admin.py
├── requirements.txt
└── README.md
```

---

## 📖 Usage Guide

### First-Time Setup

1. Create an administrator account using:

   ```bash
   python create_first_admin.py
   ```

2. Start the application:

   ```bash
   streamlit run src/app.py
   ```

3. Log in using your administrator credentials.

---

### Managing Students

1. Navigate to **Students → Add Student**.
2. Enter the student's details.
3. Save the record.

---

### Face Enrollment

1. Open **Face Enrollment**.
2. Select a student.
3. Click **Start Face Enrollment**.
4. The webcam will capture 30 facial samples.
5. An averaged facial encoding is stored for future recognition.

---

### Taking Attendance *(Coming Soon)*

1. Start an attendance session.
2. Students present themselves to the webcam.
3. The system recognises registered faces.
4. Attendance is marked automatically.
5. Export attendance records as CSV.

---

## 🔧 Troubleshooting

### dlib Fails to Install on Windows

dlib requires a C++ compiler.

Install:

* Visual Studio Build Tools
* Desktop Development with C++ workload

Then run:

```bash
pip install dlib
```

---

### Webcam Window Does Not Open Properly

The project uses:

```python
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow()
```

to ensure a usable webcam window size.

---

### MySQL Connection Refused

Check that:

1. MySQL service is running.

Linux:

```bash
sudo systemctl start mysql
```

2. Database credentials in:

```text
src/database/db.py
```

match the configured MySQL user and password.

---

## 📝 Future Work

* Attendance session management
* Automatic absent marking
* Manual attendance override by teachers
* Subject-wise attendance records
* CSV export by session or subject
* Blink-based liveness detection
* User Acceptance Testing (UAT) with real students
* Performance optimisation for larger classrooms

---

## 📄 License

This project was developed as part of the Bachelor of Business Information Systems (BBIS) programme at Kathmandu University School of Management for the COM 244 Project Work course.

This repository is intended for academic and educational purposes.
