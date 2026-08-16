import json

DISTRICTS_FILE = "knowledge-base/master/districts.json"
DISCOMS_FILE = "knowledge-base/master/discoms.json"
OUTPUT_FILE = "knowledge-base/master/district_discoms.json"

with open(DISTRICTS_FILE, encoding="utf-8") as f:
    districts = json.load(f)

with open(DISCOMS_FILE, encoding="utf-8") as f:
    discoms = json.load(f)

# State -> DISCOM mapping
# J&K is handled separately because it has two DISCOMs.
state_discom = {
    "HP": "HP_HPSEBL",
    "HR": "HR_UHBVN_DHBVN",
    "PB": "PB_PSPCL",
    "UK": "UK_UPCL",
}

# UP district -> DISCOM
up_discom = {
    "Agra": "UP_DVVNL",
    "Aligarh": "UP_DVVNL",
    "Etah": "UP_DVVNL",
    "Firozabad": "UP_DVVNL",
    "Hathras": "UP_DVVNL",
    "Mainpuri": "UP_DVVNL",
    "Mathura": "UP_DVVNL",
    "Budaun": "UP_MVVNL",
    "Bareilly": "UP_MVVNL",
    "Auraiya": "UP_DVVNL",
    "Bhadohi": "UP_PUVVNL",
    "Kasganj": "UP_DVVNL",
    "Pilibhit": "UP_MVVNL",
    "Shahjahanpur": "UP_MVVNL",
    "Etawah": "UP_MVVNL",
    "Farrukhabad": "UP_MVVNL",
    "Kannauj": "UP_MVVNL",
    "Kanpur Dehat": "UP_MVVNL",
    "Kanpur Nagar": "UP_KESCO",
    "Lakhimpur Kheri": "UP_MVVNL",
    "Lucknow": "UP_MVVNL",
    "Hardoi": "UP_MVVNL",
    "Sitapur": "UP_MVVNL",
    "Unnao": "UP_MVVNL",
    "Gautam Buddha Nagar": "UP_PVVNL",
    "Ghaziabad": "UP_PVVNL",
    "Hapur": "UP_PVVNL",
    "Meerut": "UP_PVVNL",
    "Bulandshahr": "UP_PVVNL",
    "Baghpat": "UP_PVVNL",
    "Muzaffarnagar": "UP_PVVNL",
    "Saharanpur": "UP_PVVNL",
    "Shamli": "UP_PVVNL",
    "Bijnor": "UP_PVVNL",
    "Moradabad": "UP_PVVNL",
    "Rampur": "UP_PVVNL",
    "Amroha": "UP_PVVNL",
    "Sambhal": "UP_PVVNL",
    "Banda": "UP_PUVVNL",
    "Chitrakoot": "UP_PUVVNL",
    "Fatehpur": "UP_PUVVNL",
    "Hamirpur": "UP_PUVVNL",
    "Jalaun": "UP_PUVVNL",
    "Jhansi": "UP_PUVVNL",
    "Lalitpur": "UP_PUVVNL",
    "Mahoba": "UP_PUVVNL",
    "Prayagraj": "UP_PUVVNL",
    "Kaushambi": "UP_PUVVNL",
    "Pratapgarh": "UP_PUVVNL",
    "Varanasi": "UP_PUVVNL",
    "Chandauli": "UP_PUVVNL",
    "Ghazipur": "UP_PUVVNL",
    "Jaunpur": "UP_PUVVNL",
    "Mirzapur": "UP_PUVVNL",
    "Sonbhadra": "UP_PUVVNL",
    "Mau": "UP_PUVVNL",
    "Ballia": "UP_PUVVNL",
    "Azamgarh": "UP_PUVVNL",
    "Gorakhpur": "UP_PUVVNL",
    "Deoria": "UP_PUVVNL",
    "Kushinagar": "UP_PUVVNL",
    "Maharajganj": "UP_PUVVNL",
    "Gonda": "UP_PUVVNL",
    "Balrampur": "UP_PUVVNL",
    "Bahraich": "UP_PUVVNL",
    "Shravasti": "UP_PUVVNL",
    "Siddharthnagar": "UP_PUVVNL",
    "Basti": "UP_PUVVNL",
    "Sant Kabir Nagar": "UP_PUVVNL",
    "Ayodhya": "UP_PUVVNL",
    "Ambedkar Nagar": "UP_PUVVNL",
    "Sultanpur": "UP_PUVVNL",
    "Amethi": "UP_PUVVNL",
    "Barabanki": "UP_PUVVNL",
    "Rae Bareli": "UP_PUVVNL",
    "Raebareli": "UP_PUVVNL",
}

# J&K district -> DISCOM
# Jammu division -> JPDCL
# Kashmir division -> KPDCL
jk_jpdcl = {
    "Jammu", "Kathua", "Samba", "Udhampur", "Reasi",
    "Doda", "Kishtwar", "Ramban", "Poonch", "Rajouri"
}

jk_kpdcl = {
    "Anantnag", "Bandipora", "Baramulla", "Budgam", "Ganderbal",
    "Kulgam", "Kupwara", "Pulwama", "Shopian", "Srinagar"
}

output = []

for district in districts:
    state_id = district["state_id"]
    district_name = district["district_name"]

    discom_id = None

    if state_id in state_discom:
        discom_id = state_discom[state_id]

    elif state_id == "JK":
        if district_name in jk_jpdcl:
            discom_id = "JK_JPDCL"
        elif district_name in jk_kpdcl:
            discom_id = "JK_KPDCL"

    elif state_id == "UP":
        discom_id = up_discom.get(district_name)

    record = {
        "district_id": district["district_id"],
        "district_name": district["district_name"],
        "state_id": state_id,
        "discom_id": discom_id
    }

    output.append(record)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
    f.write("\n")

missing = [x for x in output if not x["discom_id"]]

print("Total districts:", len(output))
print("Mapped:", len(output) - len(missing))
print("Missing:", len(missing))

if missing:
    print("\nStill missing:")
    for x in missing:
        print(
            x["district_id"],
            "|",
            x["district_name"],
            "|",
            x["state_id"]
        )
else:
    print("\nSUCCESS: All districts mapped to DISCOM.")
