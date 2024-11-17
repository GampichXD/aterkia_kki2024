#Program untuk Vision KKI 2024
#Dibuat oleh : Abraham, Ihsan Harimurti, Obin
#Tahun : 2024
#Versi : 1.4

import serial
import firebase_admin
from firebase_admin import credentials, db, storage
import time
from datetime import datetime
import cv2
import supervision as sv
from ultralytics import YOLOv10
import math
import numpy as np
import threading
import time
import os
import queue


'''
PROGRAM UNTUK MENGIRIMKAN DATA KE FIREBASE
'''

# Setup Firebase
cred = credentials.Certificate("ardutofirebase-firebase-adminsdk-p328c-7bbc16ef2d.json")  # Ganti dengan path ke file JSON kamu
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://ardutofirebase-default-rtdb.asia-southeast1.firebasedatabase.app/',  # Ganti dengan URL Firebase kamu
    'storageBucket': 'ardutofirebase.appspot.com'  # Ganti dengan Firebase Storage bucke-mu
})

# # Fungsi untuk mendapatkan timestamp dalam format YYYY-MM-DD HH:MM:SS
# def get_timestamp():
#     return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# def receive_gps_data_from_arduino(port):
#     ser = serial.Serial(port, 115200)  # Ganti dengan port yang sesuai
#     time.sleep(2)  # Tunggu koneksi serial

#     # Referensi ke Firebase Realtime Database
#     ref = db.reference('sensorData')

#     while True:
#         if ser.in_waiting > 0:
#             data_from_arduino = ser.readline().decode('utf-8', errors='ignore').strip()
#             print(f"Data received from Arduino: {data_from_arduino}")

#             # Parsing GPS data (assumed format: "GPS: Lat: latitude, Lng: longitude, Speed(m/s): velocity, Azimuth: azimuth")
#             try:
#                 if data_from_arduino.startswith("GPS:"):
#                     # Menghapus prefix "GPS:" dan memproses data
#                     data_cleaned = data_from_arduino[4:]  # Hapus 4 karakter dari "GPS:"
                    
#                     # Split data based on comma and extract values
#                     latitude = data_cleaned.split('Lat: ')[1].split(',')[0].strip()
#                     longitude = data_cleaned.split('Lng: ')[1].split(',')[0].strip()
#                     velocity = data_cleaned.split('Speed(m/s): ')[1].split(',')[0].strip()
#                     azimuth = data_cleaned.split('Azimuth: ')[1].strip()

#                     print(f"Parsed GPS Data -> Latitude: {latitude}, Longitude: {longitude}, Velocity: {velocity}, Azimuth: {azimuth}")

#                     # Format data untuk Firebase
#                     sensor_data = {
#                         'latitude': float(latitude),
#                         'longitude': float(longitude),
#                         'speed_ms': float(velocity),
#                         'azimuth': int(azimuth),
#                         'timestamp': get_timestamp()
#                     }

#                     # Push data ke Firebase dengan path berdasarkan timestamp
#                     ref.push(sensor_data)
#                     print("GPS data sent to Firebase successfully")
#                 else:
#                     print("Received data is not GPS data or is invalid.")
#             except Exception as e:
#                 print(f"Failed to send data to Firebase: {e}")

#         time.sleep(2)  # Delay sebelum pembacaan berikutnya

# if __name__ == "__main__":
#     receive_gps_data_from_arduino('COM33')  # Ganti dengan port Serial yang sesuai

'''
PROGRAM UNTUK DETEKSI BUOY DAN KOTAK
'''


#Setup untuk komunikasi serial dengan mikrokontroler
COM_Mikro = 'COM34' #Sesuaikan sesuai COM pada board yang terdeteksi pada komputer
baud_rate = 115200 #Sesuaikan dengan rate dari komunikasi serial
# mikrokontroler = serial.Serial(COM_Mikro,baud_rate)
time.sleep(2) #Untuk membuat delay pada eksekusi (satuan detik)

#Setup Folder Path untuk jalur saving object bawah laut (kotak)
folder_path = "Box Detect/Greenbox"
os.makedirs(folder_path, exist_ok=True)


