# ============================================================
# CONFIG — volume, distributii, probabilitati
# ============================================================

from datetime import datetime, timedelta
import os

# ── Baza de date ─────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "banking.db")

# ── Volumul datelor generate (one-shot initial) ──────────────
NUM_BRANCHES    = 20
NUM_EMPLOYEES   = 60       # ~3 per sucursala
NUM_CUSTOMERS   = 500
NUM_ACCOUNTS    = 800      # ~1.6 per client
NUM_CARDS       = 600      # doar pe conturi CURRENT
NUM_LOANS       = 200
NUM_TRANSACTIONS = 50_000  # istorice, ultimele 12 luni

# ── Fereastra temporala istorica ─────────────────────────────
DATE_END   = datetime.now()
DATE_START = DATE_END - timedelta(days=365)

# ── Distributia segmentelor clienti ─────────────────────────
SEGMENT_WEIGHTS = {
    "RETAIL"    : 0.80,
    "PREMIUM"   : 0.15,
    "SME"       : 0.04,
    "CORPORATE" : 0.01,
}

# ── Distributia tipurilor de conturi ────────────────────────
ACCOUNT_TYPE_WEIGHTS = {
    "CURRENT"  : 0.55,
    "SAVINGS"  : 0.30,
    "DEPOSIT"  : 0.10,
    "LOAN_ACC" : 0.05,
}

# ── Distributia canalelor tranzactii ────────────────────────
CHANNEL_WEIGHTS = {
    "POS"          : 0.38,
    "ONLINE"       : 0.25,
    "ATM"          : 0.18,
    "MOBILE"       : 0.12,
    "BRANCH"       : 0.05,
    "DIRECT_DEBIT" : 0.02,
}

# ── Distributia tipurilor de tranzactii ─────────────────────
TRANSACTION_TYPE_WEIGHTS = {
    "POS"              : 0.30,
    "TRANSFER_OUT"     : 0.20,
    "ATM_WITHDRAWAL"   : 0.15,
    "PAYMENT"          : 0.12,
    "TRANSFER_IN"      : 0.08,
    "DIRECT_DEBIT"     : 0.05,
    "LOAN_REPAYMENT"   : 0.04,
    "FEE"              : 0.03,
    "CREDIT"           : 0.02,
    "ATM_DEPOSIT"      : 0.01,
}

# ── Distributia statusurilor tranzactii ─────────────────────
STATUS_WEIGHTS = {
    "COMPLETED" : 0.88,
    "PENDING"   : 0.05,
    "FAILED"    : 0.04,
    "REVERSED"  : 0.02,
    "ON_HOLD"   : 0.01,
}

# ── Distributia valutelor ────────────────────────────────────
CURRENCY_WEIGHTS = {
    "RON" : 0.82,
    "EUR" : 0.12,
    "USD" : 0.04,
    "GBP" : 0.01,
    "CHF" : 0.01,
}

# ── Rate de schimb fata de RON ───────────────────────────────
EXCHANGE_RATES = {
    "RON" : 1.0,
    "EUR" : 4.97,
    "USD" : 4.61,
    "GBP" : 5.83,
    "CHF" : 5.10,
    "HUF" : 0.0126,
}

# ── Distributia rolurilor angajati per sucursala ─────────────
EMPLOYEE_ROLE_WEIGHTS = {
    "TELLER"  : 0.40,
    "ADVISOR" : 0.35,
    "MANAGER" : 0.10,   # 1 manager per sucursala
    "ANALYST" : 0.10,
    "ADMIN"   : 0.05,
}

# ── Distributia tipurilor de credite ────────────────────────
LOAN_TYPE_WEIGHTS = {
    "PERSONAL"    : 0.40,
    "MORTGAGE"    : 0.25,
    "AUTO"        : 0.15,
    "OVERDRAFT"   : 0.12,
    "SME_WORKING" : 0.05,
    "SME_INVEST"  : 0.03,
}

