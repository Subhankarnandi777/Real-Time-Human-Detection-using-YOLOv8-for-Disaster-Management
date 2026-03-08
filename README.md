# 🚁 Real-Time Human Detection using YOLOv8 for Disaster Management

## 📌 Overview

Natural disasters such as **🌊 floods, ⛰ landslides, 🌍 earthquakes, and 🌪 cyclones** often affect rural and remote areas where rescue teams face difficulties locating trapped victims quickly.

This project presents a **Real-Time Human Detection System using YOLOv8 deployed on a Raspberry Pi mounted on a drone**. The system automatically detects humans in disaster zones and calculates their **approximate GPS coordinates**.

These coordinates help **rescue teams quickly locate survivors and deliver medical kits or emergency supplies**.

The system combines **🤖 Computer Vision, Edge AI, and Geolocation Estimation** to assist disaster response teams in identifying people who may be trapped or stranded in affected regions.

---

# ✨ Key Features

- ✅ Real-time **Human Detection using YOLOv8**
- 🧠 **Edge AI inference on Raspberry Pi**
- 🚁 **Drone-based surveillance system**
- 📏 **Distance estimation using bounding box height**
- 📍 **GPS coordinate projection from drone position**
- 👁 **Human Detected / No Human status display**
- ⚡ **Low-latency threaded video capture**
- 🆘 Optimized for **real-time disaster response**

---

# 🏗 System Architecture

![System Architecture](assets/system_architecture.png)

---

# 🛠 Technologies Used

- 🐍 **Python**
- 🤖 **YOLOv8 (Ultralytics)**
- 📷 **OpenCV**
- 🔥 **PyTorch**
- 🍓 **Raspberry Pi**
- 🚁 **Drone Platform**
- 👁 **Computer Vision**
- ⚡ **Edge AI**
- 📍 **GPS Coordinate Projection**

---

# ⚙ How the System Works

1️⃣ The **drone captures real-time video** of the disaster area.

2️⃣ Video frames are processed on **Raspberry Pi**.

3️⃣ The **YOLOv8 model detects humans** in each frame.

4️⃣ The system calculates:

- 📦 Bounding box of detected human
- 📏 Estimated distance from drone

5️⃣ Using **drone heading and camera field of view**, the system computes the **bearing of the detected person**.

6️⃣ The **bearing and distance** are used to **project GPS coordinates**.

7️⃣ The drone can **drop medical kits or send location coordinates to rescue teams**.

---

# 📏 Distance Estimation Method

Distance is estimated using a **pinhole camera model**:
