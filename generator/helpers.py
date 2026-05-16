# ============================================================
# HELPERS — functii utilitare pentru generare date realiste
# ============================================================

import random
import string
import numpy as np
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("ro_RO")

# ── Judete Romania cu codul de judet din CNP ─────────────────
# Sursa: standardul oficial ANAF — ordinea alfabetica a denumirilor
# 01-39 = judete istorice, 40 = Bucuresti (general), 41-46 = sectoare 1-6,
# 51 = Calarasi, 52 = Giurgiu (judete create dupa 1981)
COUNTY_CNP_CODES = {
    "AB": "01", "AR": "02", "AG": "03", "BC": "04", "BH": "05",
    "BN": "06", "BT": "07", "BV": "08", "BR": "09", "BZ": "10",
    "CS": "11", "CJ": "12", "CT": "13", "CV": "14", "DB": "15",
    "DJ": "16", "GL": "17", "GJ": "18", "HR": "19", "HD": "20",
    "IL": "21", "IS": "22", "IF": "23", "MM": "24", "MH": "25",
    "MS": "26", "NT": "27", "OT": "28", "PH": "29", "SM": "30",
    "SJ": "31", "SB": "32", "SV": "33", "TR": "34", "TM": "35",
    "TL": "36", "VS": "37", "VL": "38", "VN": "39",
    "B" : "41",  # Bucuresti — sector 1 (placeholder; randomizat in generate_cnp)
    "CL": "51", "GR": "52",
}

# Sectoarele Bucurestiului (41-46) — pentru randomizarea CNP-urilor din B
BUCURESTI_SECTOR_CODES = ["41", "42", "43", "44", "45", "46"]

# ── Orase principale per judet ───────────────────────────────
COUNTY_CITIES = {
    "B" : ["Bucuresti"], "CJ": ["Cluj-Napoca", "Dej", "Turda"],
    "TM": ["Timisoara", "Lugoj"], "IS": ["Iasi", "Pascani"],
    "CT": ["Constanta", "Mangalia", "Medgidia"],
    "BV": ["Brasov", "Fagaras", "Sacele"],
    "PH": ["Ploiesti", "Campina", "Sinaia"],
    "DJ": ["Craiova", "Bailesti"], "GL": ["Galati", "Tecuci"],
    "BC": ["Bacau", "Onesti", "Moinesti"],
    "AR": ["Arad", "Ineu"], "SB": ["Sibiu", "Medias"],
    "MS": ["Targu Mures", "Reghin", "Sighisoara"],
    "BH": ["Oradea", "Salonta", "Beius"],
    "HD": ["Deva", "Hunedoara", "Petrosani"],
    "VL": ["Ramnicu Valcea", "Dragasani"],
    "AG": ["Pitesti", "Curtea de Arges", "Mioveni"],
}

def get_city_for_county(county_code: str) -> str:
    """Returneaza un oras din judetul dat."""
    cities = COUNTY_CITIES.get(county_code, [county_code + " Oras"])
    return random.choice(cities)


def generate_cnp(date_of_birth: datetime, gender: str, county_code: str) -> str:
    """
    Genereaza un CNP valid ca format pentru Romania.
    S + AA + LL + ZZ + JJ + NNN + C
    S  = cifra sex + secol
    AA = ultimele 2 cifre an nastere
    LL = luna nastere
    ZZ = zi nastere
    JJ = cod judet
    NNN = numar ordine (001-999)
    C  = cifra de control (calculata)
    """
    year  = date_of_birth.year
    month = date_of_birth.month
    day   = date_of_birth.day

    # Cifra de sex si secol
    if year >= 2000:
        s = "5" if gender == "M" else "6"
    elif year >= 1900:
        s = "1" if gender == "M" else "2"
    else:
        s = "3" if gender == "M" else "4"

    aa  = str(year)[-2:]
    ll  = f"{month:02d}"
    zz  = f"{day:02d}"
    # Bucurestiul foloseste codurile 41-46 (un cod per sector) — randomizam intre sectoare
    if county_code == "B":
        jj = random.choice(BUCURESTI_SECTOR_CODES)
    else:
        jj = COUNTY_CNP_CODES.get(county_code, "01")
    nnn = f"{random.randint(1, 999):03d}"

    partial = s + aa + ll + zz + jj + nnn

    # Calculul cifrei de control
    weights = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9]
    total   = sum(int(partial[i]) * weights[i] for i in range(12))
    rest    = total % 11
    c       = "1" if rest == 10 else str(rest)

    return partial + c


def generate_iban(branch_id: str, account_index: int) -> str:
    """
    Genereaza un IBAN romanesc cu format valid.
    RO + 2 cifre control + 4 litere banca + 16 cifre cont
    """
    bank_code  = "RBNK"   # cod banca fictiv consistent
    account_nr = f"{account_index:016d}"
    iban       = f"RO49{bank_code}{account_nr}"
    return iban


def generate_card_number(card_brand='visa'):
    # Prefix conform standardelor ISO 7812
    prefix = '4' if card_brand == 'visa' else str(random.randint(51, 55))
    # Generare primele 15 cifre (prefix + random)
    digits = prefix + ''.join(
        str(random.randint(0, 9))
        for _ in range(15 - len(prefix))
    )
    # Calcul cifra de control Luhn
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2 == 0:
            n *= 2
            if n > 9: n -= 9
        total += n
    check = (10 - (total % 10)) % 10
    return digits + str(check)


