-- ============================================================
-- SISTEM INFORMATIC BANCAR - SCHEMA SQLite
-- ============================================================
-- Structura: 14 tabele nomenclatoare (ref_*) + 8 tabele principale
-- Conventii: snake_case, PK = <entitate>_id, FK explicite
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- ============================================================
-- SECTIUNEA 1: TABELE NOMENCLATOARE (ref_*)
-- Date statice / semi-statice, sursa de adevar pentru coduri
-- ============================================================

-- 1.1 Tari
CREATE TABLE IF NOT EXISTS ref_countries(
    country_code    TEXT PRIMARY KEY,
    name_ro         TEXT NOT NULL,
    name_en         TEXT NOT NULL,
    is_eu           INTEGER NOT NULL DEFAULT 0,
    is_sepa         INTEGER NOT NULL DEFAULT 0,
    risk_tier       TEXT NOT NULL DEFAULT 'LOW'
                    CHECK(risk_tier IN ('LOW','MEDIUM','HIGH')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 1.2 Judete Romania
CREATE TABLE IF NOT EXISTS ref_counties (
    county_code     TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    region          TEXT NOT NULL,
    country_code    TEXT NOT NULL DEFAULT 'RO'
                    REFERENCES ref_countries(country_code),
    is_active       INTEGER NOT NULL DEFAULT 1
);

-- 1.3 Valute
CREATE TABLE IF NOT EXISTS ref_currencies (
    currency_code   TEXT PRIMARY KEY,
    name_ro         TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    decimals        INTEGER NOT NULL DEFAULT 2,
    is_base         INTEGER NOT NULL DEFAULT 0,
    exchange_rate   REAL NOT NULL DEFAULT 1.0,
    is_active       INTEGER NOT NULL DEFAULT 1,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 1.4 Tipuri tranzactii
CREATE TABLE IF NOT EXISTS ref_transaction_types (
    type_code       TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    direction       TEXT NOT NULL
                    CHECK(direction IN ('IN','OUT','BOTH')),
    affects_balance INTEGER NOT NULL DEFAULT 1,
    requires_card   INTEGER NOT NULL DEFAULT 0,
    description     TEXT
);

-- 1.5 Statusuri tranzactii
CREATE TABLE IF NOT EXISTS ref_transaction_statuses (
    status_code     TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    is_final        INTEGER NOT NULL DEFAULT 0,
    retry_allowed   INTEGER NOT NULL DEFAULT 0,
    description     TEXT
);

-- 1.6 Segmente clienti
CREATE TABLE IF NOT EXISTS ref_customer_segments (
    segment_code    TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    min_balance     REAL NOT NULL DEFAULT 0,
    fee_waiver      INTEGER NOT NULL DEFAULT 0,
    priority_support INTEGER NOT NULL DEFAULT 0,
    description     TEXT
);

-- 1.7 Tipuri conturi
CREATE TABLE IF NOT EXISTS ref_account_types (
    type_code           TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    allows_overdraft    INTEGER NOT NULL DEFAULT 0,
    taxable             INTEGER NOT NULL DEFAULT 1,
    min_balance         REAL NOT NULL DEFAULT 0,
    interest_rate_pa    REAL NOT NULL DEFAULT 0.0,
    description         TEXT
);

-- 1.8 Tipuri credite
CREATE TABLE IF NOT EXISTS ref_loan_types (
    loan_type_code  TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    max_ltv         REAL,
    typical_rate_pa REAL NOT NULL,
    max_term_months INTEGER NOT NULL,
    requires_collateral INTEGER NOT NULL DEFAULT 0,
    description     TEXT
);

-- 1.9 Tipuri carduri
CREATE TABLE IF NOT EXISTS ref_card_types (
    card_type_code  TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    network         TEXT NOT NULL
                    CHECK(network IN ('VISA','MASTERCARD','AMEX','UNIONPAY')),
    has_credit_line INTEGER NOT NULL DEFAULT 0,
    contactless     INTEGER NOT NULL DEFAULT 1,
    annual_fee      REAL NOT NULL DEFAULT 0,
    description     TEXT
);

-- 1.10 Canale bancare
CREATE TABLE IF NOT EXISTS ref_channels (
    channel_code        TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    max_tx_amount       REAL,
    max_daily_amount    REAL,
    requires_pin        INTEGER NOT NULL DEFAULT 0,
    is_active           INTEGER NOT NULL DEFAULT 1,
    description         TEXT
);

-- 1.11 Benzi de risc
CREATE TABLE IF NOT EXISTS ref_risk_bands (
    band_code       TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    score_min       INTEGER NOT NULL,
    score_max       INTEGER NOT NULL,
    auto_approve    INTEGER NOT NULL DEFAULT 0,
    auto_reject     INTEGER NOT NULL DEFAULT 0,
    monitoring_freq TEXT NOT NULL DEFAULT 'MONTHLY'
                    CHECK(monitoring_freq IN ('DAILY','WEEKLY','MONTHLY'))
);

-- 1.12 Statusuri KYC
CREATE TABLE IF NOT EXISTS ref_kyc_statuses (
    status_code     TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    requires_review INTEGER NOT NULL DEFAULT 0,
    aml_flag        INTEGER NOT NULL DEFAULT 0,
    allows_transactions INTEGER NOT NULL DEFAULT 1,
    description     TEXT
);

-- 1.13 Roluri angajati
CREATE TABLE IF NOT EXISTS ref_employee_roles (
    role_code           TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    can_approve_loans   INTEGER NOT NULL DEFAULT 0,
    loan_approval_limit REAL,
    can_block_accounts  INTEGER NOT NULL DEFAULT 0,
    can_view_reports    INTEGER NOT NULL DEFAULT 1,
    description         TEXT
);

-- 1.14 Regiuni bancare
CREATE TABLE IF NOT EXISTS ref_regions (
    region_code         TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    headquarters_county TEXT NOT NULL
                        REFERENCES ref_counties(county_code),
    counties_count      INTEGER NOT NULL DEFAULT 0
);

-- ============================================================
-- SECTIUNEA 2: TABELE PRINCIPALE
-- ============================================================

-- 2.1 Sucursale
CREATE TABLE IF NOT EXISTS branches (
    branch_id       TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    county_code     TEXT NOT NULL
                    REFERENCES ref_counties(county_code),
    region_code     TEXT NOT NULL
                    REFERENCES ref_regions(region_code),
    address         TEXT NOT NULL,
    city            TEXT NOT NULL,
    phone           TEXT,
    email           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    opened_date     TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2.2 Angajati
CREATE TABLE IF NOT EXISTS employees (
    employee_id     TEXT PRIMARY KEY,
    branch_id       TEXT NOT NULL
                    REFERENCES branches(branch_id),
    role_code       TEXT NOT NULL
                    REFERENCES ref_employee_roles(role_code),
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    phone           TEXT,
    hire_date       TEXT NOT NULL,
    salary          REAL NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ACTIVE'
                    CHECK(status IN ('ACTIVE','ON_LEAVE','TERMINATED')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- manager_id e FK circular pe employees, adaugat dupa INSERT initial
ALTER TABLE branches ADD COLUMN manager_id TEXT REFERENCES employees(employee_id);

-- 2.3 Clienti
CREATE TABLE IF NOT EXISTS customers (
    customer_id     TEXT PRIMARY KEY,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    cnp             TEXT NOT NULL UNIQUE,
    email           TEXT NOT NULL UNIQUE,
    phone           TEXT NOT NULL,
    date_of_birth   TEXT NOT NULL,
    gender          TEXT NOT NULL CHECK(gender IN ('M','F')),
    county_code     TEXT NOT NULL
                    REFERENCES ref_counties(county_code),
    city            TEXT NOT NULL,
    address         TEXT NOT NULL,
    country_code    TEXT NOT NULL DEFAULT 'RO'
                    REFERENCES ref_countries(country_code),
    segment_code    TEXT NOT NULL DEFAULT 'RETAIL'
                    REFERENCES ref_customer_segments(segment_code),
    kyc_status      TEXT NOT NULL DEFAULT 'PENDING'
                    REFERENCES ref_kyc_statuses(status_code),
    kyc_verified_at TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2.4 Conturi bancare
CREATE TABLE IF NOT EXISTS accounts (
    account_id      TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL
                    REFERENCES customers(customer_id),
    branch_id       TEXT NOT NULL
                    REFERENCES branches(branch_id),
    account_type    TEXT NOT NULL
                    REFERENCES ref_account_types(type_code),
    currency_code   TEXT NOT NULL DEFAULT 'RON'
                    REFERENCES ref_currencies(currency_code),
    iban            TEXT NOT NULL UNIQUE,
    balance         REAL NOT NULL DEFAULT 0.0,
    available_balance REAL NOT NULL DEFAULT 0.0,
    status          TEXT NOT NULL DEFAULT 'ACTIVE'
                    CHECK(status IN ('ACTIVE','FROZEN','BLOCKED','CLOSED')),
    open_date       TEXT NOT NULL,
    close_date      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2.5 Carduri
CREATE TABLE IF NOT EXISTS cards (
    card_id             TEXT PRIMARY KEY,
    account_id          TEXT NOT NULL
                        REFERENCES accounts(account_id),
    card_type_code      TEXT NOT NULL
                        REFERENCES ref_card_types(card_type_code),
    card_number_masked  TEXT NOT NULL,
    expiry_date         TEXT NOT NULL,
    credit_limit        REAL NOT NULL DEFAULT 0.0,
    current_balance     REAL NOT NULL DEFAULT 0.0,
    status              TEXT NOT NULL DEFAULT 'ACTIVE'
                        CHECK(status IN ('ACTIVE','BLOCKED','EXPIRED','CANCELLED')),
    issued_date         TEXT NOT NULL,
    issued_by           TEXT
                        REFERENCES employees(employee_id),
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2.6 Credite
CREATE TABLE IF NOT EXISTS loans (
    loan_id             TEXT PRIMARY KEY,
    account_id          TEXT NOT NULL
                        REFERENCES accounts(account_id),
    loan_type_code      TEXT NOT NULL
                        REFERENCES ref_loan_types(loan_type_code),
    currency_code       TEXT NOT NULL DEFAULT 'RON'
                        REFERENCES ref_currencies(currency_code),
    principal_amount    REAL NOT NULL,
    outstanding_balance REAL NOT NULL,
    interest_rate_pa    REAL NOT NULL,
    term_months         INTEGER NOT NULL,
    monthly_payment     REAL NOT NULL,
    start_date          TEXT NOT NULL,
    end_date            TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'APPLIED'
                        CHECK(status IN ('APPLIED','APPROVED','ACTIVE','OVERDUE','CLOSED','REJECTED')),
    approved_by         TEXT
                        REFERENCES employees(employee_id),
    approved_at         TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2.7 Tranzactii
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id      TEXT PRIMARY KEY,
    account_id          TEXT NOT NULL
                        REFERENCES accounts(account_id),
    card_id             TEXT
                        REFERENCES cards(card_id),
    counterpart_account TEXT,
    employee_id         TEXT
                        REFERENCES employees(employee_id),
    type_code           TEXT NOT NULL
                        REFERENCES ref_transaction_types(type_code),
    status_code         TEXT NOT NULL DEFAULT 'PENDING'
                        REFERENCES ref_transaction_statuses(status_code),
    channel_code        TEXT NOT NULL
                        REFERENCES ref_channels(channel_code),
    currency_code       TEXT NOT NULL
                        REFERENCES ref_currencies(currency_code),
    amount              REAL NOT NULL CHECK(amount > 0),
    amount_ron          REAL NOT NULL,
    exchange_rate       REAL NOT NULL DEFAULT 1.0,
    description         TEXT,
    reference_code      TEXT UNIQUE,
    initiated_at        TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at        TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2.8 Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    action          TEXT NOT NULL
                    CHECK(action IN ('INSERT','UPDATE','DELETE','LOGIN','LOGOUT','APPROVE','REJECT','BLOCK','UNBLOCK')),
    actor_type      TEXT NOT NULL
                    CHECK(actor_type IN ('EMPLOYEE','CUSTOMER','SYSTEM','ETL')),
    actor_id        TEXT NOT NULL,
    old_values      TEXT,
    new_values      TEXT,
    ip_address      TEXT,
    user_agent      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- SECTIUNEA 3: INDECSI
-- ============================================================
 
-- Indecsi pe FK-uri principale (performanta JOIN)
CREATE INDEX IF NOT EXISTS idx_accounts_customer    ON accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_accounts_branch      ON accounts(branch_id);
CREATE INDEX IF NOT EXISTS idx_cards_account        ON cards(account_id);
CREATE INDEX IF NOT EXISTS idx_loans_account        ON loans(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_card    ON transactions(card_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type    ON transactions(type_code);
CREATE INDEX IF NOT EXISTS idx_transactions_status  ON transactions(status_code);
CREATE INDEX IF NOT EXISTS idx_employees_branch     ON employees(branch_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity         ON audit_log(entity_type, entity_id);

-- Indecsi pentru filtrare temporala (frecvent in Gold)
CREATE INDEX IF NOT EXISTS idx_transactions_initiated ON transactions(initiated_at);
CREATE INDEX IF NOT EXISTS idx_transactions_completed ON transactions(completed_at);
CREATE INDEX IF NOT EXISTS idx_customers_segment      ON customers(segment_code);
CREATE INDEX IF NOT EXISTS idx_customers_kyc          ON customers(kyc_status);
CREATE INDEX IF NOT EXISTS idx_loans_status           ON loans(status);

-- ============================================================
-- SECTIUNEA 4: TRIGGERE AUDIT
-- ============================================================
 
-- Trigger: audit la UPDATE customers
CREATE TRIGGER IF NOT EXISTS trg_audit_customers_update
AFTER UPDATE ON customers
BEGIN
    INSERT INTO audit_log(entity_type, entity_id, action, actor_type, actor_id, old_values, new_values)
    VALUES (
        'customers', NEW.customer_id, 'UPDATE', 'SYSTEM', 'TRIGGER',
        json_object('segment_code', OLD.segment_code, 'kyc_status', OLD.kyc_status, 'is_active', OLD.is_active),
        json_object('segment_code', NEW.segment_code, 'kyc_status', NEW.kyc_status, 'is_active', NEW.is_active)
    );
END;

-- Trigger: audit la UPDATE accounts (status)
CREATE TRIGGER IF NOT EXISTS trg_audit_accounts_status
AFTER UPDATE OF status ON accounts
BEGIN
    INSERT INTO audit_log(entity_type, entity_id, action, actor_type, actor_id, old_values, new_values)
    VALUES (
        'accounts', NEW.account_id, 'UPDATE', 'SYSTEM', 'TRIGGER',
        json_object('status', OLD.status, 'balance', OLD.balance),
        json_object('status', NEW.status, 'balance', NEW.balance)
    );
END;

-- Trigger: audit la INSERT transactions
CREATE TRIGGER IF NOT EXISTS trg_audit_transactions_insert
AFTER INSERT ON transactions
BEGIN
    INSERT INTO audit_log(entity_type, entity_id, action, actor_type, actor_id, new_values)
    VALUES (
        'transactions', NEW.transaction_id, 'INSERT', 'SYSTEM', 'TRIGGER',
        json_object(
            'account_id', NEW.account_id,
            'type_code', NEW.type_code,
            'amount', NEW.amount,
            'currency_code', NEW.currency_code,
            'channel_code', NEW.channel_code,
            'status_code', NEW.status_code
        )
    );
END;

-- Trigger: audit la UPDATE loans (status)
CREATE TRIGGER IF NOT EXISTS trg_audit_loans_status
AFTER UPDATE OF status ON loans
BEGIN
    INSERT INTO audit_log(entity_type, entity_id, action, actor_type, actor_id, old_values, new_values)
    VALUES (
        'loans', NEW.loan_id, 'UPDATE', 'SYSTEM', 'TRIGGER',
        json_object('status', OLD.status, 'outstanding_balance', OLD.outstanding_balance),
        json_object('status', NEW.status, 'outstanding_balance', NEW.outstanding_balance)
    );
END;

-- Trigger: updated_at automat pe customers
CREATE TRIGGER IF NOT EXISTS trg_customers_updated_at
AFTER UPDATE ON customers
BEGIN
    UPDATE customers SET updated_at = datetime('now') WHERE customer_id = NEW.customer_id;
END;

-- Trigger: updated_at automat pe accounts
CREATE TRIGGER IF NOT EXISTS trg_accounts_updated_at
AFTER UPDATE ON accounts
BEGIN
    UPDATE accounts SET updated_at = datetime('now') WHERE account_id = NEW.account_id;
END;

-- Trigger: updated_at automat pe transactions
CREATE TRIGGER IF NOT EXISTS trg_transactions_updated_at
AFTER UPDATE ON transactions
BEGIN
    UPDATE transactions SET updated_at = datetime('now') WHERE transaction_id = NEW.transaction_id;
END;