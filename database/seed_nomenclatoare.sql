-- ============================================================
-- SEED DATE NOMENCLATOARE
-- Toate datele sunt statice / semi-statice
-- Rulat o singura data la initializarea bazei de date
-- ============================================================

PRAGMA foreign_keys = ON;

-- ────────────────────────────────────────
-- ref_countries
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_countries VALUES
('RO','Romania','Romania',1,1,'LOW',1,datetime('now')),
('DE','Germania','Germany',1,1,'LOW',1,datetime('now')),
('FR','Franta','France',1,1,'LOW',1,datetime('now')),
('IT','Italia','Italy',1,1,'LOW',1,datetime('now')),
('ES','Spania','Spain',1,1,'LOW',1,datetime('now')),
('AT','Austria','Austria',1,1,'LOW',1,datetime('now')),
('NL','Olanda','Netherlands',1,1,'LOW',1,datetime('now')),
('BE','Belgia','Belgium',1,1,'LOW',1,datetime('now')),
('PL','Polonia','Poland',1,1,'LOW',1,datetime('now')),
('HU','Ungaria','Hungary',1,1,'LOW',1,datetime('now')),
('BG','Bulgaria','Bulgaria',1,1,'LOW',1,datetime('now')),
('GB','Regatul Unit','United Kingdom',0,1,'LOW',1,datetime('now')),
('CH','Elvetia','Switzerland',0,1,'LOW',1,datetime('now')),
('US','Statele Unite','United States',0,0,'LOW',1,datetime('now')),
('MD','Republica Moldova','Moldova',0,0,'MEDIUM',1,datetime('now')),
('UA','Ucraina','Ukraine',0,0,'MEDIUM',1,datetime('now')),
('TR','Turcia','Turkey',0,0,'MEDIUM',1,datetime('now')),
('RU','Rusia','Russia',0,0,'HIGH',1,datetime('now')),
('CN','China','China',0,0,'MEDIUM',1,datetime('now')),
('AE','Emiratele Arabe','United Arab Emirates',0,0,'MEDIUM',1,datetime('now'));

-- ────────────────────────────────────────
-- ref_counties (toate judetele + Bucuresti)
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_counties VALUES
('AB','Alba','CENTRU','RO',1),
('AR','Arad','VEST','RO',1),
('AG','Arges','SUD','RO',1),
('BC','Bacau','NORD-EST','RO',1),
('BH','Bihor','NORD-VEST','RO',1),
('BN','Bistrita-Nasaud','NORD-VEST','RO',1),
('BT','Botosani','NORD-EST','RO',1),
('BV','Brasov','CENTRU','RO',1),
('BR','Braila','SUD-EST','RO',1),
('B','Bucuresti','BUCURESTI-ILFOV','RO',1),
('BZ','Buzau','SUD-EST','RO',1),
('CS','Caras-Severin','VEST','RO',1),
('CL','Calarasi','SUD','RO',1),
('CJ','Cluj','NORD-VEST','RO',1),
('CT','Constanta','SUD-EST','RO',1),
('CV','Covasna','CENTRU','RO',1),
('DB','Dambovita','SUD','RO',1),
('DJ','Dolj','SUD-VEST','RO',1),
('GL','Galati','SUD-EST','RO',1),
('GR','Giurgiu','SUD','RO',1),
('GJ','Gorj','SUD-VEST','RO',1),
('HR','Harghita','CENTRU','RO',1),
('HD','Hunedoara','VEST','RO',1),
('IL','Ialomita','SUD','RO',1),
('IS','Iasi','NORD-EST','RO',1),
('IF','Ilfov','BUCURESTI-ILFOV','RO',1),
('MM','Maramures','NORD-VEST','RO',1),
('MH','Mehedinti','SUD-VEST','RO',1),
('MS','Mures','CENTRU','RO',1),
('NT','Neamt','NORD-EST','RO',1),
('OT','Olt','SUD-VEST','RO',1),
('PH','Prahova','SUD','RO',1),
('SM','Satu Mare','NORD-VEST','RO',1),
('SJ','Salaj','NORD-VEST','RO',1),
('SB','Sibiu','CENTRU','RO',1),
('SV','Suceava','NORD-EST','RO',1),
('TR','Teleorman','SUD','RO',1),
('TM','Timis','VEST','RO',1),
('TL','Tulcea','SUD-EST','RO',1),
('VS','Vaslui','NORD-EST','RO',1),
('VL','Valcea','SUD-VEST','RO',1),
('VN','Vrancea','SUD-EST','RO',1);

-- ────────────────────────────────────────
-- ref_regions
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_regions VALUES
('NORD-VEST','Nord-Vest','CJ',6),
('CENTRU','Centru','BV',6),
('NORD-EST','Nord-Est','IS',6),
('SUD-EST','Sud-Est','CT',6),
('SUD','Sud - Muntenia','PH',8),
('SUD-VEST','Sud-Vest Oltenia','DJ',5),
('VEST','Vest','TM',4),
('BUCURESTI-ILFOV','Bucuresti-Ilfov','B',2);

