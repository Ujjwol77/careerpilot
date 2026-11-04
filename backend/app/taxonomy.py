"""Skills taxonomy with aliases.

Fixes the exact-string-match weakness of the original pseudocode: "ReactJS", "React.js" and
"React" all resolve to the same canonical slug, so profile skills and job skills compare reliably.
"""
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Skill:
    display: str
    category: str  # technical | tool | soft | certification
    aliases: tuple[str, ...]
    case_sensitive_aliases: tuple[str, ...] = field(default_factory=tuple)  # for ambiguous words like "React"


def _s(display, category, aliases, cs=()):
    return Skill(display, category, tuple(a.lower() for a in aliases), tuple(cs))


SKILLS: dict[str, Skill] = {
    # --- technical ---
    "python": _s("Python", "technical", ["python", "python3"]),
    "sql": _s("SQL", "technical", ["sql", "t-sql", "tsql", "structured query language"]),
    "java": _s("Java", "technical", ["java"]),
    "javascript": _s("JavaScript", "technical", ["javascript", "ecmascript"]),
    "typescript": _s("TypeScript", "technical", ["typescript"]),
    "csharp": _s("C#", "technical", ["c#", "c sharp", "csharp"]),
    "cpp": _s("C++", "technical", ["c++", "cpp"]),
    "html_css": _s("HTML/CSS", "technical", ["html", "html5", "css", "css3"]),
    "react": _s("React", "technical", ["reactjs", "react.js", "react js"], cs=["React"]),
    "node": _s("Node.js", "technical", ["node.js", "nodejs", "node js"]),
    "django": _s("Django", "technical", ["django"]),
    "flask": _s("Flask", "technical", ["flask"]),
    "fastapi": _s("FastAPI", "technical", ["fastapi"]),
    "rest_apis": _s("REST APIs", "technical", ["rest api", "rest apis", "restful", "restful api", "restful apis", "api development", "web services"]),
    "oop": _s("Object-oriented programming", "technical", ["oop", "object-oriented", "object oriented"]),
    "data_structures": _s("Data structures & algorithms", "technical", ["data structures", "data structure", "algorithms"]),
    "unit_testing": _s("Unit testing", "technical", ["unit testing", "unit tests", "pytest", "junit", "jest", "test-driven", "tdd", "automated testing"]),
    "microservices": _s("Microservices", "technical", ["microservices", "micro-services", "microservice"]),
    "postgresql": _s("PostgreSQL", "technical", ["postgresql", "postgres"]),
    "mysql": _s("MySQL", "technical", ["mysql"]),
    "mongodb": _s("MongoDB", "technical", ["mongodb", "mongo db", "nosql"]),
    "statistics": _s("Statistics", "technical", ["statistics", "statistical analysis", "hypothesis testing", "regression analysis", "a/b testing"]),
    "machine_learning": _s("Machine learning", "technical", ["machine learning", "ml models", "scikit-learn", "sklearn"]),
    "data_viz": _s("Data visualisation", "technical", ["data visualisation", "data visualization", "dashboards", "dashboarding", "data viz"]),
    "data_cleaning": _s("Data cleaning", "technical", ["data cleaning", "data wrangling", "data preparation", "data cleansing"]),
    "etl": _s("ETL pipelines", "technical", ["etl", "elt", "data pipelines", "data pipeline"]),
    "pandas": _s("Pandas", "technical", ["pandas"]),
    "numpy": _s("NumPy", "technical", ["numpy"]),
    "networking": _s("Networking", "technical", ["networking", "tcp/ip", "dns", "dhcp", "routing and switching", "vlan"]),
    "network_security": _s("Network security", "technical", ["network security", "intrusion detection", "intrusion prevention"]),
    "incident_response": _s("Incident response", "technical", ["incident response", "incident handling", "incident management", "digital forensics"]),
    "vuln_assessment": _s("Vulnerability assessment", "technical", ["vulnerability assessment", "vulnerability scanning", "vulnerability management", "nessus", "qualys"]),
    "pentest": _s("Penetration testing", "technical", ["penetration testing", "pen testing", "pentest", "ethical hacking"]),
    "firewalls": _s("Firewalls", "technical", ["firewall", "firewalls"]),
    "cryptography": _s("Cryptography", "technical", ["cryptography", "encryption", "pki"]),
    "risk_assessment": _s("Risk assessment", "technical", ["risk assessment", "risk management", "risk analysis"]),
    "iam": _s("Identity & access management", "technical", ["iam", "identity and access management", "active directory", "sso", "mfa", "multi-factor authentication"]),
    "owasp": _s("Secure coding (OWASP)", "technical", ["owasp", "secure coding", "application security", "appsec"]),
    "threat_modelling": _s("Threat modelling", "technical", ["threat modelling", "threat modeling", "mitre att&ck", "mitre attack"]),
    "linux": _s("Linux", "technical", ["linux", "ubuntu", "bash", "shell scripting", "unix"]),
    "cicd": _s("CI/CD", "technical", ["ci/cd", "cicd", "continuous integration", "continuous delivery", "github actions", "jenkins", "gitlab ci"]),
    "agile": _s("Agile / Scrum", "technical", ["agile", "scrum", "kanban", "sprint planning"]),
    # --- tools ---
    "git": _s("Git", "tool", ["git", "github", "gitlab", "version control", "bitbucket"]),
    "docker": _s("Docker", "tool", ["docker", "containers", "containerisation", "containerization"]),
    "kubernetes": _s("Kubernetes", "tool", ["kubernetes", "k8s"]),
    "aws": _s("AWS", "tool", ["aws", "amazon web services", "ec2"]),
    "azure": _s("Azure", "tool", ["azure", "microsoft azure"]),
    "gcp": _s("Google Cloud", "tool", ["gcp", "google cloud"]),
    "excel": _s("Excel", "tool", ["excel", "microsoft excel", "pivot tables", "vlookup", "xlookup"]),
    "power_bi": _s("Power BI", "tool", ["power bi", "powerbi", "dax"]),
    "tableau": _s("Tableau", "tool", ["tableau"]),
    "siem": _s("SIEM tools", "tool", ["siem", "splunk", "qradar", "sentinel", "elk stack"]),
    "security_tools": _s("Security testing tools", "tool", ["wireshark", "nmap", "metasploit", "burp suite", "kali linux"]),
    "jira": _s("Jira", "tool", ["jira", "confluence"]),
    # --- soft skills ---
    "communication": _s("Communication", "soft", ["communication", "communicating", "presenting", "presentations", "public speaking", "written and verbal"]),
    "teamwork": _s("Teamwork", "soft", ["teamwork", "collaboration", "collaborated", "collaborative", "team player", "cross-functional"]),
    "problem_solving": _s("Problem solving", "soft", ["problem solving", "problem-solving", "troubleshooting", "analytical thinking"]),
    "critical_thinking": _s("Critical thinking", "soft", ["critical thinking", "analytical skills", "analytical mindset"]),
    "leadership": _s("Leadership", "soft", ["leadership", "led a team", "team lead", "mentoring", "mentored"]),
    "time_management": _s("Time management", "soft", ["time management", "prioritisation", "prioritization", "meeting deadlines"]),
    "stakeholder": _s("Stakeholder management", "soft", ["stakeholder management", "stakeholder engagement", "stakeholders", "client-facing"]),
    "adaptability": _s("Adaptability", "soft", ["adaptability", "adaptable", "fast learner", "quick learner"]),
    "attention_detail": _s("Attention to detail", "soft", ["attention to detail", "detail-oriented", "detail oriented"]),
    # --- certifications ---
    "sec_plus": _s("CompTIA Security+", "certification", ["security+", "comptia security+", "comptia security plus"]),
    "net_plus": _s("CompTIA Network+", "certification", ["network+", "comptia network+"]),
    "cissp": _s("CISSP", "certification", ["cissp"]),
    "ceh": _s("Certified Ethical Hacker (CEH)", "certification", ["ceh", "certified ethical hacker"]),
    "aws_ccp": _s("AWS Cloud Practitioner", "certification", ["aws certified cloud practitioner", "cloud practitioner", "aws ccp"]),
    "az900": _s("Azure Fundamentals (AZ-900)", "certification", ["az-900", "az900", "azure fundamentals"]),
    "pl300": _s("Power BI Data Analyst (PL-300)", "certification", ["pl-300", "pl300", "power bi data analyst"]),
    "google_da": _s("Google Data Analytics Certificate", "certification", ["google data analytics certificate", "google data analytics professional certificate"]),
}

