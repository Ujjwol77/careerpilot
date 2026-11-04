"""Synthetic job dataset (45 postings) so the platform works offline.

Companies are fictional. Replace `SeedDatasetSource` in agents/job_search_agent.py with a live
job API or an Adzuna/Kaggle import when you want real postings (check each provider's terms).
"""
from ..embeddings import embed
from ..taxonomy import display

ROLE_PROFILES = {
    "data_analyst": {
        "label": "Data Analyst",
        "titles": ["Data Analyst", "Business Intelligence Analyst", "Reporting Analyst", "Insights Analyst", "Analytics Specialist"],
        "core": ["sql", "excel", "data_viz", "statistics", "communication"],
        "extras": ["python", "power_bi", "tableau", "pandas", "data_cleaning", "etl", "stakeholder", "problem_solving", "attention_detail", "google_da", "pl300"],
        "duties": [
            "turn raw business data into dashboards and clear recommendations",
            "clean and prepare datasets, then analyse trends for stakeholders",
            "build recurring reports and present findings to non-technical teams",
        ],
        "salary": {"junior": (65000, 80000), "mid": (85000, 110000), "senior": (115000, 145000)},
    },
    "cybersecurity_analyst": {
        "label": "Cybersecurity Analyst",
        "titles": ["Cybersecurity Analyst", "Security Operations Analyst", "SOC Analyst", "Information Security Analyst", "Cyber Defence Analyst"],
        "core": ["network_security", "incident_response", "siem", "vuln_assessment", "linux", "communication"],
        "extras": ["python", "firewalls", "risk_assessment", "iam", "threat_modelling", "owasp", "cryptography", "sec_plus", "cissp", "ceh", "critical_thinking", "networking", "security_tools"],
        "duties": [
            "monitor alerts, investigate incidents and write up findings",
            "run vulnerability scans and track remediation with engineering teams",
            "harden systems, review access controls and improve detection rules",
        ],
        "salary": {"junior": (70000, 90000), "mid": (95000, 125000), "senior": (130000, 165000)},
    },
    "software_developer": {
        "label": "Software Developer",
        "titles": ["Software Developer", "Software Engineer", "Full-Stack Developer", "Backend Developer", "Application Developer"],
        "core": ["git", "rest_apis", "unit_testing", "oop", "problem_solving"],
        "extras": ["python", "javascript", "typescript", "react", "node", "sql", "docker", "cicd", "aws", "agile", "microservices", "postgresql", "data_structures", "teamwork", "aws_ccp"],
        "duties": [
            "design, build and test features across our web platform",
            "write clean, tested code and review pull requests with the team",
            "ship APIs and user interfaces, then monitor and improve them in production",
        ],
        "salary": {"junior": (70000, 90000), "mid": (100000, 130000), "senior": (140000, 175000)},
    },
}

COMPANIES = {
    "data_analyst": ["Northwind Analytics", "Saltbush Data", "Kestrel Insights", "Bluegum Research"],
    "cybersecurity_analyst": ["Meridian Cyber", "Ironbark Security", "Harbourline Defence", "Redback Secure"],
    "software_developer": ["Redgum Software", "Bluegum Digital", "Harbourline Systems", "Kestrel Labs"],
}
LOCATIONS = ["Melbourne, VIC", "Sydney, NSW", "Perth, WA", "Brisbane, QLD", "Remote (Australia)"]
LEVELS = [("junior", 0, "Junior "), ("mid", 2, ""), ("senior", 5, "Senior ")]


def build_seed_jobs() -> list[dict]:
    jobs = []
    for r_idx, (role_key, role) in enumerate(ROLE_PROFILES.items()):
        for l_idx, (level, min_years, prefix) in enumerate(LEVELS):
            for v in range(5):
                core = role["core"][: 4 if level == "junior" else len(role["core"])]
                n_extra = 2 + l_idx + (v % 2)
                extras = [role["extras"][(v * 2 + i) % len(role["extras"])] for i in range(n_extra)]
                skills = list(dict.fromkeys(core + extras))
                company = COMPANIES[role_key][(l_idx * 2 + v) % 4]
                location = LOCATIONS[(r_idx + l_idx + v) % len(LOCATIONS)]
                title = f"{prefix}{role['titles'][v]}".strip()
                lo, hi = role["salary"][level]
                bump = v * 2500
                duty = role["duties"][(l_idx + v) % len(role["duties"])]
                exp_line = (
                    "No prior experience required; we will train the right person."
                    if level == "junior"
                    else f"You bring {min_years}+ years of relevant experience."
                )
                description = (
                    f"{company} is hiring a {title} in {location}. You will {duty}. "
                    f"Requirements: {', '.join(display(s) for s in skills)}. {exp_line}"
                )
                jobs.append({
                    "title": title, "company": company, "location": location,
                    "role_category": role_key, "level": level, "min_years": min_years,
                    "salary_min": lo + bump, "salary_max": hi + bump,
                    "description": description, "skills": skills,
                    "embedding": embed(f"{title}. {description}"),
                })
    return jobs
