---
name: medication-prep-sheet
description: |
  Generates a printable, caregiver-friendly medication prep sheet from a
  medication schedule and interaction-check results. Use when the user asks to
  "summarise my medications", "make a sheet for my doctor/pharmacist", "print a
  schedule", "create a caregiver handoff", or prepare medications for the week.
  Do NOT use for checking interactions (use the MCP interaction tools), for
  dosing decisions, or for medical diagnosis.
---

# Medication Prep Sheet

This skill crystallises a repeatable formatting task: turning MedGuard's
structured outputs (a daily schedule + interaction findings) into a single,
human-readable sheet a patient or caregiver can print and carry to an
appointment.

## When to trigger
Trigger after a schedule has been built and/or interactions have been checked,
when the user wants a **document** rather than a chat answer.

## How to use (progressive disclosure)
1. Read `references/prep_sheet_guidelines.md` for the content rules (what must
   always appear: the professional-review disclaimer, the "bring this to your
   pharmacist" footer, no dosing recommendations).
2. Call `scripts/build_prep_sheet.py` with a JSON payload on stdin containing:
   - `patient_label` (a non-identifying label like "Mum" or "My meds" — never a
     full legal name or ID)
   - `schedule` (the output of `build_daily_schedule`)
   - `interactions` (the output of `check_medication_list`)
   The script renders `assets/prep_sheet_template.md` and prints the finished
   Markdown to stdout.
3. Return the rendered sheet to the user.

## Safety
- The script **never** invents dosing or medical advice; it only reformats data
  that already passed MedGuard's guardrails.
- Use a minimal, non-identifying `patient_label` to keep personal data small
  (privacy-by-design, per the Concierge track).