# ── Distributia statusurilor credite ────────────────────────
LOAN_STATUS_WEIGHTS = {
    "ACTIVE"   : 0.60,
    "CLOSED"   : 0.20,
    "APPROVED" : 0.10,
    "OVERDUE"  : 0.07,
    "APPLIED"  : 0.03,
}

# ── Profile sume tranzactii (log-normala) ────────────────────
# (mean, sigma) pentru numpy lognormal — in RON
AMOUNT_PROFILES = {
    "POS"            : (5.0, 1.2),   # majority 50-500 RON
    "ATM_WITHDRAWAL" : (5.5, 0.8),   # majority 100-500 RON
    "TRANSFER_OUT"   : (6.5, 1.5),   # wider range
    "PAYMENT"        : (5.8, 1.0),
    "LOAN_REPAYMENT" : (7.0, 0.5),   # consistent amounts
    "DEFAULT"        : (5.2, 1.3),
}

# ── Profil orar tranzactii (pondere per ora 0-23) ────────────
HOURLY_WEIGHTS = [
    0.5, 0.3, 0.2, 0.1, 0.1, 0.2,   # 00-05 (noapte, minim)
    0.5, 1.5, 3.0, 4.5, 4.0, 3.5,   # 06-11 (dimineata, varf)
    3.0, 3.5, 3.0, 2.5, 3.5, 4.5,   # 12-17 (pranz + dupa-amiaza)
    4.0, 3.0, 2.5, 2.0, 1.5, 1.0,   # 18-23 (seara, descrescator)
]

# ── Rate erori intentionate ──────────────────────────────────
ERROR_RATES = {
    "technical"  : 0.03,   # 3% erori tehnice
    "logical"    : 0.03,   # 3% inconsistente logice
    "duplicate"  : 0.02,   # 2% duplicate
}
# Total ~8% date invalide pentru demonstrarea Silver quarantine

# ── Scheduler — flux continuu ────────────────────────────────
SCHEDULER_INTERVAL_MINUTES = 5     # ruleaza la fiecare 5 minute
SCHEDULER_BATCH_TRANSACTIONS = 50  # tranzactii noi per rulare

# ── Rate actualizari entitati per batch ──────────────────────
# Procentul din populatia totala care primeste o schimbare per batch
UPDATE_RATES = {
    "customers" : 0.05,   # 5%  — segment, KYC, adresa, dezactivare
    "loans"     : 0.08,   # 8%  — progresie status + reducere sold
    "cards"     : 0.04,   # 4%  — blocare/deblocare, limita credit
}

# Tranzitii status credite (stare_curenta -> [(stare_noua, probabilitate)])
LOAN_TRANSITIONS = {
    "APPLIED":  [("APPROVED", 0.70), ("REJECTED", 0.30)],
    "APPROVED": [("ACTIVE",   0.85), ("REJECTED", 0.15)],
    "ACTIVE":   [("OVERDUE",  0.15), ("CLOSED",   0.10), ("ACTIVE",   0.75)],
    "OVERDUE":  [("ACTIVE",   0.35), ("CLOSED",   0.35), ("OVERDUE",  0.30)],
}

# Tranzitii status carduri
CARD_TRANSITIONS = {
    "ACTIVE":  [("BLOCKED",   0.20), ("CANCELLED", 0.05), ("ACTIVE",  0.75)],
    "BLOCKED": [("ACTIVE",    0.60), ("CANCELLED", 0.20), ("BLOCKED", 0.20)],
    "EXPIRED": [("CANCELLED", 0.80), ("EXPIRED",   0.20)],
}

# Tranzitii status conturi
ACCOUNT_TRANSITIONS = {
    "ACTIVE":  [("FROZEN", 0.02), ("BLOCKED", 0.02), ("CLOSED", 0.01), ("ACTIVE", 0.95)],
    "FROZEN":  [("ACTIVE", 0.60), ("BLOCKED", 0.10), ("FROZEN", 0.30)],
    "BLOCKED": [("ACTIVE", 0.40), ("CLOSED",  0.20), ("BLOCKED", 0.40)],
}