# CareerPilot sample CVs: worst to best

Ten fictional CVs for testing CareerPilot, ordered from worst (01) to best (10). They cover the three roles the app knows: Data Analyst, Cybersecurity Analyst and Software Developer. Five are PDF and five are DOCX, so both upload paths are exercised.

All names, emails (example.com), phone numbers and employers are invented; employers are marked "(fictional)" where they appear in full.

## Results from CareerPilot

Measured on 16/11/2026 by uploading each file to a fresh account, with the 45 sample jobs, the mock LLM and local similarity (no Gemini or Adzuna). The ATS score uses the CV review's 12 checks against the user's best-matching job. With live Adzuna jobs or Gemini embeddings the match score will differ; the ATS score changes only through the job-keyword and job-title checks.

| # | File | Role | Tier | ATS score | Checks passed | Skills found | Years | Top role fit | Best match score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | cv_01_worst_data.docx | Data Analyst | Worst | 32 | 1/10 | 2 | 2 | Data Analyst 28% | 61.3 |
| 02 | cv_02_very_weak_software.pdf | Software Developer | Very weak | 40 | 5/12 | 4 | 1 | Software Developer 4% | 29.3 |
| 03 | cv_03_weak_cyber.docx | Cybersecurity Analyst | Weak | 50 | 4/10 | 6 | 2 | Cybersecurity Analyst 30% | 40.5 |
| 04 | cv_04_below_average_data.pdf | Data Analyst | Below average | 56 | 6/12 | 5 | 3.8 | Data Analyst 47% | 63.1 |
| 05 | cv_05_average_software.docx | Software Developer | Average | 65 | 6/12 | 15 | 4 | Software Developer 70% | 80 |
| 06 | cv_06_fair_cyber.pdf | Cybersecurity Analyst | Fair | 66 | 7/12 | 13 | 2 | Cybersecurity Analyst 58% | 51.9 |
| 07 | cv_07_good_data.docx | Data Analyst | Good | 90 | 10/12 | 13 | 2 | Data Analyst 89% | 100 |
| 08 | cv_08_very_good_software.pdf | Software Developer | Very good | 92 | 10/12 | 21 | 3 | Software Developer 98% | 93.9 |
| 09 | cv_09_excellent_cyber.docx | Cybersecurity Analyst | Excellent | 100 | 12/12 | 15 | 3 | Cybersecurity Analyst 88% | 97.9 |
| 10 | cv_10_best_data.pdf | Data Analyst | Best | 100 | 12/12 | 18 | 4 | Data Analyst 100% | 100 |

The best match score measures how well a CV fits a job, not how well it is written, so a short, weak CV can still score well against a broad advert (01 matches 61 because local word overlap is generous to short texts). The ATS score is the column that ranks writing quality.

## What makes each one weaker or stronger

- **01 Worst** (cv_01_worst_data.docx): No headings, no bullets, no summary, lower-case casual writing, 73 words, "responsible for", only 2 skills detected. Only just passes the is-it-a-CV check (email + one date range).
- **02 Very weak** (cv_02_very_weak_software.pdf): Headings for Experience, Education and Skills only; duty-only bullets with no numbers ("Responsible for", "Worked on", "Helped with"); no phone, no summary, 67 words.
- **03 Weak** (cv_03_weak_cyber.docx): Experience written as one paragraph with no bullets; vague objective; passive phrases; skills hidden in a sentence instead of a Skills heading; no certifications or SIEM.
- **04 Below average** (cv_04_below_average_data.pdf): Clean headings and bullets, but every bullet is a duty with no numbers, "Responsible for" and "Helped", a one-line summary and only 88 words.
- **05 Average** (cv_05_average_software.docx): Good structure, projects and a long skills list, but bullets show tasks rather than results (no numbers), "Worked on" phrasing, and 199 words.
- **06 Fair** (cv_06_fair_cyber.pdf): Relevant service-desk experience with some numbers (30 tickets a day, 40 laptops) and a home lab, but few action verbs, "Responsible for", and no SIEM or incident response results.
- **07 Good** (cv_07_good_data.docx): Quantified bullets (45 stores, 2 days to 3 hours, 1.2 million rows, 9% less waste), strong data analyst keywords and a certificate; still one "Responsible for" bullet and just under 250 words.
- **08 Very good** (cv_08_very_good_software.pdf): Results in nearly every bullet (50,000 updates a day, 48% to 85% coverage), full developer stack, CI/CD, AWS certificate, open-source work; the summary says "Software Developer" rather than the advert's exact title.
- **09 Excellent** (cv_09_excellent_cyber.docx): SOC experience with measurable outcomes (60+ alerts a shift, 92% closure rate, 30% fewer false positives), Splunk SIEM, MITRE ATT&CK, Security+, detection lab and CTF result.
- **10 Best** (cv_10_best_data.pdf): Every check passes: target title in the summary, 10 results-focused bullets with numbers ($1.2M saved, 5 days to 1), all core data analyst skills, two certifications, projects and relevant units.

## Rebuilding the files

`make_cvs.py` holds the text of all ten CVs and writes them with python-docx. Each PDF is made the way a real user makes one: the Word version is saved as PDF with LibreOffice (if installed), giving 20-28 KB files with embedded fonts. Without LibreOffice it falls back to ReportLab, whose 2-3 KB PDFs read fine in CareerPilot but are rejected by the APILayer resume parser as "File too small".

```
cd backend
python samples/cv_set/make_cvs.py
```