-- ────────────────────────────────────────
-- ref_currencies
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_currencies VALUES
('RON','Leu romanesc','lei',2,1,1.0,1,datetime('now')),
('EUR','Euro','€',2,0,4.97,1,datetime('now')),
('USD','Dolar american','$',2,0,4.61,1,datetime('now')),
('GBP','Lira sterlina','£',2,0,5.83,1,datetime('now')),
('CHF','Franc elvetian','CHF',2,0,5.10,1,datetime('now')),
('HUF','Forint maghiar','Ft',0,0,0.0126,1,datetime('now'));

-- ────────────────────────────────────────
-- ref_transaction_types
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_transaction_types VALUES
('DEBIT','Debit cont','OUT',1,0,'Retragere / debitare directa din cont'),
('CREDIT','Credit cont','IN',1,0,'Depunere / creditare directa in cont'),
('TRANSFER_OUT','Transfer trimis','OUT',1,0,'Transfer catre alt cont / IBAN'),
('TRANSFER_IN','Transfer primit','IN',1,0,'Transfer primit de la alt cont / IBAN'),
('ATM_WITHDRAWAL','Retragere ATM','OUT',1,1,'Retragere numerar la ATM'),
('ATM_DEPOSIT','Depunere ATM','IN',1,1,'Depunere numerar la ATM'),
('POS','Plata POS','OUT',1,1,'Plata la terminal POS'),
('PAYMENT','Plata factura','OUT',1,0,'Plata utilitati / servicii'),
('DIRECT_DEBIT','Debit direct','OUT',1,0,'Debit direct autorizat'),
('FEE','Comision bancar','OUT',1,0,'Comision / taxa bancara'),
('INTEREST','Dobanda creditata','IN',1,0,'Dobanda creditata la cont de economii'),
('LOAN_DISBURSEMENT','Tragere credit','IN',1,0,'Suma trasa din credit aprobat'),
('LOAN_REPAYMENT','Rata credit','OUT',1,0,'Plata rata lunara credit');

-- ────────────────────────────────────────
-- ref_transaction_statuses
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_transaction_statuses VALUES
('PENDING','In procesare',0,1,'Tranzactie initiata, in curs de procesare'),
('COMPLETED','Finalizata',1,0,'Tranzactie procesata cu succes'),
('FAILED','Esuata',1,0,'Procesare esuata: fonduri insuficiente, limita depasita etc.'),
('REVERSED','Anulata',1,0,'Tranzactie completata, ulterior anulata / reversata'),
('ON_HOLD','In asteptare',0,0,'Retinuta pentru verificare manuala sau AML');

-- ────────────────────────────────────────
-- ref_customer_segments
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_customer_segments VALUES
('RETAIL','Retail (persoane fizice)',0,0,0,'Clienti persoane fizice cu produse standard'),
('PREMIUM','Premium / Private Banking',50000,1,1,'Clienti cu active semnificative, servicii personalizate'),
('SME','IMM - Intreprinderi Mici si Mijlocii',10000,0,1,'Persoane juridice cu cifra de afaceri sub 50M EUR'),
('CORPORATE','Corporate',100000,1,1,'Companii mari, relatii comerciale complexe');

-- ────────────────────────────────────────
-- ref_account_types
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_account_types VALUES
('CURRENT','Cont curent',1,1,0,0.0,'Cont principal pentru tranzactii zilnice, permite overdraft'),
('SAVINGS','Cont de economii',0,1,100,3.5,'Cont de economii cu dobanda, retrageri limitate'),
('DEPOSIT','Depozit la termen',0,1,500,5.25,'Depozit blocat pe termen fix, dobanda superioara'),
('LOAN_ACC','Cont de credit',0,0,0,0.0,'Cont asociat unui credit, gestioneaza tragerile si rambursarile');

-- ────────────────────────────────────────
-- ref_loan_types
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_loan_types VALUES
('MORTGAGE','Credit ipotecar',80.0,5.5,360,1,'Credit imobiliar garantat cu proprietatea'),
('PERSONAL','Credit de nevoi personale',NULL,9.9,84,0,'Credit fara garantii, suma mica-medie'),
('AUTO','Credit auto',80.0,7.5,72,1,'Credit pentru achizitie autovehicul, garantat cu vehiculul'),
('OVERDRAFT','Overdraft cont curent',NULL,18.0,12,0,'Facilitate de descoperit de cont, reinnoibila anual'),
('SME_WORKING','Credit capital de lucru IMM',NULL,8.5,36,0,'Finantare capital de lucru pentru IMM-uri'),
('SME_INVEST','Credit investitii IMM',70.0,7.0,120,1,'Finantare investitii pentru IMM-uri, garantat');