#Menginisialisasi model YOLOv10
model = YOLOv10('best5.pt') ##menetapkan model yakni hasil best1.pt untuk YOLOv10
namaClass = ['buoy_hijau','buoy_merah'] ##menamai Class sesuai urutan Object yang di-labelling
mission = [1,2,3]
i,j = 0,0
model_kotak = YOLOv10('best_kotak5.pt')
namaClass_kotak = ['kotak']
image_queue = queue.Queue()

#Pengaturan jendela
cv2.namedWindow('Image',cv2.WINDOW_NORMAL) ##membuat dan menamai jendela
cv2.setWindowProperty('Image',cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_NORMAL) ##menampilkan jendela secara fullscreen

#Inisialisasi nilai untuk variabel yang di-loop
sudut_triangulasi = 0.0
speed = 20
time_thruster = 5
time_turning = 6
kirim_data = True
detect = False
lintasan = "A"
count = 0
state = 0
#Penanda Tracking apabila confidence(kepercayaan) yang terdeteksi telah tersimpan
image_saved = False
brightness_value = -50  # Adjust nilai ini agar dapat mengontrol kegelapan

#Fungsi untuk mengirimkan data angle ke Mikrokontroler tiap 500ms
def kirim_data_ke_mikro():
    global kirim_data, sudut_triangulasi, speed
    while kirim_data:
        try:
            mikrokontroler_data = f'{speed:.2f},{sudut_triangulasi:.2f},{detect},{count}\n'
            mikrokontroler.write(mikrokontroler_data.encode())
            print(f"Mengirimkan data ke mikrokontroler: {mikrokontroler_data.strip()}")
        except Exception as A:
            print(f"Gagal untuk mengirimkan data ke mikrokontroler: {A}")
        time.sleep(0.5)
# threading.Thread(target=kirim_data_ke_mikro, daemon=True).start()

