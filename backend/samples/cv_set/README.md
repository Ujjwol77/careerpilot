# CareerPilot sample CVs: worst to best

Nineteen fictional CVs for testing CareerPilot, in two sets, each ordered from worst to best:

- **Set 1 (01-10):** the three original roles (Data Analyst, Cybersecurity Analyst, Software Developer).
- **Set 2 (11-19):** one CV for each role added later (Business Analyst, Front-end Developer, Network Engineer, QA / Test Engineer, Service Desk Analyst, Data Scientist, Data Engineer, Penetration Tester, Cloud / DevOps Engineer).

The files mix PDF and DOCX, so both upload paths are exercised. All names, emails (example.com), phone numbers and employers are invented; employers are marked "(fictional)" where they appear in full.

## Results from CareerPilot

Measured on 22/11/2026 by uploading each file to a fresh account, with the 12 roles and 180 sample jobs, the mock LLM and local similarity (no Gemini or Adzuna). The ATS score uses the CV review's 12 checks against the user's best-matching job. With live Adzuna jobs or Gemini embeddings the match score will differ; the ATS score changes only through the job-keyword and job-title checks.

### Set 1: original roles

| # | File | Written for | Tier | ATS score | Checks passed | Skills found | Years | Top role fit | Best match score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | cv_01_worst_data.docx | Data Analyst | Worst | 32 | 1/10 | 2 | 2 | Data Analyst 28% | 61.3 |
| 02 | cv_02_very_weak_software.pdf | Software Developer | Very weak | 46 | 5/12 | 4 | 1 | Front-end Developer 31% | 69.1 |
| 03 | cv_03_weak_cyber.docx | Cybersecurity Analyst | Weak | 56 | 4/10 | 7 | 2 | Network Engineer 51% | 59.8 |
| 04 | cv_04_below_average_data.pdf | Data Analyst | Below average | 56 | 6/12 | 5 | 3.8 | Data Analyst 47% | 63.1 |
| 05 | cv_05_average_software.docx | Software Developer | Average | 63 | 6/12 | 15 | 4 | Front-end Developer 71% | 87.1 |
| 06 | cv_06_fair_cyber.pdf | Cybersecurity Analyst | Fair | 73 | 7/12 | 14 | 2 | Network Engineer 68% | 65.3 |
| 07 | cv_07_good_data.docx | Data Analyst | Good | 90 | 10/12 | 13 | 2 | Data Analyst 89% | 100 |
| 08 | cv_08_very_good_software.pdf | Software Developer | Very good | 92 | 10/12 | 21 | 3 | Software Developer 98% | 93.9 |
| 09 | cv_09_excellent_cyber.docx | Cybersecurity Analyst | Excellent | 100 | 12/12 | 15 | 3 | Cybersecurity Analyst 88% | 97.9 |
| 10 | cv_10_best_data.pdf | Data Analyst | Best | 100 | 12/12 | 18 | 4 | Data Analyst 100% | 100 |

### Set 2: roles added later

| # | File | Written for | Tier | ATS score | Checks passed | Skills found | Years | Top role fit | Best match score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | cv_11_very_weak_business_analyst.docx | Business Analyst | Very weak | 50 | 6/12 | 3 | 2 | Data Analyst 28% | 35.8 |
| 12 | cv_12_weak_frontend.pdf | Front-end Developer | Weak | 59 | 3/10 | 4 | 4 | Front-end Developer 56% | 86.4 |
| 13 | cv_13_below_average_network.docx | Network Engineer | Below average | 63 | 6/12 | 10 | 4.8 | Network Engineer 65% | 69.3 |
| 14 | cv_14_average_qa.pdf | QA / Test Engineer | Average | 69 | 7/12 | 10 | 2 | QA / Test Engineer 82% | 97.2 |
| 15 | cv_15_fair_service_desk.docx | Service Desk Analyst | Fair | 79 | 8/12 | 11 | 1.5 | Service Desk Analyst 88% | 100 |
| 16 | cv_16_good_data_scientist.pdf | Data Scientist | Good | 92 | 10/12 | 12 | 2 | Data Scientist 89% | 95.6 |
| 17 | cv_17_very_good_data_engineer.docx | Data Engineer | Very good | 95 | 11/12 | 18 | 3 | Data Engineer 96% | 100 |
| 18 | cv_18_excellent_pentest.pdf | Penetration Tester | Excellent | 100 | 12/12 | 14 | 3 | Penetration Tester 95% | 96.9 |
| 19 | cv_19_best_cloud_devops.docx | Cloud / DevOps Engineer | Best | 100 | 12/12 | 16 | 4 | Cloud / DevOps Engineer 95% | 100 |

