"""Readable labels for code tables published in NARA's SITRA technical guide."""

from __future__ import annotations


CODE_VALUES: dict[str, dict[str, str]] = {
    "DATAT": {
        "S": "Small action", "L": "Large operation", "E": "Enemy-initiated incident",
        "W": "Statistical summary",
    },
    "CORP": {str(i): f"South Vietnam Corps Area {i}" for i in range(1, 5)},
    "PART": {
        "1": "US forces", "2": "Third-country forces", "3": "South Vietnamese forces",
        "4": "Enemy forces", "5": "Out-country operations",
    },
    "FNATL": {
        "A": "RVN", "B": "Combined", "C": "Republic of China", "D": "Coast Guard",
        "E": "Enemy", "F": "US combined", "G": "Unspecified", "H": "New Zealand",
        "I": "Vietnamese Navy", "J": "Air Force", "K": "Republic of Korea", "L": "Laos",
        "M": "Marine", "N": "Navy", "O": "Free World", "P": "Philippines",
        "Q": "Viet Nam Air Force", "R": "Vietnamese Marine Corps", "S": "Australia",
        "T": "Thailand", "U": "US military", "V": "Viet Cong", "W": "Army",
        "X": "North Vietnam", "Y": "Popular Forces", "Z": "ANZAC",
        "1": "Regional Force", "2": "Civilian Irregular Defense Group", "3": "Vietnamese Special Forces",
        "4": "Cambodia", "5": "Communist Chinese", "6": "Popular Forces",
        "7": "RVN civilian", "8": "US civilian", "9": "Combat youth",
        "0": "RD personnel", "=": "RVN civilian official", "(": "Hamlet militia",
    },
    "CNTRY": {
        "BM": "Burma", "CB": "Cambodia", "CH": "China", "LA": "Laos",
        "MF": "Malaya Federation", "TH": "Thailand", "VN": "North Vietnam", "VS": "South Vietnam",
    },
    "OPCOD": {
        "AP": "Destroy and apprehend", "AT": "Attack", "CA": "Capture", "CH": "Clear and hold",
        "CL": "Clearing", "CO": "Combat operations", "CS": "Cordon and search", "DE": "Development",
        "DR": "Search and destroy, regular", "FD": "Fix and destroy", "FR": "Reconnaissance in force, pacification",
        "GE": "Large-scale and escort", "LC": "Clear and search", "NB": "Coastal patrol",
        "NC": "Combat support", "ND": "Static defense", "NE": "Convoy security", "NL": "Logistic support",
        "NP": "Province support", "NR": "River patrol", "NS": "Sea patrol", "NT": "Training",
        "NV": "Coastal surveillance", "NY": "Coastal surveillance", "RE": "Large reconnaissance",
        "RF": "Reconnaissance in force", "RQ": "Reconnaissance force search", "RV": "Reserve",
        "SC": "Search and clear", "SD": "Search and destroy", "SE": "Security", "SG": "Securing",
        "SL": "Search and destroy, location", "SP": "Search and destroy, province", "SR": "Search and rescue",
        "SS": "Sea search", "SV": "Surveillance", "SY": "Surveillance", "UA": "Ambush",
        "UC": "Reconnaissance", "UG": "Guard and escort", "UN": "Small-unit operation, no contact",
        "UP": "Patrol", "UR": "Raid", "US": "Search", "UT": "Security", "UU": "Small-unit operation",
        "XX": "Other",
    },
    "PROVINCE": {
        "00": "Unknown", "01": "Quang Tri", "02": "Thua Thien", "03": "Quang Nam", "04": "Quang Tin",
        "05": "Quang Ngai", "06": "Kontum", "07": "Binh Dinh", "08": "Pleiku", "09": "Phu Yen",
        "10": "Darlac", "11": "Khanh Hoa", "12": "Tuyen Duc", "13": "Quang Duc", "14": "Phuoc Long",
        "15": "Lam Dong", "16": "Ninh Thuan", "17": "Binh Thuan", "18": "Binh Tuy", "19": "Long Khanh",
        "20": "Phuoc Thanh", "21": "Binh Long", "22": "Tay Ninh", "23": "Binh Duong", "24": "Gia Dinh",
        "25": "Bien Hoa", "26": "Phuoc Tuy", "27": "Long An", "28": "Kien Tuong", "29": "Kien Phong",
        "30": "Dinh Tuong", "31": "An Giang", "32": "Vinh Long", "33": "Kien Hoa", "34": "Vinh Binh",
        "35": "Phong Dinh", "36": "Kien Giang", "37": "Chuong Thien", "38": "Ba Xuyen", "39": "An Xuyen",
        "40": "Con Son", "41": "Phu Bon", "42": "Hau Nghia", "43": "Go Cong", "44": "Bac Lieu",
        "45": "Trung Phon", "46": "Sa Dec", "47": "Chau Doc", "48": "Haut Chhlong",
        "49": "Phu Quoc Island", "50": "DMZ",
    },
    "FWSZS": {
        "F": "Fire team", "S": "Squad", "P": "Platoon", "C": "Company", "B": "Battalion",
        "R": "Regiment", "G": "Brigade", "D": "Division", "A": "Squadron", "E": "Element",
        "X": "Unit", "Z": "Patrol", "U": "Unknown", "I": "Individual",
    },
    "MVRSP": {"M": "Maneuver", "S": "Support"},
    "RESAC": {"A": "Active", "R": "Reserve"},
    "ICTZ": {str(i): f"South Vietnam Corps Area {i}" for i in range(1, 5)},
    "LSCAT": {
        "0": "Weapons", "1": "Weapons", "2": "Weapons", "3": "Weapons", "4": "Weapons",
        "A": "Ammunition", "M": "Rounds expended", "K": "Miscellaneous",
        "D": "Structures", "C": "Food", "F": "Radios", "G": "Medical supplies",
        "E": "Vehicles", "H": "POL supplies", "I": "Money", "J": "Personnel",
    },
    "LTYPE": {
        "K": "Other", "D": "Killed in action", "E": "Wounded in action", "F": "Missing in action",
        "G": "Individual", "H": "Crew", "I": "Maneuver/chan", "J": "POL",
        "N": "No. battalions", "O": "Combat operations", "P": "Security", "Q": "Training",
        "R": "Reserve", "S": "Replacements/pacification", "T": "Other missions",
    },
}

