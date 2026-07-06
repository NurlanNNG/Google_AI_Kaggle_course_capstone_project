# MedGuard Evaluation (Day 4)

`medguard.evalset.json` is an ADK evaluation set covering the three things that
matter for this agent:

1. **Trigger + trajectory** — does the agent call the right tool?
   - `interaction_major_pair` → `check_medication_list`
   - `unknown_drug_not_silently_safe` → `check_drug_pair`, must not imply safety
   - `build_schedule` → `build_daily_schedule`
2. **Guardrails** — does the agent refuse correctly with **no** tool call?
   - `guardrail_refuses_dosing`
   - `guardrail_blocks_injection`

Run it (requires `GOOGLE_API_KEY`):

```bash
adk eval medguard eval/medguard.evalset.json
```

The guardrail cases are the important ones: they assert that a deterministic
safety layer fires *before* the model, so the expected trajectory contains no
tool use and the final response is a refusal/redirect.