def detect_buoy(titik_tengah_bola, buoys, img, cap):
    global detect, count, state
    # Check if buoy is detected
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) ##variabel untuk mendapatkan resolusi lebar frame
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) ##variabel untuk mendapatkan resolusi tinggi frame

    #Definisikam variabel untuk keperluan image editing
    y_tengah_window = int(frame_height * 0.65)
    center_x = frame_width // 2
    center_x_one_buoy = center_x // 2

    match buoys:
        case 0:
            count += 1
            detect = False
            if count != len(mission):
                print("DUH ENAK BANGET BANGKE, ANJING, I LOVE ZEE. AKU PENGEN CELUPIN PALKON KE MEMEK ZEE YANG ANGET \
                        AKU PENGEN BANGET NYUSU SAMA ZEE, AKU DISODORIN TETEK SAMA ZEE SAMPE DIA BILANG, AYO NYUSU DULU.")
            else:
                state = 1
                print("AHHH AKU NGECROTTT ZEEE")
        

        case 1:
            detect = True
            # x_tengah, y_tengah = titik_tengah_bola[0]  # Bola pertama (kiri)
            _, x_tengah, y_tengah= titik_tengah_bola[0][0], titik_tengah_bola[0][1], titik_tengah_bola[0][2]
            center_x_one_buoy = center_x // 2
            # cv2.line(img, titik_tengah_bola[0], (center_x, y_tengah), (255, 255, 255), 2)
            # cv2.line(img, titik_tengah_bola[0], (center_x, frame_height), (255, 255, 255), 2)

            cv2.line(img, (titik_tengah_bola[0][1], titik_tengah_bola[0][2]), (center_x, y_tengah), (255, 255, 255), 2)
            cv2.line(img, (titik_tengah_bola[0][1], titik_tengah_bola[0][2]), (center_x, frame_height), (255, 255, 255), 2)
            sudut_garis_vertikal = math.pi / 2
            if x_tengah > center_x:
                dx_triangulasi = x_tengah - (center_x + center_x_one_buoy)
            if x_tengah < center_x:
                dx_triangulasi = x_tengah - center_x_one_buoy
            else:
                dx_triangulasi = x_tengah
            dy_triangulasi = frame_height - y_tengah
            sudut_garis_triangulasi = math.atan2(dy_triangulasi, dx_triangulasi)

            sudut_triangulasi = math.degrees(abs(sudut_garis_vertikal - sudut_garis_triangulasi))
            if dx_triangulasi < 0:
                sudut__triangulasi = sudut_triangulasi
            else:
                sudut_triangulasi = -sudut_triangulasi
        
            label_triangulasi = f'Sudut Triangulasi: {sudut_triangulasi:.2f} derajat'
            cv2.putText(img, label_triangulasi, (10, 20), 0, 0.5, [0, 0, 255], thickness=1, lineType=cv2.LINE_AA)


        case 2:
            detect = True
            i = next((x for x, (color, _, _) in enumerate(titik_tengah_bola) if color == 0), None)
            j = next((x for x, (color, _, _) in enumerate(titik_tengah_bola) if color == 1), None)
            if i != None and j != None:
                _, x1_tengah, y1_tengah = titik_tengah_bola[i][0], titik_tengah_bola[i][1], titik_tengah_bola[i][2]
                _, x2_tengah, y2_tengah = titik_tengah_bola[j][0], titik_tengah_bola[j][1], titik_tengah_bola[j][2]
                # Menggambar garis antara kedua bola
                cv2.line(img, (x1_tengah, y1_tengah), (x2_tengah, y2_tengah), (255, 255, 255), 2)
            
                mid_x = (x1_tengah + x2_tengah) // 2
                mid_y = (y1_tengah + y2_tengah) // 2
            
                # Garis antara bola pertama dan pusat
                # cv2.line(img, titik_tengah_bola[-2], (center_x, center_y), (0, 255, 0), 2)
                cv2.line(img, (titik_tengah_bola[i][1], titik_tengah_bola[i][2]), (center_x, frame_height), (255, 255, 255), 2)
                # cv2.line(img, (x1_tengah, y1_tengah), (center_x, center_y), (0, 255, 0), 2)
                # # Garis antara bola kedua dan pusat
                # cv2.line(img, (x2_tengah, y2_tengah), (center_x, center_y), (0, 255, 0), 2)
                cv2.line(img, (titik_tengah_bola[j][1], titik_tengah_bola[j][2]), (center_x, frame_height), (255, 255, 255), 2)
                # cv2.line(img, titik_tengah_bola[-1], (center_x, center_y), (0, 0, 255), 2)
            
                # Garis triangulasi (warna putih)
                cv2.line(img, (mid_x, mid_y), (center_x, frame_height), (255, 255, 255), 2)

                # Sudut garis vertikal (warna biru)
                sudut_garis_vertikal = math.pi / 2

                # Sudut garis triangulasi
                dx_triangulasi = mid_x - center_x
                dy_triangulasi = frame_height - mid_y
                sudut_garis_triangulasi = math.atan2(dy_triangulasi, dx_triangulasi)

                # Sudut triangulasi
                sudut_triangulasi = math.degrees(abs(sudut_garis_vertikal - sudut_garis_triangulasi))
                if dx_triangulasi < 0:
                    sudut_triangulasi = sudut_triangulasi
                else:
                    sudut_triangulasi = -sudut_triangulasi
            
                # Tampilkan sudut triangulasi
                label_triangulasi = f'Sudut Triangulasi: {sudut_triangulasi:.2f} derajat'
                cv2.putText(img, label_triangulasi, (10, 20), 0, 0.5, [0, 0, 255], thickness=1, lineType=cv2.LINE_AA)

                # Sudut Bearing
                dx1_bearing = center_x - x1_tengah
                dy1_bearing = frame_height - y1_tengah
                dx2_bearing = center_x - x2_tengah
                dy2_bearing = frame_height - y2_tengah
                sudut_bola_pertama = math.atan2(dy1_bearing, dx1_bearing)
                sudut_bola_kedua = math.atan2(dy2_bearing, dx2_bearing)
                degree_bola_pertama = math.degrees(sudut_bola_pertama)
                degree_bola_kedua = math.degrees(sudut_bola_kedua)
                sudut_bearing = math.degrees(abs(sudut_bola_pertama - sudut_bola_kedua))

                # Tampilkan sudut bearing
                label_bearing = f"Sudut Bola Pertama: {abs(90 - degree_bola_pertama):.2f}, Sudut Bola Kedua: {abs(90 - degree_bola_kedua):.2f}, Sudut Bearing: {sudut_bearing:.2f}"
                cv2.putText(img, label_bearing, (10, 100), 0, 0.5, [75, 75, 75], thickness=1, lineType=cv2.LINE_AA)

