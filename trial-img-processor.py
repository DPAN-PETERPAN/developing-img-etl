import os
import base64
import requests
import cv2
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
        return

    h, w = img.shape[:2]
    scale = MAX_WIDTH / max(w, h)
    if scale < 1:
        img = cv2.resize(img, (int(w*scale), int(h*scale)))

    cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])


def upload_to_github(filename, filepath):
    with open(filepath, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FOLDER}/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    data = {
        "message": f"Upload {filename}",
        "content": content
    }

    r = requests.put(url, headers=headers, json=data)
    print("GitHub:", r.status_code)

    r.raise_for_status()
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GITHUB_FOLDER}/{filename}"


# ================= MAIN =================

for root, dirs, files in os.walk(FORMS_LOCAL_PATH):
    for file in files:
        if file.lower().endswith((".jpg", ".jpeg", ".png")):
            full_path = os.path.join(root, file)

            folder_name = os.path.basename(root)
            new_name = f"{folder_name}_{file}".replace(" ", "_")
            output_path = os.path.join(OUTPUT_FOLDER, new_name)

            print("Compressing:", new_name)
            compress_image(full_path, output_path)

            print("Uploading:", new_name)
            raw_url = upload_to_github(new_name, output_path)

            print("RAW URL:", raw_url)
