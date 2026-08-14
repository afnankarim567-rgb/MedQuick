"""
merge_medicines.py

Merges three medicine JSON files into one: merged_medicine.json

This version keeps ONLY 5 fields for every medicine in the output:
    brand_name, generic_name, dosage_type, strength, manufacturer

Logic:
  1. From dgda_unique_medicines.json -> take these 5 fields for every record.
  2. From medicine.json and medicine_prices.json -> take these 5 fields too,
     but only ADD a medicine if that same (brand_name, generic_name,
     dosage_type, strength, manufacturer) combination is not already present
     (comparison is case-insensitive, whitespace-trimmed, since the 3 files
     use slightly different key names for the same fields).
"""

import json
import os

# ---------------------------------------------------------------------------
# 1. CONFIG - GitHub Actions & Local Desktop dynamic path support
# ---------------------------------------------------------------------------
# GitHub-এ চললে কারেন্ট ডিরেক্টরি নিবে, লোকালি আপনার পিসির পাথ নিবে
DEFAULT_DIR = r"C:\Users\Msi\OneDrive\Desktop\MedQuick apps"
BASE_DIR = os.getenv("BASE_DIR", DEFAULT_DIR if os.path.exists(DEFAULT_DIR) else ".")

DGDA_FILE = os.path.join(BASE_DIR, "dgda_unique_medicines.json")
MEDICINE_FILE = os.path.join(BASE_DIR, "medicine.json")
PRICES_FILE = os.path.join(BASE_DIR, "medicine_prices.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "merged_medicine.json")


# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------
def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_field(record, candidate_keys):
    """Return the first matching key's value from a record, trying several
    possible spellings of the same field (files use different key names)."""
    for key in candidate_keys:
        if key in record and record[key] is not None:
            return str(record[key]).strip()
    return ""


def normalize(value):
    return value.strip().lower()


def extract_5_fields(record):
    """Pull out brand_name, generic_name, dosage_type, strength, manufacturer
    from a record, no matter which of the 3 source files it came from."""
    brand = get_field(record, ["brand_name", "brand name", "brandName", "brand"])
    generic = get_field(record, ["generic_name", "generic name", "genericName", "generic"])
    dosage = get_field(
        record,
        [
            "dosage_type", "dosage type", "dosageType",
            "dosage_form", "dosage form", "dosageForm",
        ],
    )
    strength = get_field(record, ["strength", "strength_name"])
    manufacturer = get_field(record, ["manufacturer", "manufacturer_name", "manufacturerName"])
    return {
        "brand_name": brand,
        "generic_name": generic,
        "dosage_type": dosage,
        "strength": strength,
        "manufacturer": manufacturer,
    }


def make_key(fields_dict):
    """Build the signature used to detect duplicate medicines."""
    return (
        normalize(fields_dict["brand_name"]),
        normalize(fields_dict["generic_name"]),
        normalize(fields_dict["dosage_type"]),
        normalize(fields_dict["strength"]),
        normalize(fields_dict["manufacturer"]),
    )


# ---------------------------------------------------------------------------
# 3. Load files
# ---------------------------------------------------------------------------
dgda_records = load_json(DGDA_FILE)
medicine_records = load_json(MEDICINE_FILE)
price_records = load_json(PRICES_FILE)

print(f"dgda_unique_medicines.json : {len(dgda_records)} records")
print(f"medicine.json              : {len(medicine_records)} records")
print(f"medicine_prices.json       : {len(price_records)} records")

# ---------------------------------------------------------------------------
# 4. Build merged list, each entry reduced to the 5 target fields
# ---------------------------------------------------------------------------
merged = []
seen_keys = set()

for rec in dgda_records:
    fields = extract_5_fields(rec)
    key = make_key(fields)
    if key not in seen_keys:
        merged.append(fields)
        seen_keys.add(key)

added_from_medicine = 0
added_from_prices = 0

for rec in medicine_records:
    fields = extract_5_fields(rec)
    key = make_key(fields)
    if key not in seen_keys:
        merged.append(fields)
        seen_keys.add(key)
        added_from_medicine += 1

for rec in price_records:
    fields = extract_5_fields(rec)
    key = make_key(fields)
    if key not in seen_keys:
        merged.append(fields)
        seen_keys.add(key)
        added_from_prices += 1

print(f"\nNew medicines added from medicine.json       : {added_from_medicine}")
print(f"New medicines added from medicine_prices.json : {added_from_prices}")
print(f"Total merged records                          : {len(merged)}")

# ---------------------------------------------------------------------------
# 5. Save
# ---------------------------------------------------------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print(f"\nSaved -> {OUTPUT_FILE}")