"""Question bank: (question, expected keywords used for scoring)."""

SKILL_QUESTIONS: dict[str, list[tuple[str, list[str]]]] = {
    "sql": [("Explain the difference between INNER JOIN and LEFT JOIN and when you would use each.",
             ["join", "rows", "null", "match", "left", "inner"])],
    "python": [("How would you clean a CSV with missing values and duplicates in Python?",
                ["pandas", "missing", "duplicates", "dropna", "fillna", "validate"])],
    "excel": [("How do you summarise a large sales sheet by region and month in Excel?",
               ["pivot", "table", "group", "sum", "filter", "chart"])],
    "power_bi": [("What is the difference between a measure and a calculated column in Power BI?",
                  ["measure", "column", "dax", "row", "context", "aggregate"])],
    "statistics": [("A p-value is 0.03. What does that tell you, and what does it not tell you?",
                    ["null", "hypothesis", "probability", "significance", "effect", "sample"])],
    "data_viz": [("How do you choose between a bar chart, line chart and scatter plot?",
                  ["trend", "comparison", "categories", "relationship", "audience", "time"])],
    "git": [("Walk me through how you resolve a merge conflict.",
             ["conflict", "merge", "branch", "pull", "commit", "review"])],
    "docker": [("What is the difference between a Docker image and a container?",
                ["image", "container", "layer", "run", "dockerfile", "instance"])],
    "linux": [("How would you find which process is using the most CPU on a Linux server?",
               ["top", "ps", "cpu", "process", "kill", "monitor"])],
    "siem": [("An alert shows 50 failed logins followed by one success from a new country. What do you do?",
              ["investigate", "logs", "account", "mfa", "reset", "escalate", "ip"])],
    "network_security": [("What is the difference between a stateful and stateless firewall?",
                          ["state", "connection", "packet", "rules", "track", "session"])],
    "incident_response": [("Describe the phases of incident response and what happens in each.",
                           ["preparation", "identification", "containment", "eradication", "recovery", "lessons"])],
    "vuln_assessment": [("How do you prioritise 200 vulnerabilities from a scan?",
                         ["severity", "cvss", "exploit", "asset", "risk", "patch", "business"])],
    "rest_apis": [("What makes an API RESTful? Which status codes would you return for create, not found and invalid input?",
                   ["resource", "http", "201", "404", "400", "stateless", "verbs"])],
    "unit_testing": [("What makes a good unit test, and what should you mock?",
                      ["isolated", "fast", "assert", "mock", "dependency", "deterministic"])],
    "react": [("When does a React component re-render and how can you avoid unnecessary renders?",
               ["state", "props", "render", "memo", "key", "hooks"])],
    "javascript": [("Explain closures in JavaScript with a practical example.",
                    ["function", "scope", "variable", "closure", "lexical", "example"])],
    "typescript": [("What problems do TypeScript types solve compared with plain JavaScript?",
                    ["type", "compile", "errors", "interface", "refactor", "safety"])],
    "cicd": [("What should a CI pipeline do on every pull request?",
              ["test", "build", "lint", "automate", "merge", "feedback"])],
    "aws": [("When would you choose object storage over a block volume on AWS?",
             ["s3", "object", "durable", "cost", "ebs", "access"])],
    "agile": [("What happens in a sprint retrospective and why does it matter?",
               ["team", "improve", "went well", "action", "sprint", "feedback"])],
}

ROLE_QUESTIONS: dict[str, list[tuple[str, list[str]]]] = {
    "data_analyst": [
        ("Tell me about an analysis that changed a decision. What was the data and the outcome?", ["data", "insight", "decision", "result", "stakeholder"]),
        ("How do you check a dataset is trustworthy before analysing it?", ["missing", "outliers", "duplicates", "validate", "source", "quality"]),
    ],
    "cybersecurity_analyst": [
        ("How would you explain a phishing risk to non-technical staff?", ["phishing", "report", "links", "training", "simple", "example"]),
        ("What is the principle of least privilege and where have you applied it?", ["least", "access", "permissions", "role", "need", "reduce"]),
    ],
    "software_developer": [
        ("How do you decide when code is ready for review?", ["tests", "readable", "scope", "description", "lint", "review"]),
        ("Describe how you would debug a bug that only happens in production.", ["logs", "reproduce", "monitor", "hypothesis", "rollback", "metrics"]),
    ],
    "data_engineer": [
        ("A nightly pipeline failed and the morning dashboards are empty. What do you do?", ["logs", "rerun", "idempotent", "alert", "stakeholders", "root cause"]),
        ("How would you design a fact table for online orders?", ["grain", "fact", "dimension", "keys", "star schema", "measures"]),
    ],
    "data_scientist": [
        ("How do you know a model is good enough to put in front of users?", ["baseline", "validation", "metric", "test set", "overfitting", "business"]),
        ("Explain a model's result to a manager with no statistics background.", ["simple", "example", "uncertainty", "impact", "decision", "visual"]),
    ],
    "penetration_tester": [
        ("Walk me through how you would start testing a web application you have never seen.", ["scope", "recon", "map", "authentication", "owasp", "permission"]),
        ("How do you write a finding so the developer can fix it?", ["risk", "steps", "reproduce", "evidence", "impact", "remediation"]),
    ],
    "frontend_developer": [
        ("How do you make a form accessible?", ["labels", "keyboard", "errors", "aria", "contrast", "screen reader"]),
        ("A page feels slow on mobile. How do you find out why?", ["lighthouse", "bundle", "images", "network", "measure", "lazy"]),
    ],
    "qa_engineer": [
        ("How do you decide what to automate and what to test by hand?", ["repeat", "regression", "risk", "stable", "cost", "exploratory"]),
        ("Write a bug report for a login button that does nothing. What goes in it?", ["steps", "expected", "actual", "environment", "severity", "screenshot"]),
    ],
    "cloud_devops_engineer": [
        ("Why use infrastructure as code instead of setting things up in the console?", ["repeatable", "version control", "review", "drift", "terraform", "rollback"]),
        ("A deployment broke production. What do you do in the first 15 minutes?", ["rollback", "communicate", "monitor", "logs", "incident", "impact"]),
    ],
    "network_engineer": [
        ("A user says 'the internet is down'. How do you troubleshoot it?", ["ping", "dns", "gateway", "cable", "layer", "isolate"]),
        ("What is a VLAN and why would you use one?", ["segment", "broadcast", "security", "switch", "trunk", "traffic"]),
    ],
    "service_desk_analyst": [
        ("A manager is locked out an hour before a board meeting. How do you handle it?", ["verify", "identity", "reset", "priority", "calm", "ticket"]),
        ("How do you decide which tickets to work on first?", ["impact", "urgency", "priority", "sla", "business", "escalate"]),
    ],
    "business_analyst": [
        ("Two stakeholders want opposite things from the same feature. What do you do?", ["listen", "goals", "priority", "trade-off", "data", "agree"]),
        ("How do you write a good user story?", ["as a", "so that", "acceptance criteria", "value", "small", "testable"]),
    ],
}

BEHAVIOURAL = [
    "Tell me about a time you had to learn something quickly to finish a task.",
    "Describe a disagreement with a teammate and how you resolved it.",
    "Give an example of a mistake you made at work or study and what you did next.",
    "Tell me about a time you managed several deadlines at once.",
    "Describe a time you explained something technical to someone non-technical.",
    "Tell me about a project you are proud of and your specific contribution.",
]