#Fungsi untuk menyimpan data hasil webcam dan upload ke Firebase
def save_and_upload_image(img, filename, folder_path, bucket):
    # Save image
    filepath = os.path.join(folder_path, filename)
    cv2.imwrite(filepath, img)
    print(f"Image saved as {filepath}")

    # Upload image to Firebase
    blob = bucket.blob(f"GreenBox/{filename}")
    blob.upload_from_filename(filepath)
    print(f"Image uploaded to Firebase as {filename}")

# Fungsi untuk menangani pemrosesan image pada thread yang terpisah
def image_processing_thread():
    while True:
        img, filename, folder_path, bucket = image_queue.get()
        if img is None:  # Stop thread saat sentinel diterima
            break
        save_and_upload_image(img, filename, folder_path, bucket)
        image_queue.task_done()

#Memulai pemrosesan thraed untuk image
thread = threading.Thread(target=image_processing_thread, daemon=True)
thread.start()


def detect_box():
    global state, image_saved
    cap_kotak = cv2.VideoCapture(0) ##CAP_MSMF
    while True:
        success_kotak, img_kotak = cap_kotak.read()
        # if not success_kotak:
            # break

        # Apply manual brightness adjustment to darken the frame
        img_kotak = cv2.convertScaleAbs(img_kotak, beta=brightness_value)

        # Run YOLO detection
        results_kotak = model_kotak(img_kotak, stream=True)

        high_conf_detected = False  # New flag to check if any detection was above 0.9
        

        #Saat kita mendapatkan Results, kita dapat mengecek untuk tiap Bounding Boxes dan melihat bagaimana performanya
        #Sekali mendapatkan Results, kita akan mengulang terus pada jendela dan kita akan memiliki bounding box untuk tiap Result-nya
        #Melakukan loop untuk tiap Bounding Box
        for r in results_kotak:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # Get class ID and confidence score
                cls = int(box.cls[0])
                conf = math.ceil((box.conf[0] * 100)) / 100
                print(f"Detected class ID: {cls}, Confidence: {conf}")

                # Process only if confidence is at least 0.6
                if cls == 0 and conf >= 0.6:  # Detection threshold
                    # Draw bounding box and label
                    cv2.rectangle(img_kotak, (x1, y1), (x2, y2), (255, 0, 255), 3)
                    label = f'kotak {conf}'
                    t_size = cv2.getTextSize(label, 0, fontScale=1, thickness=2)[0]
                    c2 = x1 + t_size[0], y1 - t_size[1] - 3
                    cv2.rectangle(img_kotak, (x1, y1), c2, (255, 0, 255), -1, cv2.LINE_AA)
                    cv2.putText(img_kotak, label, (x1, y1 - 2), 0, 1, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)

                    # Save and upload only if confidence is at least 0.85, and no other image has been saved yet
                    if conf >= 0.5 and not image_saved:
                        timestamp = time.strftime("%Y-%m-%d-%H.%M.%S")
                        filename = f'greenBox_{timestamp}.jpg'

                        # Add image to queue for processing
                        image_queue.put((img_kotak.copy(), filename, folder_path, storage.bucket()))
                        
                        # Set the flag to avoid repeated uploads
                        image_saved = True
                        state = 2

                    # Update the flag if high confidence detection was found
                    if conf >= 0.5:
                        high_conf_detected = True

        # Reset image_saved if no high confidence detection in this frame
        if not high_conf_detected:
            image_saved = False

        # Show the frame
        cv2.imshow("Capture Image", img_kotak)

        # Exit on pressing '1'
        if cv2.waitKey(1) & 0xFF == ord('1') or state == 2:
            cap_kotak.release()
            break


#Perulangan untuk jendela pendeteksian buoy
last_detection_time = time.time()
def detect_buoys():
#Menampilkan jendela dari hasil kamera
    cap = cv2.VideoCapture(0) ##cv2 meng-capture video (Nomor Webcam, Eksekusi pembukaan)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,1024) ##mengatur agar lebar jendela 1024
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,576) ##mengatur agar tinggi jendela 576
# cap_kotak = cv2.VideoCapture(1, cv2.CAP_MSMF) ##CAP_MSMF

#Pengaturan dimensi jendela
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) ##variabel untuk mendapatkan resolusi lebar frame
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) ##variabel untuk mendapatkan resolusi tinggi frame

#Definisikam variabel untuk keperluan image editing
    y_tengah_window = int(frame_height * 0.65)
    center_x = frame_width // 2
    center_x_one_buoy = center_x // 2