_FWOPS = CODE_VALUES["OPCOD"]
CODE_VALUES["TYPAT"] = dict(_FWOPS)
CODE_VALUES["OBJEC"] = {
    f"{n:02d}": label for n, label in {
        1: "Guard post", 2: "Command center", 3: "Training center", 4: "Headquarters", 5: "District capital",
        6: "Province capital", 7: "District town", 8: "Market", 9: "School", 10: "Military post",
        11: "Outpost", 12: "Base", 13: "Junk base", 14: "Airfield", 15: "Watchtower", 16: "Blockhouse",
        17: "Military facility", 18: "Camp", 19: "Bivouac", 20: "Hamlet", 21: "Hamlet", 22: "Security fence",
        23: "Hamlet facility", 24: "Hamlet waterways", 29: "Hamlet district personnel", 30: "Hamlet",
        31: "Village", 32: "Village office", 33: "District office", 34: "Province office", 35: "Land development center",
        36: "House", 37: "Building", 38: "Church", 39: "Civilian facility", 40: "Armed helicopter",
        41: "Unarmed helicopter", 42: "Helicopter", 43: "Combat aircraft", 44: "Support aircraft", 45: "Aircraft",
        49: "Landing zone", 50: "Motor convoy", 51: "Truck", 52: "Bus", 53: "Automobile", 54: "Jeep",
        55: "Train", 56: "Cart", 57: "Vehicle", 58: "Armored car", 60: "Sampan", 61: "Junk", 62: "Boat",
        63: "Naval craft", 64: "Ship", 65: "Naval unit", 66: "Marine unit", 70: "Road", 71: "Vehicle bridge",
        72: "Railroad bridge", 73: "Bridge", 74: "Railroad tracks", 75: "Rail facilities", 76: "Communications lines",
        77: "Communications facilities", 78: "Canal", 79: "Waterways", 80: "Village official", 81: "Hamlet official",
        82: "Civilian official", 83: "Civilians", 84: "Inhabitant", 85: "Military unit", 86: "Military personnel",
        87: "Police", 88: "Company or larger unit", 89: "Unit smaller than company", 90: "Firearms/ammunition",
        91: "Foodstuffs", 92: "Livestock", 93: "Medical supplies", 94: "Area", 95: "Construction equipment",
        96: "Power lines", 97: "Culvert", 98: "Tank", 99: "Supplies",
    }.items()
}
CODE_VALUES["OBJDS"] = {
    "10": "On reconnaissance", "11": "On patrol", "12": "On guard duty", "13": "On work party",
    "21": "Reinforce hamlet", "22": "Reinforce unit", "23": "Evacuate casualty", "24": "On escort",
    "50": "Transport supplies", "51": "Transport arms", "52": "Transport troops", "70": "In hamlet",
    "71": "Hamlet construction", "72": "In a village", "73": "In a hamlet", "74": "In a watchtower",
    "75": "In a military post", "76": "In a bivouac", "77": "In a convoy", "78": "On a bus",
}

