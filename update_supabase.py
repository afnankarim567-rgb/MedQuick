import os
import json
import gzip
import requests

# ---------------------------------------------------------
# Supabase Configuration
# ---------------------------------------------------------
# Local Testing-এর জন্য যদি Environment Variable না থাকে,
# তবে সরাসরি আপনার Key এবং URL এখানে কাজ করবে।
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vpvfkpbxwvwowpnemelf.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "sb_secret_0Zk5Tq00qVMtcbAFEiM-6A_hAIJRmWz")
BUCKET_NAME = "medicine-data"

headers = {
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "apikey": SUPABASE_SERVICE_KEY
}

def upload_to_supabase(file_path, destination_path, content_type):
    """Supabase Storage-এ ফাইল আপলোড / ওভাররাইট করার ফাংশন"""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{destination_path}"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} file not found!")
        return

    with open(file_path, "rb") as f:
        file_data = f.read()

    upload_headers = {
        **headers,
        "Content-Type": content_type,
        "x-upsert": "true"  # আগের ফাইল থাকলে ওভাররাইট করবে
    }

    response = requests.post(url, headers=upload_headers, data=file_data)
    if response.status_code in [200, 201]:
        print(f"✅ Successfully uploaded: {destination_path}")
    else:
        print(f"❌ Failed to upload {destination_path}: {response.text}")

def main():
    # ১. ফাইল নেম হ্যান্ডলিং (merged_medicine.json অথবা merged_medicine)
    json_file = None
    if os.path.exists('merged_medicine.json'):
        json_file = 'merged_medicine.json'
    elif os.path.exists('merged_medicine'):
        json_file = 'merged_medicine'
    else:
        print("❌ Error: merged_medicine.json file not found in current directory!")
        return

    # ২. Gzip Compression
    print(f"Compressing {json_file} -> merged_medicine.json.gz ...")
    with open(json_file, 'rb') as f_in:
        with gzip.open('merged_medicine.json.gz', 'wb') as f_out:
            f_out.writelines(f_in)

    # ৩. Supabase থেকে বর্তমান Version চেক করে ১ বাড়ানো
    version = 1
    version_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/version.json"
    try:
        res = requests.get(version_url)
        if res.status_code == 200:
            current_ver = res.json().get("version", 0)
            version = current_ver + 1
    except Exception as e:
        print(f"⚠️ Could not fetch previous version, defaulting to 1: {e}")

    # version.json ফাইল লোকালি রাইট করা
    with open("version.json", "w") as f:
        json.dump({"version": version}, f)

    print(f"📌 New Version set to: {version}")

    # ৪. Supabase-এ আপলোড
    print("Uploading files to Supabase Storage...")
    upload_to_supabase("merged_medicine.json.gz", "merged_medicine.json.gz", "application/gzip")
    upload_to_supabase("version.json", "version.json", "application/json")
    print("🎉 All tasks completed successfully!")

if __name__ == "__main__":
    main()