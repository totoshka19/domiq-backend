---
name: migrate
description: Create and apply an Alembic migration for database schema changes
disable-model-invocation: true
argument-hint: <migration description in English>
---

Create and apply an Alembic migration: `$ARGUMENTS`

## Steps

1. Run the autogenerate command:
```bash
alembic revision --autogenerate -m "$ARGUMENTS"
```

2. Show me the full content of the generated migration file from `migrations/versions/`.

3. Review the migration together:
   - Check that `upgrade()` contains the correct changes
   - Check that `downgrade()` correctly reverts them
   - Warn me if anything looks wrong or unexpected

4. Ask: "Apply this migration with `alembic upgrade head`?"

5. If I confirm — run:
```bash
alembic upgrade head
```

6. Confirm success by running:
```bash
alembic current
```
and show me the output.

## Rules
- Never apply the migration without showing it to me first
- If `autogenerate` detects no changes, tell me clearly: "No schema changes detected"
- If there's an error, show the full error message and suggest how to fix it
