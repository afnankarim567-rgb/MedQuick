import requests
import json
import time
import string

URL = "https://www.dgdagov.info/administrator/components/com_jcode/source/serverProcessing.php"

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://www.dgdagov.info",
    "Referer": "https://www.dgdagov.info/index.php/search-price",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

COOKIES = {
    "64b89d05a4a7cf540e8cd068c2904eaf":
        "157aab5d1d0e84e90c4eae7d6c28270f"
}


def clean(value):
    if value is None:
        return ""

    return " ".join(str(value).split()).strip()


def normalize(value):
    return clean(value).casefold()


def get_page(search_term, start, length=1000):

    data = {
        "sEcho": str((start // length) + 1),

        "iColumns": "10",
        "sColumns": "",
        "iDisplayStart": str(start),
        "iDisplayLength": str(length),

        "mDataProp_0": "0",
        "mDataProp_1": "1",
        "mDataProp_2": "2",
        "mDataProp_3": "3",
        "mDataProp_4": "4",
        "mDataProp_5": "5",
        "mDataProp_6": "6",
        "mDataProp_7": "7",
        "mDataProp_8": "8",
        "mDataProp_9": "9",

        "iSortCol_0": "1",
        "sSortDir_0": "asc",
        "iSortingCols": "1",

        "bSortable_0": "false",
        "bSortable_1": "true",
        "bSortable_2": "true",
        "bSortable_3": "true",
        "bSortable_4": "false",
        "bSortable_5": "true",
        "bSortable_6": "true",
        "bSortable_7": "true",
        "bSortable_8": "true",
        "bSortable_9": "false",

        "action": "getDrugCompanyDatabaseSearchPriceData",

        # DGDA search
        "FilterAll": "4",
        "FilterItem": search_term
    }

    response = requests.post(
        URL,
        headers=HEADERS,
        cookies=COOKIES,
        data=data,
        timeout=60
    )

    response.raise_for_status()

    return response.json()


def process_row(row, seen, medicines):

    if not isinstance(row, list):
        return

    if len(row) < 10:
        return

    # DGDA columns:
    #
    # 0 = SL
    # 1 = Generic Name
    # 2 = Strength
    # 3 = Pack Size
    # 4 = Retail Price
    # 5 = Manufacturer
    # 6 = Brand Name
    # 7 = Dosages Description
    # 8 = Use For
    # 9 = DAR

    generic = clean(row[1])
    strength = clean(row[2])
    price = clean(row[4])
    manufacturer = clean(row[5])
    brand = clean(row[6])
    dosage = clean(row[7])

    # --------------------------------------------
    # YOUR UNIQUE MEDICINE RULE
    # --------------------------------------------

    unique_key = (
        normalize(brand),
        normalize(generic),
        normalize(strength),
        normalize(dosage),
        normalize(manufacturer),
        normalize(price)
    )

    if unique_key in seen:
        return

    seen.add(unique_key)

    medicines.append({
        "brand_name": brand,
        "generic_name": generic,
        "strength": strength,
        "dosage_type": dosage,
        "manufacturer": manufacturer,
        "price": price
    })


def main():

    medicines = []
    seen = set()

    # Search terms
    search_terms = list(string.ascii_lowercase)
    search_terms += list(string.digits)

    print("=" * 65)
    print("DGDA COMPLETE MEDICINE SCRAPER")
    print("=" * 65)
    print(f"Search batches: {len(search_terms)}")
    print()

    for batch_number, term in enumerate(search_terms, start=1):

        print()
        print("-" * 65)
        print(
            f"[{batch_number}/{len(search_terms)}] "
            f"Searching: {term}"
        )
        print("-" * 65)

        start = 0
        page_size = 1000
        total_records = None

        while True:

            print(
                f"Downloading {term}: "
                f"{start} - {start + page_size}"
            )

            try:

                result = get_page(
                    term,
                    start,
                    page_size
                )

            except Exception as e:

                print("Request error:", e)

                # Retry once
                time.sleep(2)

                try:
                    result = get_page(
                        term,
                        start,
                        page_size
                    )

                except Exception as e2:

                    print(
                        "Retry failed:",
                        e2
                    )

                    break

            rows = result.get("aaData", [])

            if total_records is None:

                total_records = result.get(
                    "iTotalDisplayRecords",
                    result.get("iTotalRecords", 0)
                )

                try:
                    total_records = int(total_records)
                except:
                    total_records = 0

                print(
                    f"DGDA records for '{term}': "
                    f"{total_records}"
                )

            if not rows:
                break

            before = len(medicines)

            for row in rows:
                process_row(
                    row,
                    seen,
                    medicines
                )

            added = len(medicines) - before

            print(
                f"Received: {len(rows)} | "
                f"New unique: {added} | "
                f"Total unique: {len(medicines)}"
            )

            # All records downloaded
            if total_records > 0:

                if start + len(rows) >= total_records:
                    break

            # Last page
            if len(rows) < page_size:
                break

            start += page_size

            time.sleep(0.4)

        # Small delay between search batches
        time.sleep(0.8)

    # ------------------------------------------------
    # SAVE JSON
    # ------------------------------------------------

    output_file = "dgda_unique_medicines.json"

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            medicines,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("=" * 65)
    print("SCRAPING COMPLETED")
    print("=" * 65)
    print(
        f"TOTAL UNIQUE MEDICINES: {len(medicines)}"
    )
    print(
        f"JSON FILE: {output_file}"
    )
    print("=" * 65)


if __name__ == "__main__":
    main()