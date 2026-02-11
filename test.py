import os
import base64
import requests
import cv2
import pandas as pd
from datetime import datetime
from urllib.parse import unquote
from dotenv import load_dotenv
import certifi

# ================= LOAD ENV =================
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# ================= CONFIG =================

FORMS_LOCAL_PATH = r"C:\Users\mgalang_g.i\OneDrive - Bank Indonesia\Apps\Microsoft Forms\Dokumentasi Foto Perkerjaan Mingguan (Copy)"
EXCEL_FILE = r"C:\Users\mgalang_g.i\OneDrive - Bank Indonesia\Progres Mingguan - Dokumentasi Foto.xlsx"  # <-- your forms export
OUTPUT_FOLDER = "compressed"
GITHUB_FOLDER = "weekly_photos"

FOTO_FOLDER_MAP = {
    "Foto Satu": "Foto Pertama",
    "Foto Dua": "Foto Kedua",
    "Foto Tiga": "Foto Ketiga",
    "Foto Empat": "Foto Keempat",
    "Foto Lima": "Foto Kelima",
    "Foto Enam": "Foto Keenam",
    "Foto Tujuh": "Foto Ketujuh",
    "Foto Delapan": "Foto Kedelapan"
}


MAX_WIDTH = 1024
QUALITY = 65

EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ================= FUNCTIONS =================

def compress_image(input_path, output_path):
    img = cv2.imread(input_path)
    if img is None:
        print("❌ Cannot read:", input_path)
        return False, None

    h, w = img.shape[:2]
    scale = MAX_WIDTH / max(w, h)
    if scale < 1:
        img = cv2.resize(img, (int(w*scale), int(h*scale)))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])

    size_kb = os.path.getsize(output_path) / 1024
    return True, round(size_kb, 2)


def upload_to_github(github_path, local_filepath):
    with open(local_filepath, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FOLDER}/{github_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # Check if file exists (overwrite mode)
    check = requests.get(url, headers=headers, verify=False)
    print(check.status_code)
    sha = check.json().get("sha") if check.status_code == 200 else None

    data = {
        "message": f"Upload {github_path}",
        "content": content,
        "branch": "main"
    }

    if sha:
        data["sha"] = sha  # overwrite

    r = requests.put(
    url,
    headers=headers,
    json=data,
    verify=False
)
    if r.status_code not in [200, 201]:
        print(f"❌ Upload failed {github_path}: {r.status_code} - {r.text}")
        return None

    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GITHUB_FOLDER}/{github_path}"


# ================= MAIN PIPELINE =================

df = pd.read_excel(EXCEL_FILE)

foto_cols = [
    ("Foto Satu", "Kegiatan pada foto satu"),
    ("Foto Dua", "Kegiatan pada foto dua"),
    ("Foto Tiga", "Kegiatan pada foto tiga"),
    ("Foto Empat", "Kegiatan pada foto empat"),
    ("Foto Lima", "Kegiatan pada foto lima"),
    ("Foto Enam", "Kegiatan pada foto enam"),
    ("Foto Tujuh", "Kegiatan pada foto tujuh"),
    ("Foto Delapan", "Kegiatan pada foto delapan"),
]

records = []

for _, row in df.iterrows():
    kode_proyek = str(row["Kode proyek ..."]).replace(" ", "_")
    minggu = str(row["Minggu yang dilaporkan ..."]).replace(" ", "_")

    for foto_col, desc_col in foto_cols:
        url = row.get(foto_col)
        desc = row.get(desc_col, "")

        if pd.isna(url):
            continue

        filename = os.path.basename(unquote(url))
        clean_filename = filename.replace(" ", "_")

        # Identify folder name in OneDrive
        # folder_name = foto_col.replace("Foto ", "Foto ").strip()
        # local_folder = os.path.join(FORMS_LOCAL_PATH, folder_name)

        folder_name = FOTO_FOLDER_MAP.get(foto_col)
        if not folder_name:
            print("❌ Unknown foto column:", foto_col)
            continue

        local_folder = os.path.join(FORMS_LOCAL_PATH, folder_name)


        # Find file locally
        local_file = os.path.join(local_folder, filename)
        if not os.path.exists(local_file):
            # try fuzzy match
            base = filename.split(".")[0]
            for f in os.listdir(local_folder):
                if base in f:
                    local_file = os.path.join(local_folder, f)
                    print("⚠️ Matched similar file:", f)
                    break

        if not os.path.exists(local_file):
            print("❌ File not found:", local_file)
            continue

        # Build GitHub hierarchy
        github_path = f"{kode_proyek}/{minggu}/{clean_filename}"
        output_path = os.path.join(OUTPUT_FOLDER, kode_proyek, minggu, clean_filename)

        print(f"Processing: {github_path}")

        ok, size_kb = compress_image(local_file, output_path)
        if not ok:
            continue

        raw_url = upload_to_github(github_path, output_path)
        if not raw_url:
            continue

        # Save metadata
        records.append({
            "kode_proyek": kode_proyek,
            "minggu": minggu,
            "link_foto": raw_url,
            "deskripsi_foto": desc,
            "nama_file": clean_filename,
            "size_gambar_kb": size_kb
        })

# Save Excel metadata for PowerBI
meta_df = pd.DataFrame(records)
meta_df.to_excel("foto_metadata.xlsx", index=False)
print("✅ Metadata saved to foto_metadata.xlsx")
