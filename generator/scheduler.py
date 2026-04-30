# ============================================================
# SCHEDULER.PY — flux continuu de date noi
# Ruleaza dupa generarea initiala, adauga tranzactii periodic
# ============================================================

import schedule
import time
from loguru import logger
from config import SCHEDULER_INTERVAL_MINUTES, SCHEDULER_BATCH_TRANSACTIONS
from generate import run_batch_generation

def job():
    logger.info(f"Scheduler: generare batch de {SCHEDULER_BATCH_TRANSACTIONS} tranzactii...")
    run_batch_generation(SCHEDULER_BATCH_TRANSACTIONS)

logger.info(f"Scheduler pornit — batch la fiecare {SCHEDULER_INTERVAL_MINUTES} minute")
logger.info("Ctrl+C pentru oprire")

schedule.every(SCHEDULER_INTERVAL_MINUTES).minutes.do(job)

# Rulam primul batch imediat
job()

while True:
    schedule.run_pending()
    time.sleep(30)