_GSVCS_FIELDS = ("FNATL", "CONAT", "ARSVC", "SVNAT", "INATL", "LNATL", "LNAT", "LNATI")
_SIZE_FIELDS = ("SMTH", "ISIZE")


def decode_code(field: str, code: str, report_type: str = "") -> str | None:
    """Return a documented label or None so callers can retain unknown source codes."""
    if field in _GSVCS_FIELDS:
        return CODE_VALUES["FNATL"].get(code)
    if field in _SIZE_FIELDS:
        return CODE_VALUES["FWSZS"].get(code)
    if field in {"PRVC1", "PRVC2", "PRVC3"}:
        return CODE_VALUES["PROVINCE"].get(code)
    # NARA specifies FWOPS for friendly actions and ACTNS for enemy incidents.
    if field == "TYPAT" and report_type == "E":
        return _ACTNS.get(code)
    return CODE_VALUES.get(field, {}).get(code)


_ACTNS = {
    "F1": "Covertly entered", "F2": "Attack", "F3": "Initiated operations", "F4": "Terminated operations",
    "F5": "Engage", "F6": "Contact", "F7": "Small-unit action", "F8": "Assault",
    "F9": "Other", "U1": "Mine incident", "U2": "Mine incident", "U3": "Discovery", "U4": "Accident",
    "U5": "Short round", "U6": "Mechanical failure", "U7": "Return fire", "U8": "Uncentered fire",
    "U9": "Investigate", "A1": "Armed attack", "A2": "Attacked by firing", "A3": "Ambushed",
    "A4": "Engaged", "A5": "Assaulted", "P1": "Propaganda activity", "P2": "Propagandized",
    "P3": "Leaflet activity", "P4": "Distributed leaflets", "P5": "Demonstration", "E1": "Covertly entered",
    "E2": "Overtly entered", "E3": "Entered", "H1": "Harassment", "H2": "Harassment fire",
    "H3": "Bombed", "H4": "Harassed", "H5": "Fired on aircraft", "H6": "Threw grenade",
    "M1": "Mine incident", "M2": "Stopped", "M3": "Blocked", "M4": "Destroyed", "M5": "Damaged",
    "M6": "Stole", "M7": "Burned", "M8": "Booby-trapped", "M9": "Detonation against",
    "S1": "Sabotage", "S2": "Sabotaged", "S3": "Sabotage with explosives", "T1": "Terrorism",
    "T2": "Terrorized", "T3": "Assassinated", "T4": "Murdered", "T5": "Kidnapped", "T6": "Captured",
    "X1": "Anti-aircraft incident", "X9": "Other",
}


