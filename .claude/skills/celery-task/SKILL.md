---
name: celery-task
description: Add a new Celery background task to notifications/tasks.py. Use when implementing async processing like sending emails, uploading files, or sending notifications.
disable-model-invocation: true
argument-hint: <task description>
---

Add a new Celery task: `$ARGUMENTS`

## Steps

1. Add the task to `app/notifications/tasks.py`:

```python
from core.celery_app import celery
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_name(self, param1: str, param2: int) -> dict:
    """
    Task description: $ARGUMENTS
    """
    try:
        # task logic here
        logger.info(f"Task started: param1={param1}")

        # ... do the work ...

        logger.info("Task completed successfully")
        return {"status": "success"}

    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc)
```

2. Show me where to call this task (which endpoint/service should trigger it):
```python
# In the relevant service.py:
from app.notifications.tasks import task_name

# Call async (fire and forget):
task_name.delay(param1="value", param2=42)

# Call with delay:
task_name.apply_async(args=[param1], countdown=60)
```

3. If the task needs configuration (email credentials, S3 keys, etc.) — check `core/config.py` and add any missing `Settings` fields with a note to update `.env.example`.

4. Show me the final implementation.

## Task types for Domiq:
- `upload_photo_to_s3` — upload listing photo to S3
- `send_email_notification` — email on new chat message
- `notify_admin_new_listing` — alert admin about listing pending moderation
- `process_listing_photos` — resize/optimize photos after upload
