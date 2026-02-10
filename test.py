import os
import base64
import requests
import cv2
from datetime import datetime
from dotenv import load_dotenv

# Load env
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# CONFIG
FORMS_LOCAL_PATH = "C:/Users/mgalang_g.i/OneDrive - Bank Indonesia/Apps/Microsoft Forms/Dokumentasi Foto Perkerjaan Mingguan"
OUTPUT_FOLDER = "compressed"
GITHUB_FOLDER = "weekly_photos"

MAX_WIDTH = 1024
QUALITY = 65

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ================= FUNCTIONS =================

def compress_image(input_path, output_path):
    img = cv2.imread(input_path)
    if img is None:
        print("❌ Cannot read:", input_path)
        return False

    h, w = img.shape[:2]
    scale = MAX_WIDTH / max(w, h)
    if scale < 1:
        img = cv2.resize(img, (int(w*scale), int(h*scale)))

    # Pastikan folder output lokal tersedia sebelum save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])
    return True


def upload_to_github(github_path, local_filepath):
    with open(local_filepath, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    # github_path sekarang sudah termasuk struktur folder: UNIT/YEAR/WEEK/file.jpg
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FOLDER}/{github_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    data = {
        "message": f"Upload {github_path}",
        "content": content
    }

    r = requests.put(url, headers=headers, json=data)
    
    if r.status_code in [200, 201]:
        print(f"✅ Berhasil Upload ke: {github_path}")
    else:
        print(f"❌ Gagal Upload {github_path}: {r.status_code} - {r.text}")
        return None

    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GITHUB_FOLDER}/{github_path}"


# ================= MAIN =================

for root, dirs, files in os.walk(FORMS_LOCAL_PATH):
    for file in files:
        if file.lower().endswith((".jpg", ".jpeg", ".png")):
            full_path = os.path.join(root, file)
            
            # 1. Ambil Nama Unit (Folder asal)
            unit_name = os.path.basename(root).replace(" ", "_")
            
            # 2. Ambil Waktu Modifikasi File untuk Tahun & Minggu
            mtime = os.path.getmtime(full_path)
            date_obj = datetime.fromtimestamp(mtime)
            year = date_obj.strftime("%Y")
            week = "W" + date_obj.strftime("%V") # %V adalah standar ISO week number
            
            # 3. Susun Path untuk GitHub
            # Format: UNIT/YEAR/WEEK/filename
            clean_filename = file.replace(" ", "_")
            github_path = f"{unit_name}/{year}/{week}/{clean_filename}"
            
            # 4. Tentukan Path Lokal Sementara untuk hasil kompresi
            output_path = os.path.join(OUTPUT_FOLDER, unit_name, year, week, clean_filename)

            print(f"Processing: {github_path}")
            if compress_image(full_path, output_path):
                raw_url = upload_to_github(github_path, output_path)
                if raw_url:
                    print("RAW URL:", raw_url)