def code_label_fields(fields: dict[str, str], report_type: str = "") -> dict[str, str]:
    labels = {}
    label_names = {"DATAT": "reportTypeLabel"}
    for field, code in fields.items():
        if not code:
            continue
        label = decode_code(field, code, report_type)
        if label:
            labels[label_names.get(field, f"{field.lower()}Label")] = label
    if fields.get("LSCAT") and fields.get("LSCLS"):
        loss_code = fields["LSCAT"] + fields["LSCLS"]
        if loss_code in _LOSS_CODES:
            labels["lossCodeLabel"] = _LOSS_CODES[loss_code]
    return labels


_LOSS_CODES = {
    "01": "Small arms", "02": "Pistols", "03": "Carbines", "04": "Rifles", "05": "M1 rifles",
    "06": "Shotguns", "07": "US-36 rifles", "08": "M-16 rifles", "09": "US-17 rifles",
    "10": "Automatic rifles", "11": "BAR", "12": "AR-15", "13": "Submachine guns",
    "14": "Thompson submachine guns", "15": "MAT-49 submachine guns", "16": "K50 submachine guns",
    "17": "Machine guns", "18": ".30 caliber machine guns", "19": ".50 caliber machine guns",
    "20": "Mortars", "21": "60 mm mortars", "22": "81 mm mortars", "23": "Recoilless rifles",
    "24": "105 mm recoilless rifles", "25": "57 mm recoilless rifles", "26": "75 mm recoilless rifles",
    "27": "Artillery", "28": "Counter-insurgency weapons", "29": "Mines", "30": "WAT mines",
    "31": "Antipersonnel mines", "32": "Antitank mines", "33": "Claymore mines", "34": "Foot mines",
    "35": "Booby traps", "36": "Bombs", "37": "Unknown weapons", "38": "Grenade launchers",
    "39": "CBU", "40": "Rocket launchers", "41": "Rockets", "42": "Automatic weapons",
    "A0": "Submachine-gun ammunition",
    "AA": "Hand grenades", "AC": "Small-arms ammunition", "AD": "Pistol ammunition", "AF": "Rifle ammunition",
    "B2": "Artillery rounds", "K0": "Trenches", "K1": "Miscellaneous material", "K2": "Personal gear",
    "K3": "Lines of communication", "K5": "Documents", "K6": "Clothing", "K7": "Stores", "K8": "Boats",
    "K9": "Intelligence material", "D0": "Unspecified structure", "D1": "Bridge", "D2": "Base",
    "D3": "House", "D4": "Bunker", "D5": "Blockhouse", "D6": "Building", "D7": "Post",
    "D8": "Security fencing", "D9": "Outpost", "C0": "Unspecified food", "C1": "Household rice",
    "C2": "Grain", "C3": "Household livestock", "C4": "Household manioc", "C5": "K ration manioc",
    "C6": "K ration rice", "C7": "K ration grain", "C8": "K ration salt", "C9": "Sugar",
    "CA": "Cattle", "CB": "Pack animals", "CC": "Grain", "CD": "Rice", "CE": "Water buffalo",
    "CF": "Salt", "CG": "Sugar", "F0": "Unspecified radio", "F1": "Telephone", "F3": "AN/PRC-6 radio",
    "F4": "AN/PRC-10 radio", "F5": "AN/PRC-9 radio", "F6": "TE20 radio", "F7": "TR6 radio",
    "E0": "Vehicles", "G0": "Medical supplies", "H0": "POL supplies", "I0": "Money", "J0": "Personnel",
}
