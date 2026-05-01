# ============================================================
# GENERATE.PY — generatorul principal de date sintetice
# ============================================================
# Ordine executie (respecta FK-urile):
#   1. branches
#   2. employees  →  update branches.manager_id
#   3. customers
#   4. accounts
#   5. cards
#   6. loans
#   7. transactions
# audit_log se populeaza automat prin triggerele SQLite
# ============================================================

import sqlite3
import random
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
from loguru import logger

from config  import *
from helpers import (
    generate_cnp, generate_iban, generate_card_number_masked,
    generate_amount, generate_timestamp, weighted_choice,
    random_id, random_reference_code, compute_amount_ron,
    random_salary_for_role, inject_technical_error, inject_logical_error,
    get_city_for_county, COUNTY_CNP_CODES,
)

fake = Faker("ro_RO")
random.seed(42)
np.random.seed(42)

# ── Conectare DB ─────────────────────────────────────────────
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ════════════════════════════════════════════════════════════
# 1. BRANCHES
# ════════════════════════════════════════════════════════════
def generate_branches(conn, n=NUM_BRANCHES):
    logger.info(f"Generare {n} sucursale...")

    # Luam judetele si regiunile din nomenclatoare
    counties = conn.execute("SELECT county_code, name, region FROM ref_counties").fetchall()
    selected = random.sample(counties, min(n, len(counties)))

    rows = []
    for i, county in enumerate(selected, start=1):
        city = get_city_for_county(county["county_code"])
        rows.append((
            random_id("BR", i, 3),              # branch_id
            f"Sucursala {city}",                # name
            county["county_code"],              # county_code
            county["region"],                   # region_code
            fake.street_address(),              # address
            city,                               # city
            f"02{random.randint(1000000,9999999)}",  # phone
            f"sucursala.{city.lower().replace(' ','')}@banca.ro",  # email
            1,                                  # is_active
            fake.date_between(start_date="-10y", end_date="-1y").isoformat(),  # opened_date
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO branches
        (branch_id, name, county_code, region_code, address, city,
         phone, email, is_active, opened_date)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()
    logger.success(f"  {len(rows)} sucursale inserate")
    return [r[0] for r in rows]   # lista branch_id


# ════════════════════════════════════════════════════════════
# 2. EMPLOYEES
# ════════════════════════════════════════════════════════════
def generate_employees(conn, branch_ids, n=NUM_EMPLOYEES):
    logger.info(f"Generare {n} angajati...")

    roles = list(EMPLOYEE_ROLE_WEIGHTS.keys())
    role_weights = list(EMPLOYEE_ROLE_WEIGHTS.values())

    # Asiguram cel putin 1 MANAGER per sucursala
    rows        = []
    managers    = {}   # branch_id -> employee_id manager
    emp_index   = 1

    # Prima trecere: 1 MANAGER per sucursala
    for branch_id in branch_ids:
        gender = random.choice(["M", "F"])
        first  = fake.first_name_male() if gender == "M" else fake.first_name_female()
        last   = fake.last_name()
        emp_id = random_id("EMP", emp_index, 4)
        email  = f"{first.lower()}.{last.lower()}{emp_index}@banca.ro"

        rows.append((
            emp_id, branch_id, "MANAGER",
            first, last, email,
            f"07{random.randint(10000000,99999999)}",
            fake.date_between(start_date="-15y", end_date="-2y").isoformat(),
            random_salary_for_role("MANAGER"),
            "ACTIVE",
        ))
        managers[branch_id] = emp_id
        emp_index += 1

    # A doua trecere: restul angajatilor distribuiti pe sucursale
    remaining = n - len(branch_ids)
    for i in range(remaining):
        branch_id = random.choice(branch_ids)
        role      = random.choices(
            [r for r in roles if r != "MANAGER"],
            weights=[EMPLOYEE_ROLE_WEIGHTS[r] for r in roles if r != "MANAGER"],
            k=1
        )[0]
        gender = random.choice(["M", "F"])
        first  = fake.first_name_male() if gender == "M" else fake.first_name_female()
        last   = fake.last_name()
        emp_id = random_id("EMP", emp_index, 4)
        email  = f"{first.lower()}.{last.lower()}{emp_index}@banca.ro"
        status = random.choices(["ACTIVE","ON_LEAVE","TERMINATED"], weights=[0.90,0.06,0.04])[0]

        rows.append((
            emp_id, branch_id, role,
            first, last, email,
            f"07{random.randint(10000000,99999999)}",
            fake.date_between(start_date="-10y", end_date="-1m").isoformat(),
            random_salary_for_role(role),
            status,
        ))
        emp_index += 1

    conn.executemany("""
        INSERT OR IGNORE INTO employees
        (employee_id, branch_id, role_code, first_name, last_name,
         email, phone, hire_date, salary, status)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, rows)

    # Update manager_id pe branches
    for branch_id, manager_id in managers.items():
        conn.execute(
            "UPDATE branches SET manager_id=? WHERE branch_id=?",
            (manager_id, branch_id)
        )
    conn.commit()
    logger.success(f"  {len(rows)} angajati inserati, {len(managers)} manageri asignati")
    return [r[0] for r in rows]   # lista employee_id


# ════════════════════════════════════════════════════════════
# 3. CUSTOMERS
# ════════════════════════════════════════════════════════════
def generate_customers(conn, n=NUM_CUSTOMERS):
    logger.info(f"Generare {n} clienti...")

    # Luam EXACT codurile din DB — nu presupunem nimic
    counties = [r[0] for r in conn.execute(
        "SELECT county_code FROM ref_counties WHERE is_active=1"
    ).fetchall()]
    
    valid_segments = [r[0] for r in conn.execute(
        "SELECT segment_code FROM ref_customer_segments"
    ).fetchall()]
    
    valid_kyc = [r[0] for r in conn.execute(
        "SELECT status_code FROM ref_kyc_statuses"
    ).fetchall()]

    rows    = []
    cnp_set = set()

    for i in range(1, n + 1):
        gender     = random.choice(["M", "F"])
        dob        = fake.date_of_birth(minimum_age=18, maximum_age=80)
        county     = random.choice(counties)
        city       = get_city_for_county(county)
        
        # Segment si KYC strict din valorile existente in DB
        segment    = random.choices(
            valid_segments,
            weights=[SEGMENT_WEIGHTS.get(s, 0.01) for s in valid_segments]
        )[0]
        kyc_status = random.choices(
            valid_kyc,
            weights=[0.85 if s=="VERIFIED" else 0.10 if s=="PENDING" 
                     else 0.04 if s=="FLAGGED" else 0.01 for s in valid_kyc]
        )[0]
        kyc_verified_at = (
            fake.date_time_between(start_date="-2y").isoformat()
            if kyc_status == "VERIFIED" else None
        )

        cnp = generate_cnp(
            datetime.combine(dob, datetime.min.time()), gender, county
        )
        attempts = 0
        while cnp in cnp_set and attempts < 10:
            cnp = generate_cnp(
                datetime.combine(dob, datetime.min.time()), gender, county
            )
            attempts += 1
        cnp_set.add(cnp)

        first = fake.first_name_male() if gender == "M" else fake.first_name_female()
        last  = fake.last_name()
        email = f"{first.lower()}.{last.lower()}{i}@{fake.free_email_domain()}"

        # Nu injectam erori de FK — le lasam doar pe cele de format
        # (erorile de FK ar bloca INSERT-ul complet)
        rows.append((
            random_id("CUST", i),
            first, last, cnp, email,
            f"07{random.randint(10000000, 99999999)}",
            dob.isoformat(), gender,
            county, city,
            fake.street_address(),
            "RO",           # country_code — mereu valid
            segment,
            kyc_status,
            kyc_verified_at,
            1,
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO customers
        (customer_id, first_name, last_name, cnp, email, phone,
         date_of_birth, gender, county_code, city, address,
         country_code, segment_code, kyc_status, kyc_verified_at, is_active)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()

    inserted = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    logger.success(f"  {inserted} clienti in baza de date")
    return [r[0] for r in conn.execute(
        "SELECT customer_id FROM customers"
    ).fetchall()]


# ════════════════════════════════════════════════════════════
# 4. ACCOUNTS
# ════════════════════════════════════════════════════════════
def generate_accounts(conn, customer_ids, branch_ids, n=NUM_ACCOUNTS):
    logger.info(f"Generare {n} conturi...")

    currencies = list(CURRENCY_WEIGHTS.keys())
    curr_w     = list(CURRENCY_WEIGHTS.values())
    rows       = []

    for i in range(1, n + 1):
        customer_id  = random.choice(customer_ids)
        branch_id    = random.choice(branch_ids)
        acc_type     = weighted_choice(ACCOUNT_TYPE_WEIGHTS)
        currency     = random.choices(currencies, weights=curr_w)[0]
        balance      = round(random.uniform(0, 50_000), 2)
        available    = round(balance * random.uniform(0.8, 1.0), 2)
        status       = random.choices(
            ["ACTIVE","FROZEN","BLOCKED","CLOSED"],
            weights=[0.90, 0.04, 0.03, 0.03]
        )[0]
        open_date_obj = fake.date_between(start_date="-8y", end_date="-1m")
        open_date    = open_date_obj.isoformat()
        close_date   = (
            fake.date_between(start_date=open_date_obj, end_date="today").isoformat()
            if status == "CLOSED" else None
        )

        rows.append((
            random_id("ACC", i),
            customer_id, branch_id, acc_type, currency,
            generate_iban(branch_id, i),
            balance, available, status,
            open_date, close_date,
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO accounts
        (account_id, customer_id, branch_id, account_type, currency_code,
         iban, balance, available_balance, status, open_date, close_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()
    logger.success(f"  {len(rows)} conturi inserate")
    return [r[0] for r in rows]


# ════════════════════════════════════════════════════════════
# 5. CARDS
# ════════════════════════════════════════════════════════════
def generate_cards(conn, account_ids, employee_ids, n=NUM_CARDS):
    logger.info(f"Generare {n} carduri...")

    # Cardurile se emit doar pe conturi CURRENT sau SAVINGS active
    eligible_accounts = [
        r[0] for r in conn.execute("""
            SELECT account_id FROM accounts
            WHERE account_type IN ('CURRENT','SAVINGS') AND status = 'ACTIVE'
        """).fetchall()
    ]
    if not eligible_accounts:
        eligible_accounts = account_ids

    card_types = ["DEBIT_VISA","DEBIT_MC","CREDIT_VISA","CREDIT_MC","PREPAID_VISA","VIRTUAL_MC"]
    card_w     = [0.30, 0.30, 0.18, 0.12, 0.07, 0.03]
    rows       = []
    today      = datetime.now().date()

    for i in range(1, n + 1):
        account_id  = random.choice(eligible_accounts)
        card_type   = random.choices(card_types, weights=card_w)[0]
        issued_date = fake.date_between(start_date="-5y", end_date="-1m")
        expiry_date_obj = issued_date + timedelta(days=365*3)
        expiry_date = expiry_date_obj.strftime("%Y-%m")
        has_credit  = card_type in ("CREDIT_VISA","CREDIT_MC")
        credit_limit = round(random.uniform(1000, 15000), 2) if has_credit else 0.0
        curr_balance = round(credit_limit * random.uniform(0, 0.7), 2) if has_credit else 0.0

        # Status determinat coerent cu expiry_date:
        # - card legitim expirat → EXPIRED sau CANCELLED
        # - card valid → distributie obisnuita pentru carduri active
        if expiry_date_obj < today:
            status = random.choices(
                ["EXPIRED", "CANCELLED"],
                weights=[0.80, 0.20]
            )[0]
        else:
            status = random.choices(
                ["ACTIVE", "BLOCKED", "CANCELLED"],
                weights=[0.92, 0.06, 0.02]
            )[0]

        record = {
            "card_id"            : random_id("CARD", i),
            "account_id"         : account_id,
            "card_type_code"     : card_type,
            "card_number_masked" : generate_card_number_masked(),
            "expiry_date"        : expiry_date,
            "credit_limit"       : credit_limit,
            "current_balance"    : curr_balance,
            "status"             : status,
            "issued_date"        : issued_date.isoformat(),
            "issued_by"          : random.choice(employee_ids),
        }

        # Injectare erori logice pe carduri (ramane la ~3% pentru demo Silver quarantine)
        if random.random() < ERROR_RATES["logical"]:
            record = inject_logical_error(record, "cards")

        rows.append((
            record["card_id"], record["account_id"], record["card_type_code"],
            record["card_number_masked"], record["expiry_date"],
            record["credit_limit"], record["current_balance"],
            record["status"], record["issued_date"], record["issued_by"],
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO cards
        (card_id, account_id, card_type_code, card_number_masked, expiry_date,
         credit_limit, current_balance, status, issued_date, issued_by)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()
    logger.success(f"  {len(rows)} carduri inserate")
    return [r[0] for r in rows]


# ════════════════════════════════════════════════════════════
# 6. LOANS
# ════════════════════════════════════════════════════════════
def generate_loans(conn, account_ids, employee_ids, n=NUM_LOANS):
    logger.info(f"Generare {n} credite...")

    loan_rates = {
        "MORTGAGE": 5.5, "PERSONAL": 9.9, "AUTO": 7.5,
        "OVERDRAFT": 18.0, "SME_WORKING": 8.5, "SME_INVEST": 7.0,
    }
    loan_amounts = {
        "MORTGAGE"   : (100_000, 500_000),
        "PERSONAL"   : (5_000,   50_000),
        "AUTO"       : (15_000,  80_000),
        "OVERDRAFT"  : (1_000,   10_000),
        "SME_WORKING": (20_000, 150_000),
        "SME_INVEST" : (50_000, 300_000),
    }
    loan_terms = {
        "MORTGAGE": 240, "PERSONAL": 60, "AUTO": 60,
        "OVERDRAFT": 12, "SME_WORKING": 36, "SME_INVEST": 120,
    }

    rows = []
    for i in range(1, n + 1):
        account_id  = random.choice(account_ids)
        loan_type   = weighted_choice(LOAN_TYPE_WEIGHTS)
        currency    = "RON"
        lo, hi      = loan_amounts.get(loan_type, (5000, 50000))
        principal   = round(random.uniform(lo, hi), 2)
        rate        = loan_rates.get(loan_type, 9.9)
        term        = loan_terms.get(loan_type, 60)
        # Calcul rata lunara (formula anuitate)
        r_lunar = rate / 100 / 12
        if r_lunar > 0:
            monthly = round(principal * r_lunar / (1 - (1 + r_lunar) ** (-term)), 2)
        else:
            monthly = round(principal / term, 2)

        start_date  = fake.date_between(start_date="-5y", end_date="-1m")
        end_date    = start_date + timedelta(days=30 * term)
        status      = weighted_choice(LOAN_STATUS_WEIGHTS)
        outstanding = round(principal * random.uniform(0.1, 0.95), 2) if status == "ACTIVE" else (
            0.0 if status == "CLOSED" else principal
        )
        approved_by = random.choice(employee_ids) if status != "APPLIED" else None
        approved_at = (
            fake.date_time_between(start_date=start_date, end_date="now").isoformat()
            if approved_by else None
        )

        record = {
            "loan_id"           : random_id("LOAN", i),
            "account_id"        : account_id,
            "loan_type_code"    : loan_type,
            "currency_code"     : currency,
            "principal_amount"  : principal,
            "outstanding_balance": outstanding,
            "interest_rate_pa"  : rate,
            "term_months"       : term,
            "monthly_payment"   : monthly,
            "start_date"        : start_date.isoformat(),
            "end_date"          : end_date.isoformat(),
            "status"            : status,
            "approved_by"       : approved_by,
            "approved_at"       : approved_at,
        }

        # Injectare erori logice pe credite
        if random.random() < ERROR_RATES["logical"]:
            record = inject_logical_error(record, "loans")

        rows.append((
            record["loan_id"], record["account_id"], record["loan_type_code"],
            record["currency_code"], record["principal_amount"],
            record["outstanding_balance"], record["interest_rate_pa"],
            record["term_months"], record["monthly_payment"],
            record["start_date"], record["end_date"], record["status"],
            record["approved_by"], record["approved_at"],
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO loans
        (loan_id, account_id, loan_type_code, currency_code, principal_amount,
         outstanding_balance, interest_rate_pa, term_months, monthly_payment,
         start_date, end_date, status, approved_by, approved_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()
    logger.success(f"  {len(rows)} credite inserate")
    return [r[0] for r in rows]


# ════════════════════════════════════════════════════════════
# 7. TRANSACTIONS
# ════════════════════════════════════════════════════════════
def generate_transactions(conn, account_ids, card_ids, employee_ids, n=NUM_TRANSACTIONS):
    logger.info(f"Generare {n} tranzactii istorice...")

    duplicates_to_inject = int(n * ERROR_RATES["duplicate"])
    rows                 = []
    ref_codes_set        = set()
    duplicate_candidates = []

    currencies = list(CURRENCY_WEIGHTS.keys())
    curr_w     = list(CURRENCY_WEIGHTS.values())

    for i in range(1, n + 1):
        account_id  = random.choice(account_ids)
        tx_type     = weighted_choice(TRANSACTION_TYPE_WEIGHTS)
        channel     = weighted_choice(CHANNEL_WEIGHTS)
        currency    = random.choices(currencies, weights=curr_w)[0]
        amount      = generate_amount(tx_type, AMOUNT_PROFILES)
        amount_ron  = compute_amount_ron(amount, currency, EXCHANGE_RATES)
        exc_rate    = EXCHANGE_RATES.get(currency, 1.0)
        status      = weighted_choice(STATUS_WEIGHTS)
        initiated   = generate_timestamp(DATE_START, DATE_END, HOURLY_WEIGHTS)
        completed   = (
            (initiated + timedelta(seconds=random.randint(1, 300))).isoformat()
            if status == "COMPLETED" else None
        )
        card_id     = (
            random.choice(card_ids) if card_ids and tx_type in ("POS","ATM_WITHDRAWAL") else None
        )
        employee_id = (
            random.choice(employee_ids) if tx_type in ("BRANCH","LOAN_REPAYMENT") else None
        )
        counterpart = fake.iban() if tx_type in ("TRANSFER_OUT","TRANSFER_IN") else None

        # Referinta unica
        ref = random_reference_code()
        while ref in ref_codes_set:
            ref = random_reference_code()
        ref_codes_set.add(ref)

        record = {
            "transaction_id" : random_id("TXN", i, 8),
            "account_id"     : account_id,
            "card_id"        : card_id,
            "counterpart_account": counterpart,
            "employee_id"    : employee_id,
            "type_code"      : tx_type,
            "status_code"    : status,
            "channel_code"   : channel,
            "currency_code"  : currency,
            "amount"         : amount,
            "amount_ron"     : amount_ron,
            "exchange_rate"  : exc_rate,
            "description"    : None,
            "reference_code" : ref,
            "initiated_at"   : initiated.isoformat(),
            "completed_at"   : completed,
        }

        # Injectare erori tehnice si logice
        if random.random() < ERROR_RATES["technical"]:
            record = inject_technical_error(record, "transactions")
        elif random.random() < ERROR_RATES["logical"]:
            record = inject_logical_error(record, "transactions")
        else:
            duplicate_candidates.append(record)

        rows.append((
            record["transaction_id"], record["account_id"], record["card_id"],
            record["counterpart_account"], record["employee_id"],
            record["type_code"], record["status_code"], record["channel_code"],
            record["currency_code"], record["amount"], record["amount_ron"],
            record["exchange_rate"], record["description"],
            record["reference_code"], record["initiated_at"], record["completed_at"],
        ))

    # Injectare duplicate
    logger.info(f"  Injectare {duplicates_to_inject} duplicate...")
    for _ in range(duplicates_to_inject):
        if not duplicate_candidates:
            break
        orig   = random.choice(duplicate_candidates)
        dup_id = orig["transaction_id"] + "-DUP"
        rows.append((
            dup_id, orig["account_id"], orig["card_id"],
            orig["counterpart_account"], orig["employee_id"],
            orig["type_code"], orig["status_code"], orig["channel_code"],
            orig["currency_code"],
            round(orig["amount"] * random.uniform(0.99, 1.01), 2),  # suma usor diferita
            orig["amount_ron"], orig["exchange_rate"],
            "DUPLICATE", orig["reference_code"] + "D",
            orig["initiated_at"], orig["completed_at"],
        ))

    # FK dezactivat intentionat: randurile cu status_code/channel_code invalide
    # (erori tehnice injectate) trebuie stocate ca date "murdare" in Bronze layer.
    # Silver layer din Databricks le va detecta si carantina.
    conn.execute("PRAGMA foreign_keys = OFF")
    batch_size = 1_000
    inserted   = 0
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        try:
            conn.executemany("""
                INSERT OR IGNORE INTO transactions
                (transaction_id, account_id, card_id, counterpart_account, employee_id,
                 type_code, status_code, channel_code, currency_code,
                 amount, amount_ron, exchange_rate, description,
                 reference_code, initiated_at, completed_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, batch)
            conn.commit()
            inserted += len(batch)
        except Exception as e:
            logger.warning(f"  Batch eroare: {e}")
    conn.execute("PRAGMA foreign_keys = ON")

    total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    logger.success(f"  {total} tranzactii in baza de date")


# ════════════════════════════════════════════════════════════
# MAIN — orchestreaza generarea completa
# ════════════════════════════════════════════════════════════
def run_full_generation():
    import os
    
    # Sterge DB existenta si o recreaza curat
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        logger.info("DB existenta stearsa — recreare curata")

    conn = get_connection()

    # Aplica schema si seed nomenclatoare (IF NOT EXISTS — sigur de rulat pe DB existenta)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conn.executescript(open(os.path.join(base_dir, "database", "schema.sql")).read())
    conn.executescript(open(os.path.join(base_dir, "database", "seed_nomenclatoare.sql")).read())
    logger.info("Schema si nomenclatoare reaplicate")

    logger.info("=" * 60)
    logger.info("START generare date bancare")
    logger.info(f"DB: {DB_PATH}")
    logger.info("=" * 60)

    start_time = datetime.now()

    # Verificam ca nomenclatoarele exista
    count = conn.execute("SELECT COUNT(*) FROM ref_countries").fetchone()[0]
    if count == 0:
        logger.error("Nomenclatoarele nu sunt populate! Ruleaza seed_nomenclatoare.sql intai.")
        conn.close()
        return

    branch_ids   = generate_branches(conn)
    employee_ids = generate_employees(conn, branch_ids)
    customer_ids = generate_customers(conn)
    account_ids  = generate_accounts(conn, customer_ids, branch_ids)
    card_ids     = generate_cards(conn, account_ids, employee_ids)
    _            = generate_loans(conn, account_ids, employee_ids)
    generate_transactions(conn, account_ids, card_ids, employee_ids)

    # Raport final
    elapsed = (datetime.now() - start_time).seconds
    logger.info("=" * 60)
    logger.info("RAPORT FINAL")
    for table in ["branches","employees","customers","accounts","cards","loans","transactions","audit_log"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        logger.info(f"  {table:<20} {cnt:>7} randuri")
    logger.info(f"  Timp total: {elapsed}s")
    logger.info("=" * 60)
    logger.success("Generare completa!")
    conn.close()


# ════════════════════════════════════════════════════════════
# UPDATE GENERATORS — simuleaza modificari pe entitati existente
# ════════════════════════════════════════════════════════════

def generate_customer_updates(conn):
    """Aplica modificari realiste pe un subset de clienti existenti."""
    logger.info("Actualizare clienti...")

    valid_segments = [r[0] for r in conn.execute(
        "SELECT segment_code FROM ref_customer_segments"
    ).fetchall()]
    valid_kyc = [r[0] for r in conn.execute(
        "SELECT status_code FROM ref_kyc_statuses"
    ).fetchall()]
    counties = [r[0] for r in conn.execute(
        "SELECT county_code FROM ref_counties WHERE is_active=1"
    ).fetchall()]

    customers = conn.execute(
        "SELECT customer_id, segment_code, kyc_status FROM customers WHERE is_active=1"
    ).fetchall()
    if not customers:
        logger.warning("  Nu exista clienti activi pentru actualizare")
        return

    n = max(1, int(len(customers) * UPDATE_RATES["customers"]))
    to_update = random.sample(customers, min(n, len(customers)))

    updated = 0
    for cust in to_update:
        change = random.choices(
            ["segment", "kyc", "address", "deactivate"],
            weights=[0.40, 0.35, 0.20, 0.05]
        )[0]

        if change == "segment":
            other = [s for s in valid_segments if s != cust["segment_code"]]
            if not other:
                continue
            conn.execute(
                "UPDATE customers SET segment_code=? WHERE customer_id=?",
                (random.choice(other), cust["customer_id"])
            )
        elif change == "kyc":
            other = [s for s in valid_kyc if s != cust["kyc_status"]]
            if not other:
                continue
            new_kyc = random.choice(other)
            kyc_verified_at = datetime.now().isoformat() if new_kyc == "VERIFIED" else None
            conn.execute(
                "UPDATE customers SET kyc_status=?, kyc_verified_at=? WHERE customer_id=?",
                (new_kyc, kyc_verified_at, cust["customer_id"])
            )
        elif change == "address":
            county = random.choice(counties)
            conn.execute(
                "UPDATE customers SET county_code=?, city=?, address=? WHERE customer_id=?",
                (county, get_city_for_county(county), fake.street_address(), cust["customer_id"])
            )
        elif change == "deactivate":
            conn.execute(
                "UPDATE customers SET is_active=0 WHERE customer_id=?",
                (cust["customer_id"],)
            )
        updated += 1

    conn.commit()
    logger.success(f"  {updated} clienti actualizati")


def generate_loan_updates(conn):
    """Progreseaza statusul creditelor si reduce soldul pentru cele active."""
    logger.info("Actualizare credite...")

    loans = conn.execute("""
        SELECT loan_id, status, outstanding_balance, monthly_payment, approved_by
        FROM loans WHERE status NOT IN ('CLOSED','REJECTED')
    """).fetchall()
    if not loans:
        logger.warning("  Nu exista credite eligibile pentru actualizare")
        return

    employee_ids = [r[0] for r in conn.execute(
        "SELECT employee_id FROM employees WHERE status='ACTIVE'"
    ).fetchall()]

    n = max(1, int(len(loans) * UPDATE_RATES["loans"]))
    to_update = random.sample(loans, min(n, len(loans)))

    updated = 0
    for loan in to_update:
        options = LOAN_TRANSITIONS.get(loan["status"])
        if not options:
            continue

        new_status = random.choices(
            [t[0] for t in options],
            weights=[t[1] for t in options]
        )[0]

        new_balance = loan["outstanding_balance"]
        if new_status == "ACTIVE" and loan["status"] == "ACTIVE":
            new_balance = max(0.0, round(
                loan["outstanding_balance"] - loan["monthly_payment"] * random.uniform(0.9, 1.1), 2
            ))
            if new_balance == 0.0:
                new_status = "CLOSED"
        elif new_status == "CLOSED":
            new_balance = 0.0

        new_approved_by = loan["approved_by"]
        new_approved_at = None
        if loan["approved_by"] is None and new_status in ("APPROVED", "ACTIVE") and employee_ids:
            new_approved_by = random.choice(employee_ids)
            new_approved_at = datetime.now().isoformat()

        if new_approved_at:
            conn.execute(
                "UPDATE loans SET status=?, outstanding_balance=?, approved_by=?, approved_at=? WHERE loan_id=?",
                (new_status, new_balance, new_approved_by, new_approved_at, loan["loan_id"])
            )
        else:
            conn.execute(
                "UPDATE loans SET status=?, outstanding_balance=? WHERE loan_id=?",
                (new_status, new_balance, loan["loan_id"])
            )
        updated += 1

    conn.commit()
    logger.success(f"  {updated} credite actualizate")


def generate_card_updates(conn):
    """Schimba statusul cardurilor si ajusteaza limitele de credit."""
    logger.info("Actualizare carduri...")

    cards = conn.execute("""
        SELECT card_id, status, card_type_code, credit_limit, current_balance
        FROM cards WHERE status != 'CANCELLED'
    """).fetchall()
    if not cards:
        logger.warning("  Nu exista carduri eligibile pentru actualizare")
        return

    n = max(1, int(len(cards) * UPDATE_RATES["cards"]))
    to_update = random.sample(cards, min(n, len(cards)))

    updated = 0
    for card in to_update:
        options = CARD_TRANSITIONS.get(card["status"])
        if not options:
            continue

        new_status = random.choices(
            [t[0] for t in options],
            weights=[t[1] for t in options]
        )[0]

        new_limit   = card["credit_limit"]
        new_balance = card["current_balance"]

        if (new_status == "ACTIVE" and card["status"] == "ACTIVE"
                and card["card_type_code"] in ("CREDIT_VISA", "CREDIT_MC")
                and random.random() < 0.30):
            new_limit   = round(min(card["credit_limit"] * random.uniform(0.8, 1.5), 50_000.0), 2)
            new_balance = min(card["current_balance"], new_limit)

        conn.execute(
            "UPDATE cards SET status=?, credit_limit=?, current_balance=? WHERE card_id=?",
            (new_status, new_limit, new_balance, card["card_id"])
        )
        updated += 1

    conn.commit()
    logger.success(f"  {updated} carduri actualizate")


def generate_account_updates(conn):
    """Schimba statusul conturilor si aplica drift de sold simuland tranzactii agregate."""
    logger.info("Actualizare conturi...")

    accounts = conn.execute("""
        SELECT account_id, status, balance, available_balance, account_type
        FROM accounts WHERE status != 'CLOSED'
    """).fetchall()
    if not accounts:
        logger.warning("  Nu exista conturi eligibile pentru actualizare")
        return

    n = max(1, int(len(accounts) * UPDATE_RATES.get("accounts", 0.04)))
    to_update = random.sample(accounts, min(n, len(accounts)))

    updated = 0
    for acc in to_update:
        options = ACCOUNT_TRANSITIONS.get(acc["status"])
        if not options:
            continue

        new_status = random.choices(
            [t[0] for t in options],
            weights=[t[1] for t in options]
        )[0]

        new_balance   = acc["balance"]
        new_available = acc["available_balance"]

        if new_status == "ACTIVE" and acc["status"] == "ACTIVE":
            # Drift de sold: simuleaza efectul net al tranzactiilor din batch
            drift = round(random.uniform(-2_000, 2_000), 2)
            new_balance   = max(0.0, round(acc["balance"] + drift, 2))
            new_available = round(new_balance * random.uniform(0.85, 1.0), 2)
        elif new_status == "CLOSED":
            new_balance   = 0.0
            new_available = 0.0

        conn.execute(
            "UPDATE accounts SET status=?, balance=?, available_balance=? WHERE account_id=?",
            (new_status, new_balance, new_available, acc["account_id"])
        )
        updated += 1

    conn.commit()
    logger.success(f"  {updated} conturi actualizate")


# ════════════════════════════════════════════════════════════
# BATCH GENERATION — pentru scheduler (flux continuu)
# ════════════════════════════════════════════════════════════
def run_batch_generation(n_transactions=SCHEDULER_BATCH_TRANSACTIONS):
    """Adauga un batch mic de tranzactii noi — apelat de scheduler."""
    conn         = get_connection()
    account_ids  = [r[0] for r in conn.execute("SELECT account_id FROM accounts WHERE status='ACTIVE'").fetchall()]
    card_ids     = [r[0] for r in conn.execute("SELECT card_id FROM cards WHERE status='ACTIVE'").fetchall()]
    employee_ids = [r[0] for r in conn.execute("SELECT employee_id FROM employees WHERE status='ACTIVE'").fetchall()]

    if not account_ids:
        logger.warning("Nu exista conturi active. Ruleaza mai intai run_full_generation().")
        conn.close()
        return

    # Gasim ultimul index de tranzactie
    last = conn.execute("SELECT MAX(transaction_id) FROM transactions").fetchone()[0]
    start_index = int(last.split("-")[1]) + 1 if last else 1

    # Generam tranzactii noi cu timestamp = acum
    now  = datetime.now()
    rows = []
    for i in range(n_transactions):
        idx        = start_index + i
        account_id = random.choice(account_ids)
        tx_type    = weighted_choice(TRANSACTION_TYPE_WEIGHTS)
        channel    = weighted_choice(CHANNEL_WEIGHTS)
        currency   = weighted_choice(CURRENCY_WEIGHTS)
        amount     = generate_amount(tx_type, AMOUNT_PROFILES)
        amount_ron = compute_amount_ron(amount, currency, EXCHANGE_RATES)
        status     = weighted_choice(STATUS_WEIGHTS)
        card_id    = random.choice(card_ids) if card_ids and tx_type in ("POS","ATM_WITHDRAWAL") else None
        initiated  = now - timedelta(seconds=random.randint(0, 300))
        completed  = (initiated + timedelta(seconds=random.randint(1, 60))).isoformat() if status == "COMPLETED" else None

        rows.append((
            random_id("TXN", idx, 8), account_id, card_id, None, None,
            tx_type, status, channel, currency,
            amount, amount_ron, EXCHANGE_RATES.get(currency, 1.0),
            None, random_reference_code(), initiated.isoformat(), completed,
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO transactions
        (transaction_id, account_id, card_id, counterpart_account, employee_id,
         type_code, status_code, channel_code, currency_code,
         amount, amount_ron, exchange_rate, description,
         reference_code, initiated_at, completed_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    logger.info(f"Batch: +{n_transactions} tranzactii | Total: {total}")

    generate_customer_updates(conn)
    generate_loan_updates(conn)
    generate_card_updates(conn)
    generate_account_updates(conn)

    conn.close()


if __name__ == "__main__":
    run_full_generation()