def generate_amount(type_code: str, profiles: dict) -> float:
    """
    Genereaza o suma realista folosind distributie log-normala.
    Returneaza suma rotunjita la 2 zecimale.
    """
    mean, sigma = profiles.get(type_code, profiles["DEFAULT"])
    amount = np.random.lognormal(mean=mean, sigma=sigma)
    # Limiteaza la valori rezonabile: minim 1 RON, maxim 500.000 RON
    amount = max(1.0, min(amount, 500_000.0))
    return round(amount, 2)


def generate_timestamp(start: datetime, end: datetime, hourly_weights: list) -> datetime:
    """
    Genereaza un timestamp realist intre start si end,
    cu distributie orara conform profilului bancii.
    """
    # Alege o zi random in interval
    delta_days = (end - start).days
    random_day = start + timedelta(days=random.randint(0, delta_days))

    # Alege ora conform distributiei
    hour = random.choices(range(24), weights=hourly_weights, k=1)[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return random_day.replace(hour=hour, minute=minute, second=second)


def weighted_choice(weights_dict: dict) -> str:
    """Alege o cheie dintr-un dictionar conform ponderilor."""
    keys    = list(weights_dict.keys())
    weights = list(weights_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]


def random_id(prefix: str, index: int, padding: int = 6) -> str:
    """Genereaza un ID formatat: PREFIX-000001"""
    return f"{prefix}-{index:0{padding}d}"


def random_reference_code() -> str:
    """Genereaza un cod de referinta unic pentru tranzactie."""
    chars = string.ascii_uppercase + string.digits
    return "REF-" + "".join(random.choices(chars, k=12))


def compute_amount_ron(amount: float, currency: str, rates: dict) -> float:
    """Calculeaza echivalentul in RON al unei sume in valuta."""
    rate = rates.get(currency, 1.0)
    return round(amount * rate, 2)


def random_salary_for_role(role_code: str) -> float:
    """Genereaza un salariu realist pentru fiecare rol bancar."""
    salary_ranges = {
        "TELLER"  : (3_500,  5_500),
        "ADVISOR" : (5_000,  9_000),
        "MANAGER" : (9_000, 18_000),
        "ANALYST" : (6_000, 12_000),
        "ADMIN"   : (7_000, 15_000),
    }
    low, high = salary_ranges.get(role_code, (4_000, 8_000))
    return round(random.uniform(low, high), 2)


# ── Functii pentru injectare erori intentionate ──────────────

def inject_technical_error(record: dict, entity: str) -> dict:
    """
    Injecteaza o eroare tehnica intr-un record.
    Adauga _error_injected si _error_type pentru tracking.
    """
    record = record.copy()
    errors = []

    if entity == "transactions":
        error_type = random.choice(["null_amount", "negative_amount", "invalid_status", "invalid_fk"])
        if error_type == "null_amount":
            record["amount"] = None
            errors.append("amount IS NULL")
        elif error_type == "negative_amount":
            record["amount"] = round(random.uniform(-1000, -1), 2)
            errors.append("amount < 0")
        elif error_type == "invalid_status":
            record["status_code"] = "INVALID_STATUS"
            errors.append("status_code not in ref_transaction_statuses")
        elif error_type == "invalid_fk":
            record["channel_code"] = "INVALID_CHANNEL"
            errors.append("channel_code FK violation")

    elif entity == "customers":
        error_type = random.choice(["invalid_email", "invalid_cnp", "invalid_fk"])
        if error_type == "invalid_email":
            record["email"] = record["email"].replace("@", "")
            errors.append("email missing @")
        elif error_type == "invalid_cnp":
            record["cnp"] = record["cnp"][:-1]   # 12 cifre in loc de 13
            errors.append("cnp length != 13")
        elif error_type == "invalid_fk":
            record["county_code"] = "XX"
            errors.append("county_code FK violation")

    record["_error_injected"] = True
    record["_error_type"]     = "technical:" + "|".join(errors)
    return record


def inject_logical_error(record: dict, entity: str) -> dict:
    """Injecteaza o inconsistenta logica intr-un record."""
    record = record.copy()
    errors = []

    if entity == "transactions":
        error_type = random.choice(["inverted_dates", "wrong_amount_ron"])
        if error_type == "inverted_dates" and record.get("completed_at"):
            # completed_at inainte de initiated_at
            initiated = datetime.fromisoformat(record["initiated_at"])
            record["completed_at"] = (initiated - timedelta(hours=random.randint(1, 48))).isoformat()
            errors.append("completed_at < initiated_at")
        elif error_type == "wrong_amount_ron":
            # amount_ron nu corespunde cu amount * exchange_rate
            record["amount_ron"] = round(record.get("amount_ron", 100) * random.uniform(3, 10), 2)
            errors.append("amount_ron inconsistent with amount * exchange_rate")

    elif entity == "cards":
        # Card expirat dar status ACTIVE
        record["expiry_date"] = (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m")
        record["status"]      = "ACTIVE"
        errors.append("card expired but status=ACTIVE")

    elif entity == "loans":
        # end_date inainte de start_date
        start = datetime.fromisoformat(record["start_date"])
        record["end_date"] = (start - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d")
        errors.append("end_date < start_date")

    record["_error_injected"] = True
    record["_error_type"]     = "logical:" + "|".join(errors)
    return record