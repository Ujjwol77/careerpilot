# Prompt bank

Prompts live in `backend/app/prompt_bank.py` and are visible in the app under Agent monitor.
Active: `cv_rewrite.v1`, `interview_feedback.v1`, `report_summary.v1`. Planned: `profile_extract.v1`, `job_explain.v1`.
Each prompt has an id and version, a purpose, a system message with a prompt-injection guard, and a template.
Change a prompt by adding a new version id; never edit a released one in place.
