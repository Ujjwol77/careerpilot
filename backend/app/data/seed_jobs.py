"""Synthetic job dataset (15 postings per role, 180 in all) so the platform works offline.

Roles are grouped into IT fields (FIELDS) for the two-step field -> role pickers. Companies are fictional
and salary bands are indicative Australian ranges for the synthetic postings, not market data. Replace `SeedDatasetSource` in agents/job_search_agent.py with a live
job API or an Adzuna/Kaggle import when you want real postings (check each provider's terms).
"""
from ..embeddings import embed
from ..taxonomy import display

ROLE_PROFILES = {
    "data_analyst": {
        "field": "data_ai",
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
        "field": "cybersecurity",
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
        "field": "software",
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
    "data_engineer": {
        "field": "data_ai",
        "label": "Data Engineer",
        "titles": ["Data Engineer", "Analytics Engineer", "Data Platform Engineer", "ETL Developer", "Big Data Engineer"],
        "core": ["sql", "python", "etl", "data_warehousing", "data_modelling"],
        "extras": ["spark", "airflow", "aws", "azure", "gcp", "docker", "postgresql", "cicd", "git", "linux", "problem_solving", "teamwork", "aws_ccp", "communication"],
        "duties": [
            "build and run the pipelines that move data from source systems into the warehouse",
            "model warehouse tables so analysts can trust and reuse them",
            "automate, test and monitor data workflows in the cloud",
        ],
        "salary": {"junior": (80000, 100000), "mid": (110000, 140000), "senior": (150000, 185000)},
    },
    "data_scientist": {
        "field": "data_ai",
        "label": "Data Scientist",
        "titles": ["Data Scientist", "Machine Learning Engineer", "Applied Scientist", "Data Science Analyst", "AI/ML Specialist"],
        "core": ["python", "statistics", "machine_learning", "sql", "communication"],
        "extras": ["pandas", "numpy", "deep_learning", "nlp", "data_viz", "data_cleaning", "git", "aws", "critical_thinking", "stakeholder", "tableau"],
        "duties": [
            "build and evaluate predictive models that answer real business questions",
            "explore large datasets, test hypotheses and explain the results to decision makers",
            "put machine learning models into production and track how they perform",
        ],
        "salary": {"junior": (80000, 100000), "mid": (110000, 140000), "senior": (150000, 190000)},
    },
    "penetration_tester": {
        "field": "cybersecurity",
        "label": "Penetration Tester",
        "titles": ["Penetration Tester", "Ethical Hacker", "Offensive Security Consultant", "Application Security Tester", "Red Team Analyst"],
        "core": ["pentest", "security_tools", "networking", "linux", "owasp"],
        "extras": ["python", "vuln_assessment", "cryptography", "threat_modelling", "report_writing", "oscp", "ceh", "sec_plus", "iam", "critical_thinking", "communication"],
        "duties": [
            "test web applications, networks and cloud services for exploitable weaknesses",
            "write clear findings reports with risk ratings and fixes for client teams",
            "run scoped attack simulations and help defenders improve detection",
        ],
        "salary": {"junior": (75000, 95000), "mid": (105000, 135000), "senior": (140000, 175000)},
    },
    "frontend_developer": {
        "field": "software",
        "label": "Front-end Developer",
        "titles": ["Front-end Developer", "UI Developer", "React Developer", "Web Developer", "Front-end Engineer"],
        "core": ["javascript", "html_css", "react", "git", "responsive_design"],
        "extras": ["typescript", "accessibility", "rest_apis", "unit_testing", "figma", "agile", "node", "teamwork", "attention_detail", "cicd"],
        "duties": [
            "build accessible, responsive interfaces from designs in Figma",
            "turn APIs into fast, well-tested user interfaces",
            "improve page performance and accessibility across devices",
        ],
        "salary": {"junior": (70000, 88000), "mid": (95000, 125000), "senior": (135000, 165000)},
    },
    "qa_engineer": {
        "field": "software",
        "label": "QA / Test Engineer",
        "titles": ["QA Engineer", "Test Analyst", "Test Automation Engineer", "Software Tester", "Quality Assurance Analyst"],
        "core": ["manual_testing", "test_automation", "api_testing", "attention_detail", "communication"],
        "extras": ["python", "javascript", "sql", "cicd", "agile", "jira", "git", "unit_testing", "istqb", "problem_solving"],
        "duties": [
            "write test plans and test cases, then run them before every release",
            "build and maintain automated UI and API test suites in the CI pipeline",
            "find, reproduce and clearly report defects to the development team",
        ],
        "salary": {"junior": (65000, 82000), "mid": (90000, 115000), "senior": (120000, 150000)},
    },
    "cloud_devops_engineer": {
        "field": "cloud_infra",
        "label": "Cloud / DevOps Engineer",
        "titles": ["Cloud Engineer", "DevOps Engineer", "Site Reliability Engineer", "Platform Engineer", "Cloud Infrastructure Engineer"],
        "core": ["aws", "linux", "cicd", "docker", "iac"],
        "extras": ["kubernetes", "azure", "gcp", "python", "monitoring", "networking", "git", "aws_saa", "az900", "aws_ccp", "problem_solving", "teamwork"],
        "duties": [
            "build and automate cloud infrastructure with infrastructure as code",
            "run deployment pipelines and keep production services reliable",
            "monitor systems, respond to outages and reduce cloud costs",
        ],
        "salary": {"junior": (85000, 105000), "mid": (120000, 150000), "senior": (160000, 195000)},
    },
    "network_engineer": {
        "field": "cloud_infra",
        "label": "Network Engineer",
        "titles": ["Network Engineer", "Network Administrator", "Network Support Engineer", "Infrastructure Engineer (Network)", "Network Analyst"],
        "core": ["networking", "routing_switching", "firewalls", "network_security", "problem_solving"],
        "extras": ["ccna", "net_plus", "linux", "python", "monitoring", "aws", "azure", "iam", "communication", "time_management"],
        "duties": [
            "design, configure and maintain routers, switches and firewalls across our sites",
            "troubleshoot connectivity issues and keep network documentation up to date",
            "monitor network performance and plan upgrades with the infrastructure team",
        ],
        "salary": {"junior": (70000, 90000), "mid": (95000, 125000), "senior": (130000, 160000)},
    },
    "service_desk_analyst": {
        "field": "support_business",
        "label": "Service Desk Analyst",
        "titles": ["Service Desk Analyst", "IT Support Officer", "Help Desk Technician", "Desktop Support Analyst", "IT Support Analyst"],
        "core": ["it_support", "windows", "m365", "customer_service", "communication"],
        "extras": ["iam", "networking", "servicenow", "itil", "comptia_a", "problem_solving", "time_management", "attention_detail", "az900", "linux"],
        "duties": [
            "resolve hardware, software and account issues for staff by phone, chat and in person",
            "log, prioritise and follow up tickets in our service management tool",
            "set up laptops, Microsoft 365 accounts and access for new starters",
        ],
        "salary": {"junior": (55000, 68000), "mid": (70000, 85000), "senior": (90000, 110000)},
    },
    "business_analyst": {
        "field": "support_business",
        "label": "Business Analyst",
        "titles": ["Business Analyst", "IT Business Analyst", "Business Systems Analyst", "Requirements Analyst", "Digital Business Analyst"],
        "core": ["requirements", "stakeholder", "process_modelling", "communication", "critical_thinking"],
        "extras": ["sql", "excel", "agile", "jira", "data_viz", "power_bi", "manual_testing", "teamwork", "problem_solving", "leadership"],
        "duties": [
            "gather requirements from stakeholders and write clear user stories",
            "map current and future business processes and find improvements",
            "support delivery teams through testing and user acceptance",
        ],
        "salary": {"junior": (75000, 95000), "mid": (105000, 135000), "senior": (140000, 175000)},
    },
}

# Two-step pickers: field -> roles, in display order.
FIELDS = {
    "data_ai": "Data & AI",
    "cybersecurity": "Cybersecurity",
    "software": "Software Engineering",
    "cloud_infra": "Cloud & Infrastructure",
    "support_business": "IT Support & Business",
}


def fields_with_roles() -> list[dict]:
    return [{"key": f, "label": label,
             "roles": [{"key": k, "label": r["label"]} for k, r in ROLE_PROFILES.items() if r["field"] == f]}
            for f, label in FIELDS.items()]

COMPANIES = {
    "data_analyst": ["Northwind Analytics", "Saltbush Data", "Kestrel Insights", "Bluegum Research"],
    "cybersecurity_analyst": ["Meridian Cyber", "Ironbark Security", "Harbourline Defence", "Redback Secure"],
    "software_developer": ["Redgum Software", "Bluegum Digital", "Harbourline Systems", "Kestrel Labs"],
    "data_engineer": ["Lyrebird Data Works", "Coolibah Platforms", "Saltbush Data", "Kestrel Insights"],
    "data_scientist": ["Kestrel Insights", "Bluegum Research", "Lyrebird Data Works", "Quoll Labs"],
    "penetration_tester": ["Ironbark Security", "Redback Secure", "Taipan Offensive Security", "Meridian Cyber"],
    "frontend_developer": ["Bluegum Digital", "Wattle Studio", "Redgum Software", "Kestrel Labs"],
    "qa_engineer": ["Harbourline Systems", "Redgum Software", "Wattle Studio", "Banksia Quality Labs"],
    "cloud_devops_engineer": ["Coolibah Cloud", "Harbourline Systems", "Lyrebird Data Works", "Bluegum Digital"],
    "network_engineer": ["Mulga Networks", "Ironbark Infrastructure", "Harbourline Defence", "Gidgee Telecom"],
    "service_desk_analyst": ["Wombat IT Services", "Banksia Health IT", "Harbourline Systems", "Mallee Council Digital"],
    "business_analyst": ["Northwind Analytics", "Banksia Health IT", "Mallee Council Digital", "Bluegum Digital"],
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