-- ────────────────────────────────────────
-- ref_card_types
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_card_types VALUES
('DEBIT_VISA','Card debit Visa','VISA',0,1,0,'Card debit standard, acces direct la contul curent'),
('DEBIT_MC','Card debit Mastercard','MASTERCARD',0,1,0,'Card debit standard, acces direct la contul curent'),
('CREDIT_VISA','Card credit Visa','VISA',1,1,120,'Card credit cu limita, perioada de gratie 30 zile'),
('CREDIT_MC','Card credit Mastercard','MASTERCARD',1,1,120,'Card credit cu limita, perioada de gratie 30 zile'),
('PREPAID_VISA','Card prepaid Visa','VISA',0,1,0,'Card prepaid reincarcat, fara cont bancar asociat'),
('VIRTUAL_MC','Card virtual Mastercard','MASTERCARD',0,0,0,'Card exclusiv online, generat instant');

-- ────────────────────────────────────────
-- ref_channels
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_channels VALUES
('ATM','Bancomat / ATM',5000,10000,1,1,'Retrageri si depuneri numerar, interogare sold'),
('BRANCH','Ghiseu sucursala',NULL,NULL,0,1,'Tranzactii la ghiseul bancii, asistate de angajat'),
('ONLINE','Internet banking',50000,100000,0,1,'Platforma web de internet banking'),
('MOBILE','Mobile banking',20000,50000,0,1,'Aplicatie mobila iOS / Android'),
('POS','Terminal POS',10000,20000,1,1,'Plati la comercianti prin card'),
('DIRECT_DEBIT','Debit direct',5000,NULL,0,1,'Plati automate recurente autorizate'),
('API','Integrare API',NULL,NULL,0,1,'Tranzactii initiate prin API (B2B, fintech)');

-- ────────────────────────────────────────
-- ref_risk_bands
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_risk_bands VALUES
('LOW','Risc scazut',0,25,1,0,'MONTHLY'),
('MEDIUM','Risc mediu',26,60,0,0,'WEEKLY'),
('HIGH','Risc ridicat',61,85,0,0,'DAILY'),
('CRITICAL','Risc critic',86,100,0,1,'DAILY');

-- ────────────────────────────────────────
-- ref_kyc_statuses
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_kyc_statuses VALUES
('PENDING','In curs de verificare',1,0,1,'Documente depuse, in asteptarea verificarii'),
('VERIFIED','Verificat',0,0,1,'Identitate confirmata, acces complet la produse'),
('FLAGGED','Semnalat pentru revizuire',1,1,1,'Suspiciune activitate neobisnuita, sub monitorizare'),
('BLOCKED','Blocat',1,1,0,'Blocat complet: decizie legala sau AML confirmat');

-- ────────────────────────────────────────
-- ref_employee_roles
-- ────────────────────────────────────────
INSERT OR IGNORE INTO ref_employee_roles VALUES
('TELLER','Casier / Operator ghiseu',0,NULL,0,0,'Procesare tranzactii la ghiseu, depuneri, retrageri'),
('ADVISOR','Consilier bancar',1,50000,0,1,'Vanzare produse, aprobare credite mici'),
('MANAGER','Manager sucursala',1,500000,1,1,'Responsabil sucursala, aprobare credite mari'),
('ANALYST','Analist risc / date',0,NULL,0,1,'Analiza date, rapoarte, fara acces operational'),
('ADMIN','Administrator sistem',0,NULL,1,1,'Acces complet la configuratia sistemului');

-- ────────────────────────────────────────
-- Verificare integritate seed
-- ────────────────────────────────────────
SELECT 'ref_countries'           AS tabel, COUNT(*) AS randuri FROM ref_countries
UNION ALL SELECT 'ref_counties',            COUNT(*) FROM ref_counties
UNION ALL SELECT 'ref_regions',             COUNT(*) FROM ref_regions
UNION ALL SELECT 'ref_currencies',          COUNT(*) FROM ref_currencies
UNION ALL SELECT 'ref_transaction_types',   COUNT(*) FROM ref_transaction_types
UNION ALL SELECT 'ref_transaction_statuses',COUNT(*) FROM ref_transaction_statuses
UNION ALL SELECT 'ref_customer_segments',   COUNT(*) FROM ref_customer_segments
UNION ALL SELECT 'ref_account_types',       COUNT(*) FROM ref_account_types
UNION ALL SELECT 'ref_loan_types',          COUNT(*) FROM ref_loan_types
UNION ALL SELECT 'ref_card_types',          COUNT(*) FROM ref_card_types
UNION ALL SELECT 'ref_channels',            COUNT(*) FROM ref_channels
UNION ALL SELECT 'ref_risk_bands',          COUNT(*) FROM ref_risk_bands
UNION ALL SELECT 'ref_kyc_statuses',        COUNT(*) FROM ref_kyc_statuses
UNION ALL SELECT 'ref_employee_roles',      COUNT(*) FROM ref_employee_roles;