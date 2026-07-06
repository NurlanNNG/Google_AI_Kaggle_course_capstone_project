# Submission checklist — do these before 11:59 PM PT, July 6, 2026

The code, README, writeup, and video script are all done. These final steps only
**you** can do (they need your accounts). Budget ~30–45 minutes.

## 1. Put the code on GitHub (public)
```bash
cd medguard
git init
git add .
git commit -m "MedGuard: medication-safety concierge agent (Kaggle capstone)"
# create an empty public repo on github.com first, then:
git remote add origin https://github.com/<your-username>/medguard.git
git branch -M main
git push -u origin main
```
✅ Check: the repo is **public**, the README renders, and **no `.env`/API key** is
committed (the included `.gitignore` already excludes `.env`).

## 2. Record & upload the video (YouTube, ≤ 5 min)
- Follow `VIDEO_SCRIPT.md`. The easiest reliable demo is
  `python -m scripts.demo_offline` (needs no API key).
- Upload to **YouTube**. Copy the video URL.

## 3. Make a cover image
- A cover image is **required**. Use `docs/architecture_cover.png` (included) or a
  screenshot of the offline demo output.

## 4. Create the Kaggle Writeup
- On the competition page click **New Writeup**.
- Title: **MedGuard: a safety-first medication concierge agent**
- Paste the body from `KAGGLE_WRITEUP.md` (it's 1,461 words — under the 2,500 limit).
- **Select the Track: Concierge Agents** (required to submit).

## 5. Attach the required assets to the Writeup
- **Media Gallery:** upload the cover image + attach the YouTube video link.
- **Project Link:** paste your **GitHub repo URL** (a public code link satisfies
  this requirement; the README has full setup instructions).

## 6. Submit
- Click **Submit** (top-right of the saved Writeup).
- ⚠️ A saved *draft* is **not** a submission — make sure you see it confirmed as
  submitted before the deadline.

---

### Concepts you're claiming (need ≥ 3; you have 5)
- Multi-agent system (ADK) — code
- MCP Server — code
- Agent Skills — code
- Security features — code
- Deployability — Dockerfile / video

### 60-second sanity check before you submit
```bash
PYTHONPATH=. pytest -q            # expect: 26 passed
PYTHONPATH=. python -m scripts.demo_offline   # prints the full walkthrough
```
