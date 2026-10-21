import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app import crud

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def run_sla_check_job():
    logger.info("Executing periodic SLA & Overdue check...")
    db = SessionLocal()
    try:
        crud.check_sla_and_generate_alerts(db)
    except Exception as e:
        logger.error(f"Error running SLA check job: {e}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        # Run check every 60 seconds
        scheduler.add_job(run_sla_check_job, 'interval', seconds=60, id='sla_check_job', replace_existing=True)
        scheduler.start()
        logger.info("CareLoop SLA Automation Scheduler started successfully.")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("CareLoop SLA Automation Scheduler stopped.")
