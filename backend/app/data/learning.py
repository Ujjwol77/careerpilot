"""Curated learning catalogue: every skill maps to specific pages on named learning sites.

Each resource links straight to a real course, module, tutorial or exam page (no web searches).
URLs were checked on 2026-11-05; run `python -m app.check_links` to re-check them.

Hours: where the provider publishes a duration it is used (marked hours_source="provider");
otherwise it is our estimate for a beginner (hours_source="estimate").

Live course APIs (Coursera, Udemy, edX) need partner keys, so this catalogue is the default
`LearningSource`. A keyed API source can be added later behind the same interface.
"""
from dataclasses import dataclass

from ..taxonomy import SKILLS, display

CHECKED_ON = "2026-11-05"


@dataclass(frozen=True)
class Resource:
    type: str        # course | tutorial | lab | project | certification | practice
    title: str
    provider: str
    url: str
    hours: int
    cost: str        # free | free tier | paid | free to audit
    hours_source: str = "estimate"


R = Resource

CATALOG: dict[str, list[Resource]] = {
    # ---------------- technical ----------------
    "python": [
        R("course", "Python", "Kaggle Learn", "https://www.kaggle.com/learn/python", 5, "free", "provider"),
        R("course", "CS50's Introduction to Programming with Python", "Harvard CS50", "https://cs50.harvard.edu/python/", 30, "free"),
    ],
    "sql": [
        R("course", "Intro to SQL", "Kaggle Learn", "https://www.kaggle.com/learn/intro-to-sql", 3, "free", "provider"),
        R("course", "Advanced SQL (joins, window functions)", "Kaggle Learn", "https://www.kaggle.com/learn/advanced-sql", 4, "free", "provider"),
        R("tutorial", "Interactive SQL lessons and exercises", "SQLBolt", "https://sqlbolt.com/", 5, "free"),
    ],
    "java": [R("course", "Java Programming I and II", "University of Helsinki MOOC", "https://java-programming.mooc.fi/", 40, "free")],
    "javascript": [R("tutorial", "The Modern JavaScript Tutorial", "javascript.info", "https://javascript.info/", 25, "free")],
    "typescript": [R("tutorial", "The TypeScript Handbook", "typescriptlang.org", "https://www.typescriptlang.org/docs/handbook/intro.html", 10, "free")],
    "csharp": [R("tutorial", "A tour of the C# language", "Microsoft Learn", "https://learn.microsoft.com/en-us/dotnet/csharp/tour-of-csharp/", 10, "free")],
    "cpp": [R("tutorial", "Learn C++ (full tutorial)", "LearnCpp.com", "https://www.learncpp.com/", 40, "free")],
    "html_css": [R("course", "Learn web development: HTML and CSS", "MDN Web Docs", "https://developer.mozilla.org/en-US/docs/Learn_web_development", 20, "free")],
    "react": [
        R("tutorial", "Learn React (official docs)", "react.dev", "https://react.dev/learn", 12, "free"),
        R("project", "Tutorial: Tic-Tac-Toe in React", "react.dev", "https://react.dev/learn/tutorial-tic-tac-toe", 3, "free"),
    ],
    "node": [R("tutorial", "Introduction to Node.js", "nodejs.org", "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs", 8, "free")],
    "django": [R("tutorial", "Writing your first Django app", "Django docs", "https://docs.djangoproject.com/en/stable/intro/tutorial01/", 8, "free")],
    "flask": [R("tutorial", "Flask tutorial: build a blog app", "Flask docs", "https://flask.palletsprojects.com/en/stable/tutorial/", 6, "free")],
    "fastapi": [R("tutorial", "FastAPI tutorial: user guide", "FastAPI docs", "https://fastapi.tiangolo.com/tutorial/", 8, "free")],
    "rest_apis": [
        R("tutorial", "Web API design best practices", "Microsoft Learn", "https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design", 3, "free"),
        R("project", "Build a REST API with tests following the FastAPI tutorial", "FastAPI docs", "https://fastapi.tiangolo.com/tutorial/", 10, "free"),
    ],
    "oop": [R("tutorial", "Classes (object-oriented Python)", "Python docs", "https://docs.python.org/3/tutorial/classes.html", 4, "free")],
    "data_structures": [
        R("course", "CS50x: Introduction to Computer Science", "Harvard CS50", "https://cs50.harvard.edu/x/", 60, "free"),
        R("course", "Introduction to Algorithms (6.006)", "MIT OpenCourseWare", "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", 40, "free"),
    ],
    "unit_testing": [
        R("tutorial", "Get started with pytest", "pytest docs", "https://docs.pytest.org/en/stable/getting-started.html", 3, "free"),
        R("tutorial", "Getting started with Jest", "Jest docs", "https://jestjs.io/docs/getting-started", 3, "free"),
    ],
    "microservices": [R("tutorial", "Microservices architecture style", "Microsoft Learn", "https://learn.microsoft.com/en-us/azure/architecture/microservices/", 6, "free")],
    "postgresql": [R("tutorial", "PostgreSQL tutorial", "PostgreSQL docs", "https://www.postgresql.org/docs/current/tutorial.html", 6, "free")],
    "mysql": [R("tutorial", "MySQL 8.4 tutorial", "MySQL docs", "https://dev.mysql.com/doc/refman/8.4/en/tutorial.html", 5, "free")],
    "mongodb": [R("course", "MongoDB University learning paths", "MongoDB University", "https://learn.mongodb.com/", 10, "free")],
    "statistics": [
        R("course", "Statistics and probability", "Khan Academy", "https://www.khanacademy.org/math/statistics-probability", 30, "free"),
        R("course", "OpenIntro Statistics (free textbook)", "OpenIntro", "https://www.openintro.org/book/os/", 30, "free"),
    ],
    "machine_learning": [
        R("course", "Intro to Machine Learning", "Kaggle Learn", "https://www.kaggle.com/learn/intro-to-machine-learning", 3, "free", "provider"),
        R("course", "Machine Learning Crash Course", "Google for Developers", "https://developers.google.com/machine-learning/crash-course", 15, "free", "provider"),
    ],
    "data_viz": [
        R("course", "Data Visualization", "Kaggle Learn", "https://www.kaggle.com/learn/data-visualization", 4, "free", "provider"),
        R("project", "Publish a dashboard to Tableau Public", "Tableau Public", "https://public.tableau.com/", 6, "free"),
    ],
    "data_cleaning": [R("course", "Data Cleaning", "Kaggle Learn", "https://www.kaggle.com/learn/data-cleaning", 4, "free", "provider")],
    "etl": [R("course", "Data Engineering Zoomcamp", "DataTalks.Club", "https://github.com/DataTalksClub/data-engineering-zoomcamp", 40, "free")],
    "pandas": [R("course", "Pandas", "Kaggle Learn", "https://www.kaggle.com/learn/pandas", 4, "free", "provider")],
    "numpy": [R("tutorial", "NumPy: the absolute basics for beginners", "NumPy docs", "https://numpy.org/doc/stable/user/absolute_beginners.html", 3, "free")],
    "networking": [
        R("course", "Networking Basics", "Cisco Networking Academy", "https://www.netacad.com/courses/networking-basics", 22, "free"),
        R("lab", "Pre Security learning path", "TryHackMe", "https://tryhackme.com/path/outline/presecurity", 40, "free tier"),
    ],
    "network_security": [R("course", "Network Defense", "Cisco Networking Academy", "https://www.netacad.com/courses/network-defense", 27, "free")],
    "incident_response": [
        R("lab", "SOC Level 1 learning path", "TryHackMe", "https://tryhackme.com/path/outline/soclevel1", 65, "free tier", "provider"),
        R("tutorial", "NIST SP 800-61 Rev. 3: incident response recommendations", "NIST", "https://csrc.nist.gov/pubs/sp/800/61/r3/final", 4, "free"),
    ],
    "vuln_assessment": [
        R("lab", "Nmap room", "TryHackMe", "https://tryhackme.com/room/furthernmap", 3, "free tier"),
        R("tutorial", "OWASP Top 10", "OWASP", "https://owasp.org/www-project-top-ten/", 4, "free"),
    ],
    "pentest": [
        R("lab", "Web Security Academy", "PortSwigger", "https://portswigger.net/web-security", 40, "free"),
        R("lab", "Jr Penetration Tester learning path", "TryHackMe", "https://tryhackme.com/path/outline/jrpenetrationtester", 60, "free tier"),
    ],
    "firewalls": [R("course", "Network Defense (firewalls, ACLs)", "Cisco Networking Academy", "https://www.netacad.com/courses/network-defense", 27, "free")],
    "cryptography": [
        R("course", "Cryptography I (Stanford)", "Coursera", "https://www.coursera.org/learn/crypto", 20, "free to audit"),
        R("lab", "Interactive cryptography challenges", "CryptoHack", "https://cryptohack.org/", 10, "free"),
    ],
    "risk_assessment": [R("tutorial", "NIST Cybersecurity Framework 2.0", "NIST", "https://www.nist.gov/cyberframework", 6, "free")],
    "iam": [R("tutorial", "What is IAM? (AWS IAM user guide)", "AWS docs", "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html", 4, "free")],
    "owasp": [
        R("tutorial", "OWASP Top 10", "OWASP", "https://owasp.org/www-project-top-ten/", 4, "free"),
        R("lab", "Web Security Academy", "PortSwigger", "https://portswigger.net/web-security", 20, "free"),
    ],
    "threat_modelling": [
        R("tutorial", "Threat modeling", "OWASP", "https://owasp.org/www-community/Threat_Modeling", 3, "free"),
        R("tutorial", "MITRE ATT&CK knowledge base", "MITRE", "https://attack.mitre.org/", 6, "free"),
    ],
    "linux": [
        R("lab", "Linux Fundamentals module", "TryHackMe", "https://tryhackme.com/module/linux-fundamentals", 4, "free tier"),
        R("lab", "Bandit wargame (shell practice)", "OverTheWire", "https://overthewire.org/wargames/bandit/", 10, "free"),
    ],
    "cicd": [R("tutorial", "GitHub Actions documentation", "GitHub Docs", "https://docs.github.com/en/actions", 5, "free")],
    "agile": [
        R("tutorial", "The Scrum Guide", "Scrum.org / Scrum Inc.", "https://scrumguides.org/scrum-guide.html", 2, "free"),
        R("tutorial", "Agile Coach", "Atlassian", "https://www.atlassian.com/agile", 4, "free"),
    ],
    # ---------------- tools ----------------
    "git": [
        R("lab", "Learn Git Branching (interactive)", "learngitbranching.js.org", "https://learngitbranching.js.org/", 3, "free"),
        R("tutorial", "Pro Git book", "git-scm.com", "https://git-scm.com/book/en/v2", 10, "free"),
    ],
    "docker": [R("tutorial", "Docker: get started", "Docker docs", "https://docs.docker.com/get-started/", 6, "free")],
    "kubernetes": [R("tutorial", "Learn Kubernetes basics", "kubernetes.io", "https://kubernetes.io/docs/tutorials/kubernetes-basics/", 5, "free")],
    "aws": [R("course", "Cloud Practitioner training (AWS Skill Builder)", "AWS Training", "https://aws.amazon.com/training/learn-about/cloud-practitioner/", 20, "free")],
    "azure": [R("course", "AZ-900T00: Introduction to Cloud Infrastructure", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/courses/az-900t00", 24, "free", "provider")],
    "gcp": [R("course", "Google Cloud training", "Google Cloud", "https://cloud.google.com/learn/training", 15, "free tier")],
    "excel": [R("course", "Excel video training", "Microsoft Support", "https://support.microsoft.com/en-us/office/excel-video-training-9bc05390-e94c-46af-a5b3-d7c22f6990bb", 8, "free")],
    "power_bi": [R("course", "PL-300T00: Design and manage analytics solutions using Power BI", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/courses/pl-300t00", 72, "free", "provider")],
    "tableau": [R("course", "Free training videos", "Tableau", "https://www.tableau.com/learn/training", 10, "free")],
    "siem": [
        R("course", "Free Splunk training courses", "Splunk", "https://www.splunk.com/en_us/training/free-courses/overview.html", 10, "free"),
        R("lab", "Splunk: The Basics", "TryHackMe", "https://tryhackme.com/room/splunk101", 1, "free tier", "provider"),
    ],
    "security_tools": [
        R("lab", "Wireshark: The Basics", "TryHackMe", "https://tryhackme.com/room/wiresharkthebasics", 1, "free tier", "provider"),
        R("lab", "Nmap room", "TryHackMe", "https://tryhackme.com/room/furthernmap", 3, "free tier"),
    ],
    "jira": [R("tutorial", "Jira guides", "Atlassian", "https://www.atlassian.com/software/jira/guides", 3, "free")],
    # ---------------- certifications ----------------
    "sec_plus": [
        R("course", "SY0-701 Security+ video course", "Professor Messer", "https://www.professormesser.com/security-plus/sy0-701/sy0-701-video/sy0-701-comptia-security-plus-course/", 15, "free", "provider"),
        R("certification", "CompTIA Security+ exam page", "CompTIA", "https://www.comptia.org/certifications/security", 40, "paid"),
    ],
    "net_plus": [
        R("course", "N10-009 Network+ video course", "Professor Messer", "https://www.professormesser.com/network-plus/n10-009/n10-009-video/n10-009-training-course/", 15, "free"),
        R("certification", "CompTIA Network+ exam page", "CompTIA", "https://www.comptia.org/certifications/network", 40, "paid"),
    ],
    "cissp": [
        R("course", "Certified in Cybersecurity (entry-level, free training)", "ISC2", "https://www.isc2.org/certifications/cc", 20, "free"),
        R("certification", "CISSP exam page", "ISC2", "https://www.isc2.org/certifications/cissp", 80, "paid"),
    ],
    "ceh": [R("certification", "Certified Ethical Hacker (CEH)", "EC-Council", "https://www.eccouncil.org/train-certify/certified-ethical-hacker-ceh/", 40, "paid")],
    "aws_ccp": [
        R("course", "Cloud Practitioner training (AWS Skill Builder)", "AWS Training", "https://aws.amazon.com/training/learn-about/cloud-practitioner/", 20, "free"),
        R("certification", "AWS Certified Cloud Practitioner exam page", "AWS", "https://aws.amazon.com/certification/certified-cloud-practitioner/", 10, "paid"),
    ],
    "az900": [
        R("course", "AZ-900T00: Introduction to Cloud Infrastructure", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/courses/az-900t00", 24, "free", "provider"),
        R("certification", "Azure Fundamentals exam page", "Microsoft Learn", "https://learn.microsoft.com/en-us/credentials/certifications/azure-fundamentals/", 6, "paid"),
    ],
    "pl300": [
        R("course", "PL-300T00: Design and manage analytics solutions using Power BI", "Microsoft Learn", "https://learn.microsoft.com/en-us/training/courses/pl-300t00", 72, "free", "provider"),
        R("certification", "Power BI Data Analyst Associate exam page", "Microsoft Learn", "https://learn.microsoft.com/en-us/credentials/certifications/power-bi-data-analyst-associate/", 10, "paid"),
    ],
    "google_da": [R("certification", "Google Data Analytics Professional Certificate", "Coursera", "https://www.coursera.org/professional-certificates/google-data-analytics", 180, "paid")],
}

# Soft skills are built through practice, so each gets a concrete activity plus a guide to follow.
SOFT: dict[str, tuple[str, str, str, str]] = {
    "communication": ("Present a 5-minute walkthrough of one of your projects, then refine it",
                      "Toastmasters", "https://www.toastmasters.org/", "free tier"),
    "teamwork": ("Make your first open-source contribution and note your role and outcome",
                 "First Contributions (GitHub)", "https://github.com/firstcontributions/first-contributions", "free"),
    "problem_solving": ("Solve coding exercises with mentor feedback and write up one hard problem",
                        "Exercism", "https://exercism.org/", "free"),
    "critical_thinking": ("Critique the assumptions in a published analysis using a structured method",
                          "Atlassian Team Playbook", "https://www.atlassian.com/team-playbook", "free"),
    "leadership": ("Run a study-group sprint using a team playbook and note what you would change",
                   "Atlassian Team Playbook", "https://www.atlassian.com/team-playbook", "free"),
    "time_management": ("Plan a two-week sprint for a personal project and review what slipped",
                        "The Scrum Guide", "https://scrumguides.org/scrum-guide.html", "free"),
    "stakeholder": ("Interview a 'client' about a need and write a one-page requirements summary",
                    "Atlassian Team Playbook", "https://www.atlassian.com/team-playbook", "free"),
    "adaptability": ("Pick up a new tool in a week with a hands-on course and note what helped",
                     "Kaggle Learn", "https://www.kaggle.com/learn", "free"),
    "attention_detail": ("Fact-check and proofread a report; keep a checklist of issues you catch",
                         "Atlassian Team Playbook", "https://www.atlassian.com/team-playbook", "free"),
}

# Fallback for skills added to the taxonomy later without a catalogue entry yet.
FALLBACK = {
    "technical": Resource("course", "Browse free courses on Class Central", "Class Central", "https://www.classcentral.com/", 15, "free"),
    "tool": Resource("course", "Browse free courses on Class Central", "Class Central", "https://www.classcentral.com/", 10, "free"),
    "certification": Resource("course", "Browse free courses on Class Central", "Class Central", "https://www.classcentral.com/", 40, "free"),
}


def _as_dict(slug: str, r: Resource) -> dict:
    return {"skill": slug, "type": r.type, "title": r.title, "provider": r.provider, "url": r.url,
            "hours": r.hours, "cost": r.cost, "hours_source": r.hours_source}


def resources_for(slug: str) -> list[dict]:
    skill = SKILLS.get(slug)
    if slug in CATALOG:
        return [_as_dict(slug, r) for r in CATALOG[slug]]
    if slug in SOFT or (skill and skill.category == "soft"):
        text, provider, url, cost = SOFT.get(slug, (
            f"Practise {display(slug)} through a real project and reflect on the result",
            "Atlassian Team Playbook", "https://www.atlassian.com/team-playbook", "free"))
        return [_as_dict(slug, Resource("practice", text, provider, url, 5, cost))]
    fb = FALLBACK.get(skill.category if skill else "technical", FALLBACK["technical"])
    return [_as_dict(slug, Resource(fb.type, f"{display(slug)}: {fb.title.lower()}", fb.provider, fb.url, fb.hours, fb.cost))]


def all_urls() -> list[tuple[str, str]]:
    """(slug, url) for every link in the catalogue, used by the link checker."""
    out = [(s, r.url) for s, rs in CATALOG.items() for r in rs]
    out += [(s, v[2]) for s, v in SOFT.items()]
    out += [("fallback", FALLBACK["technical"].url)]
    seen, unique = set(), []
    for s, u in out:
        if u not in seen:
            seen.add(u)
            unique.append((s, u))
    return unique
