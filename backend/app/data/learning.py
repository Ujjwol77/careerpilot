"""Learning resource catalogue. Titles are descriptive (not links to specific vendors' pages);
`search` is a query the UI turns into a web search so nothing here can go stale or 404."""
from ..taxonomy import SKILLS, display

CATALOG: dict[str, list[tuple[str, str, int]]] = {
    "sql": [("course", "SQL for data analysis: joins, aggregates, window functions", 20),
            ("project", "Analyse a public dataset in SQL and publish the queries on GitHub", 10)],
    "python": [("course", "Python fundamentals through data-focused exercises", 25),
               ("project", "Automate a repetitive task or clean a messy CSV with a Python script", 10)],
    "excel": [("course", "Excel for analysts: pivot tables, lookups, charts", 12)],
    "power_bi": [("course", "Power BI report building and DAX basics", 15),
                 ("project", "Build and publish a sales dashboard from a public dataset", 8)],
    "tableau": [("course", "Tableau dashboards for beginners", 12)],
    "statistics": [("course", "Applied statistics: distributions, hypothesis tests, regression", 20)],
    "data_viz": [("project", "Redesign a poor chart and write a one-page insight summary", 6)],
    "git": [("course", "Git and GitHub workflow: branches, pull requests, code review", 6)],
    "docker": [("course", "Docker essentials: images, containers, compose", 8),
               ("project", "Containerise a small web app and document how to run it", 6)],
    "linux": [("course", "Linux command line and shell scripting fundamentals", 12)],
    "siem": [("course", "SIEM fundamentals: log sources, searches, alert triage", 15),
             ("project", "Set up a free home-lab SIEM and write three detection searches", 12)],
    "network_security": [("course", "Network security fundamentals: firewalls, IDS/IPS, segmentation", 18)],
    "incident_response": [("course", "Incident response lifecycle and playbooks", 12),
                          ("project", "Write an incident report for a simulated phishing case", 6)],
    "vuln_assessment": [("project", "Scan a deliberately vulnerable lab VM and write a remediation report", 10)],
    "react": [("course", "React fundamentals: components, state, hooks", 20),
              ("project", "Build and deploy a small React app that calls a public API", 12)],
    "typescript": [("course", "TypeScript for JavaScript developers", 10)],
    "javascript": [("course", "Modern JavaScript fundamentals (ES6+)", 18)],
    "rest_apis": [("project", "Design and document a small REST API with tests", 10)],
    "unit_testing": [("course", "Unit testing and test-driven development basics", 8)],
    "cicd": [("project", "Add a CI pipeline that runs tests on every push", 5)],
    "aws": [("course", "Core AWS services: compute, storage, networking, IAM", 20)],
    "azure": [("course", "Core Azure services and cloud concepts", 15)],
    "agile": [("course", "Agile and Scrum fundamentals", 6)],
}

SOFT_ACTIVITIES = {
    "communication": "Present a 5-minute walkthrough of one of your projects to a friend or study group, then refine it",
    "teamwork": "Contribute to a group or open-source project and write down your role and outcome",
    "problem_solving": "Document one hard problem you solved: the cause, options you weighed and result",
    "critical_thinking": "Pick a published analysis and write a short critique of its assumptions",
    "leadership": "Lead a study group or project sprint and note what you would change",
    "time_management": "Plan a two-week sprint for a personal project and review what slipped",
    "stakeholder": "Interview a 'client' (a friend) about a need and write a one-page requirements summary",
    "adaptability": "Learn a new tool in a week and write what helped you ramp up fast",
    "attention_detail": "Proofread and fact-check a report; keep a checklist of the issues you catch",
}


def resources_for(slug: str) -> list[dict]:
    name = display(slug)
    skill = SKILLS.get(slug)
    items = CATALOG.get(slug)
    if items:
        return [{"skill": slug, "type": t, "title": title, "hours": h, "search": f"{name} {t}"} for t, title, h in items]
    if skill and skill.category == "certification":
        return [{"skill": slug, "type": "certification", "title": f"Study plan and practice exams: {name}", "hours": 40, "search": f"{name} exam study guide"}]
    if skill and skill.category == "soft":
        text = SOFT_ACTIVITIES.get(slug, f"Practise {name} through a real project and reflect on the result")
        return [{"skill": slug, "type": "practice", "title": text, "hours": 5, "search": f"improve {name} at work"}]
    return [
        {"skill": slug, "type": "course", "title": f"Introductory course: {name}", "hours": 15, "search": f"{name} beginner course"},
        {"skill": slug, "type": "project", "title": f"Portfolio project using {name}", "hours": 8, "search": f"{name} project ideas"},
    ]