CATEGORY_ORDER = ["technical", "tool", "certification", "soft"]

_ALIAS_TO_SLUG: dict[str, str] = {}
for _slug, _skill in SKILLS.items():
    for _alias in _skill.aliases:
        _ALIAS_TO_SLUG.setdefault(_alias, _slug)

_ALIAS_RE = re.compile(
    r"(?<![a-z0-9+#.])("
    + "|".join(re.escape(a) for a in sorted(_ALIAS_TO_SLUG, key=len, reverse=True))
    + r")(?![a-z0-9+#])"
)
_CS_PATTERNS = {
    slug: [re.compile(r"(?<![A-Za-z0-9+#.])" + re.escape(a) + r"(?![A-Za-z0-9+#])") for a in skill.case_sensitive_aliases]
    for slug, skill in SKILLS.items()
    if skill.case_sensitive_aliases
}


def extract_skills(text: str) -> list[str]:
    """Return canonical skill slugs found in free text (CV or job description)."""
    found = {_ALIAS_TO_SLUG[m.group(1)] for m in _ALIAS_RE.finditer(text.lower())}
    for slug, patterns in _CS_PATTERNS.items():
        if any(p.search(text) for p in patterns):
            found.add(slug)
    return [s for s in SKILLS if s in found]


def canonicalise_text(text: str) -> str:
    """Replace every alias with its canonical token (skill_<slug>) so embeddings treat synonyms alike."""
    lowered = text.lower()
    out = _ALIAS_RE.sub(lambda m: f" skill_{_ALIAS_TO_SLUG[m.group(1)]} ", lowered)
    for slug, patterns in _CS_PATTERNS.items():
        if any(p.search(text) for p in patterns):
            out += f" skill_{slug}"
    return out


def display(slug: str) -> str:
    return SKILLS[slug].display if slug in SKILLS else slug


def category(slug: str) -> str:
    return SKILLS[slug].category if slug in SKILLS else "technical"