In both sets the ATS score rises with writing quality (set 1: 32 to 100; set 2: 50 to 100). The best match score measures how well a CV fits a job, not how well it is written, so a short, weak CV can still score well against a broad advert. Since the 12 roles were added, some set 1 CVs fit a newer role best (the service-desk-heavy cyber CVs 03 and 06 now fit Network Engineer; the web-heavy software CVs 02 and 05 fit Front-end Developer), which is the role-fit agent working as intended. CV 11 is so thin that its best match is a data analyst advert rather than a business analyst one.

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
- **11 Very weak** (cv_11_very_weak_business_analyst.docx): A generic objective, duty-only bullets ("Responsible for", "Assisted with", "Was involved in"), no numbers, no business analysis skills (no requirements, process mapping or stakeholder work), 91 words.
- **12 Weak** (cv_12_weak_frontend.pdf): No email address, an "About me" instead of a summary, experience written as paragraphs with no bullets, and skills hidden in a sentence with no Skills heading; no responsive design, accessibility or testing.
- **13 Below average** (cv_13_below_average_network.docx): Relevant network support work and Network+, but every bullet is a duty with no numbers ("Responsible for", "Worked on", "Helped with") and only 127 words.
- **14 Average** (cv_14_average_qa.pdf): Good QA keywords (test cases, regression, UAT, Selenium, Postman, ISTQB) but bullets describe tasks rather than results and only 1 of 7 has a number.
- **15 Fair** (cv_15_fair_service_desk.docx): Entry-level but quantified (25 tickets a day, 15 new starters a month), ServiceNow, Microsoft 365 and Intune; still one "Responsible for" bullet, few action verbs and 177 words.
- **16 Good** (cv_16_good_data_scientist.pdf): Results in most bullets (18% more fraud found, 70% of emails routed), machine learning, NLP and statistics; just under 250 words and the summary does not use the advert's exact title.
- **17 Very good** (cv_17_very_good_data_engineer.docx): Strong, quantified data engineering (40 million rows a day, 6 hours to 45 minutes) with Airflow, dbt, Snowflake, Spark and Terraform; only slightly short at 235 words.
- **18 Excellent** (cv_18_excellent_pentest.pdf): Every check passes: 40 tests led, 12 critical findings, OSCP, Burp Suite, Metasploit, report writing rated 4.8 of 5, Hack The Box ranking and mentoring.
- **19 Best** (cv_19_best_cloud_devops.docx): Every check passes and the most complete profile: Terraform for 300 resources, Kubernetes, CI/CD 40 times a week, 60% less outage time, 28% lower AWS bill, Solutions Architect certificate and the target title in the summary.

## Rebuilding the files

`make_cvs.py` holds the text of all nineteen CVs and writes them with python-docx. Each PDF is made the way a real user makes one: the Word version is saved as PDF with LibreOffice (if installed), giving 20-28 KB files with embedded fonts. Without LibreOffice it falls back to ReportLab, whose 2-3 KB PDFs read fine in CareerPilot but are rejected by the APILayer resume parser as "File too small".

```
cd backend
python samples/cv_set/make_cvs.py
```