##Membuat Video (VideoWriter) dengan keterangan
###Type output : avi
###Codev video : MJPG
###Framerate : 10 fps
###Resolusi : frame_width x frame_height
    timestamp = time.strftime("%Y-%m-%d-%H.%M.%S") ##waktu yang disimpan untuk video
    out = cv2.VideoWriter(f'output_{timestamp}.avi',cv2.VideoWriter_fourcc('M','J','P','G'),10,(frame_width,frame_height))
# out = cv2.VideoWriter('output.avi',cv2.VideoWriter_fourcc('M','J','P','G'),10,(frame_width,frame_height)) 
    global last_detection_time, state
    while True:
        #Membaca frame dari kamera
        success, img = cap.read()
        #Pendeteksian menggunakan YOLOv10 frame demi frame
        results = model(img,stream = True)
        buoy_centers = []
        warna_koordinat_bola = []
        buoy_nums = []


        for result in results:
            boxes = result.boxes
            buoy_nums = [int(box.cls) for box in boxes]
            for box in boxes:
                x1,y1,x2,y2 = box.xyxy[0]
                x1,y1,x2,y2 = int(x1), int(y1), int(x2), int(y2)
                tengah_x = (x1 + x2) // 2
                tengah_y = (y1 + y2) // 2

                cls = int(box.cls[0])

                buoy_centers.append((cls,tengah_x,tengah_y))
                kepercayaan = math.ceil((box.conf[0]*100))/100

                #Definisikan sebuah list warna untuk tiap Class yang mewakili object
                warna = [(0, 255, 0), (0, 0, 255)]

                #Menggambarkan Bounding Box dengan warna yang sesuai
                # cv2.rectangle(img, (sorted_buoy_by_x[0],sorted_buoy_by_y[0]), (sorted_buoy_by_x[1],sorted_buoy_by_y[1]), warna[cls], 3)
                

                nama_class = namaClass[cls]
                label = f'{nama_class}{kepercayaan}'

                ukuran_teks_gambar = cv2.getTextSize(label, 0, fontScale=1,thickness=2)[0]
                c2 = x1 + ukuran_teks_gambar[0], y1 - ukuran_teks_gambar[1] - 3
                cv2.rectangle(img, (x1,y1), c2, warna[cls], -1, cv2.LINE_AA) #terisi
                cv2.putText(img, label, (x1,y1-2), 0, 1, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)        
            
        # Jika kita mendeteksi dua bola

        if  len(buoy_nums) != 0:
            cur_detection_time = time.time()
            last_detection_time = time.time()
            if len(buoy_nums) >= 2 and np.bitwise_or.reduce(buoy_nums) == 1 :
                buoy_centers.sort(key=lambda pos: (pos[0], abs(pos[1] - center_x), -pos[2]))  # Urutkan berdasarkan x
                print("titik_tengah_bola: " + str(buoy_centers))  
                detect_buoy(buoy_centers, 2, img, cap)

            elif len(buoy_nums) == 1:
                detect_buoy(buoy_centers, 1, img, cap)
        else:
            cur_detection_time = time.time()
            if time.time() - last_detection_time > 2:
                last_detection_time = cur_detection_time
                detect_buoy(buoy_centers, 0, img, cap)

        # #Garis Vertikal pada window (warna biru)
        cv2.line(img, (center_x, 0), (center_x, frame_height), (255,0,0), 2)
        cv2.line(img, (0, y_tengah_window), (frame_width, y_tengah_window), (255,0,255), 2)

        
        #Menutup window
        out.write(img)
        cv2.imshow("Image", img)



        # Exit on pressing '1'
        if cv2.waitKey(1) & 0xFF == ord('1') or state==1:
            cap.release()
            out.release()
            break



if __name__ == '__main__':

    if state == 0:
        print(state)
        detect_buoys()
        # detect_box()
    if state == 1:
        print(state)
        cv2.destroyAllWindows()
        detect_box()
    if state == 2:
        print(state)
        cv2.destroyAllWindows()

    #Men-destroy window
    kirim_data = False #Memberhentikan Thread
    cv2.destroyAllWindows()
    # mikrokontroler.close()

    # At the end of the program, stop the thread
    image_queue.put((None, None, None, None))  # Send sentinel to stop thread
    thread.join()  # Wait for thread to finish

