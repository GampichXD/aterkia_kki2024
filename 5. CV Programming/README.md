# Computer Vision Programming Documentation

Ok, in the final round, we will get coding in Visual Studio Code. You can download the source code, but these is the explanation about the code.


## Explanation of the Code

### **1. Library Imports**
The script starts with importing the necessary Python libraries, such as `serial` for serial communication, `firebase_admin` for Firebase integration, `cv2` for computer vision operations, and others like `math`, `numpy`, and threading for calculations, matrix operations, and multithreading. 

- **Supervision and YOLOv10**: These libraries enable object detection. YOLOv10 is used for real-time object detection.
- **Firebase**: Integrates the application with Firebase Realtime Database and Firebase Storage for data storage and retrieval.

---

### **2. Firebase Initialization**
```python
cred = credentials.Certificate("ardutofirebase-firebase-adminsdk-p328c-7bbc16ef2d.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://ardutofirebase-default-rtdb.asia-southeast1.firebasedatabase.app/',
    'storageBucket': 'ardutofirebase.appspot.com'
})
```
This section initializes Firebase using service account credentials and sets up the Realtime Database and Cloud Storage bucket.

---

### **3. Serial Communication with Microcontroller**
```python
COM_Mikro = 'COM34'
baud_rate = 115200
time.sleep(2)
```
Defines the communication parameters between the system and a microcontroller. The COM port and baud rate should match the microcontroller settings.

---

### **4. File System Setup**
```python
folder_path = "Box Detect/Greenbox"
os.makedirs(folder_path, exist_ok=True)
```
Creates a directory (`Greenbox`) to store detected underwater object images locally before uploading them to Firebase.

---

### **5. Buoy Detection**
```python
def detect_buoy(titik_tengah_bola, buoys, img, cap):
    ...
```
- **Inputs**:
  - `titik_tengah_bola`: List of detected objects’ center coordinates.
  - `buoys`: Count or state of detected buoys.
  - `img`: Current frame from the video feed.
  - `cap`: Video capture object.

- **Key Features**:
  - Calculates angles and distances for triangulation of detected buoys.
  - Draws visual aids like lines, bounding boxes, and labels on the image for better understanding.
  - Uses the state of detection (`case 0`, `case 1`, `case 2`) to perform different actions based on the number of detected buoys.

---

### **6. Saving and Uploading Images**
```python
def save_and_upload_image(img, filename, folder_path, bucket):
    ...
```
This function saves detected images locally and uploads them to Firebase Storage.

---

### **7. Threading for Image Processing**
```python
def image_processing_thread():
    ...
thread = threading.Thread(target=image_processing_thread, daemon=True)
thread.start()
```
The image processing is handled in a separate thread to avoid blocking the main program, ensuring smooth performance during real-time detection.

---

### **8. Box Detection**
```python
def detect_box():
    ...
```
- **Workflow**:
  1. Captures video frames using OpenCV.
  2. Applies a brightness filter for enhanced visibility.
  3. Uses YOLOv10 for object detection and identifies boxes with high confidence.
  4. Saves images with confidence ≥ 0.5 and uploads them to Firebase.

- **Additional Features**:
  - Visualizes detection by drawing bounding boxes and adding labels.
  - Ensures a single upload per detected object using the `image_saved` flag.

---

### **9. Buoy Detection Loop**
```python
def detect_buoys():
    ...
```
- **Workflow**:
  - Captures live video from the camera.
  - Writes the output to a video file for later analysis.
  - Tracks buoy positions and calculates angular relationships for navigation.

- **Features**:
  - Uses YOLOv10 for buoy detection in the video frames.
  - Provides real-time feedback on detected buoys and their relative positions.

---

### **10. Overall Logic**
The system is designed to detect underwater objects (e.g., boxes) and buoys. It leverages YOLOv10 for object detection and uses Firebase for cloud integration to store detection results and captured images.

---

### **11. Improvements**
- **Efficiency**: Threading improves performance by separating tasks (e.g., image processing and detection).
- **Cloud Integration**: Firebase allows seamless storage and retrieval of data and images.
- **Visualization**: Use of OpenCV for drawing helps users interpret detection results in real-time.

Let me know if you'd like further clarification on any part of the code!

Ok, guys. That's all from Computer Vision Documentation of Kontes Kapal Indonesia 2024 officially by Aterkia Roboboat URDC. Keep spirit and Stay Coding. Bye-Bye.