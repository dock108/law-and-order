"""Main Celery application instance configuration."""

from celery import Celery
from celery.schedules import crontab

# from pi_auto_api.config import settings # Settings are loaded via config_from_object

# Define the Celery application instance
app = Celery("pi_auto_api")

# Load configuration from pi_auto_api.config
app.config_from_object("pi_auto_api.config")

# Autodiscover tasks from the pi_auto_api.tasks package
# The tasks.__init__.py imports all individual task modules.
app.autodiscover_tasks(["pi_auto_api.tasks"])

# List of modules where tasks are defined
# TASK_MODULES = [
#     "pi_auto_api.tasks.billing",
#     "pi_auto_api.tasks.damages",
#     "pi_auto_api.tasks.demand",
#     "pi_auto_api.tasks.docusign",
#     "pi_auto_api.tasks.general",
#     "pi_auto_api.tasks.intake",
#     "pi_auto_api.tasks.medical_records",
# ]

# Autodiscover tasks from the specified modules
# app.autodiscover_tasks(TASK_MODULES)
# Tasks are registered when their respective modules are imported
# by pi_auto_api.tasks.__init__.py

# Default queue
app.conf.task_default_queue = "default"

# Configure Beat schedule
# Note: Using 2:00 AM Eastern Time (America/New_York)
app.conf.beat_schedule = {
    "nightly-medical-record-request": {
        "task": "send_medical_record_requests",
        "schedule": crontab(hour=2, minute=0),
    },
    # Add nightly demand package check here later
    "nightly-demand-package-check": {
        "task": "check_and_build_demand",
        "schedule": crontab(hour=3, minute=0),  # e.g., 3 AM ET
        # Optional: "args": (arg1, arg2)
    },
}

if __name__ == "__main__":
    # This allows running the worker directly using
    # `python -m pi_auto_api.celery_app worker`
    # Note: Usually, you run celery via the `celery` command-line tool.
    app.worker_main()
