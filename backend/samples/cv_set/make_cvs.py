"""Builds the sample CVs in this folder: set 1 (01-10, three roles, worst to best) and set 2 (11-19, one for each
role added later, worst to best).

Run from the backend folder:  python samples/cv_set/make_cvs.py [output-folder]
Needs python-docx (already in requirements.txt). PDFs: LibreOffice if installed, else ReportLab (pip install reportlab).
CV text format: '- ' starts a bullet; known section names become headings; anything else is plain text.
All people, emails, phone numbers and employers are invented.
"""
import sys
from pathlib import Path
import docx
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape

CVS = [
# 01 ---------------------------------------------------------------- worst: barely a CV
dict(file="cv_01_worst_data.docx", role="Data Analyst", tier="Worst", text="""
kim nguyen
kim.nguyen.demo@example.com
looking for a job in data. i like computers and numbers and have done some excel stuff at my last job. i am a hard worker and can learn things fast.
worked at a shop 2022 - 2024 doing the till and stock and helping customers and other duties as needed. responsible for stocktake.
did a course at tafe. know excel and a bit of sql.
references available on request
"""),

# 02 ---------------------------------------------------------------- very weak: duties only, no numbers
dict(file="cv_02_very_weak_software.pdf", role="Software Developer", tier="Very weak", text="""
Daniel Okafor
daniel.okafor.demo@example.com
Experience
Junior Web Helper - Brightline Print Co  2023 - 2024
- Responsible for updating the company website
- Worked on fixing bugs when asked
- Helped with emails from customers
- Involved in team meetings
Education
Diploma of Information Technology  2021 - 2022
Skills
I know HTML, CSS, JavaScript and some Java. I am a team player and hard working. Hobbies: gaming, soccer.
"""),

# 03 ---------------------------------------------------------------- weak: paragraphs, no bullets
dict(file="cv_03_weak_cyber.docx", role="Cybersecurity Analyst", tier="Weak", text="""
Priya Raman
priya.raman.demo@example.com | 0400 000 101
Objective
I want to start a career in cyber security because it is interesting and I have always liked technology. I am looking for any entry level role where I can learn.
Experience
IT Support, Northgate Medical Clinic, 2023 - 2025. I was responsible for helping staff with computer problems, resetting passwords in Active Directory and setting up new laptops. I also worked on the antivirus and sometimes looked at the firewall settings with my manager. Duties included answering phone calls and logging tickets.
Education
Bachelor of Information Technology, 2020 - 2023
Things I know: networking, firewalls, Windows, Linux, troubleshooting, communication
"""),

# 04 ---------------------------------------------------------------- below average: bullets, no numbers, short
dict(file="cv_04_below_average_data.pdf", role="Data Analyst", tier="Below average", text="""
Tom Fraser
tom.fraser.demo@example.com | 0400 000 102 | Brisbane, QLD
Summary
Business graduate interested in data and reporting.
Experience
Administration Officer - Coastline Insurance (fictional)  Feb 2023 - Present
- Responsible for preparing weekly reports in Excel
- Updated customer records in the CRM
- Helped the team with data entry and checking errors
- Worked on pivot tables for the sales team
Education
Bachelor of Business (Analytics minor) - Griffith University  2019 - 2022
Skills
Excel, pivot tables, SQL (basic), Power BI (learning), communication, attention to detail
"""),

# 05 ---------------------------------------------------------------- average: decent structure, weak impact
dict(file="cv_05_average_software.docx", role="Software Developer", tier="Average", text="""
Lucas Ferreira
lucas.ferreira.demo@example.com | 0400 000 103 | Sydney, NSW | github.com/lucas-demo
Summary
Recent computer science graduate looking for a graduate software developer role. Comfortable with Python and JavaScript and keen to grow in a team that values code quality.
Experience
Software Intern - Harbourview Apps (fictional), Sydney  Nov 2024 - Feb 2025
- Built two internal pages in React for the support team
- Wrote unit tests with Jest for existing components
- Worked on fixing bugs reported in Jira
- Attended daily stand-ups in an Agile team
Casual Retail Assistant - Metro Sports (fictional)  Mar 2021 - Oct 2024
- Served customers and handled stock
Education
Bachelor of Computer Science - Western Sydney University  2021 - 2024
Projects
- Movie watchlist app: Node.js and Express REST API with a MongoDB database
- Final-year project: Python Flask web app for booking study rooms, used by our class
- Personal portfolio site built with HTML, CSS and JavaScript, hosted on GitHub Pages
Achievements
Dean's list in 2023. Volunteer tutor for first-year programming students in my final year, helping with Python labs and assignments.
Skills
Python, JavaScript, React, Node.js, Flask, Git, GitHub, SQL, HTML, CSS, Jest, Agile, teamwork, problem solving
"""),

# 06 ---------------------------------------------------------------- average-plus: helpdesk moving to SOC
dict(file="cv_06_fair_cyber.pdf", role="Cybersecurity Analyst", tier="Fair", text="""
Aisha Rahman
aisha.rahman.demo@example.com | 0400 000 104 | Melbourne, VIC | linkedin.com/in/aisha-demo
Professional summary
IT service desk analyst with 2 years of experience moving into a SOC analyst role. Hands-on with Active Directory, MFA and endpoint troubleshooting, and studying for CompTIA Security+.
Experience
Service Desk Analyst - Riverbend Council (fictional), Melbourne  Jan 2024 - Present
- Resolved around 30 tickets a day for access, MFA and network issues
- Managed user accounts and group policies in Active Directory
- Escalated suspected phishing emails to the security team
- Responsible for documenting fixes in Confluence
IT Support Trainee - Southside College (fictional)  Jul 2023 - Dec 2023
- Set up 40 laptops for new staff using a standard image
- Helped teachers with classroom AV and Wi-Fi problems
Education
Bachelor of Information Technology (Networks) - Swinburne University  2020 - 2023
Projects
- Home lab: set up a pfSense firewall and an Ubuntu server, then captured and reviewed traffic in Wireshark
- Completed 30 TryHackMe rooms on network security, Linux and incident handling
Certifications
Cisco Introduction to Cybersecurity (completed) | CompTIA Security+ (in progress)
Skills
Networking (TCP/IP, DNS, DHCP), Linux, Active Directory, MFA, Wireshark, Nmap, firewalls, incident handling, communication, teamwork, time management
"""),

# 07 ---------------------------------------------------------------- good: quantified, most keywords
dict(file="cv_07_good_data.docx", role="Data Analyst", tier="Good", text="""
Mei Lin Tan
meilin.tan.demo@example.com | 0400 000 105 | Melbourne, VIC | github.com/meilin-demo
Professional summary
Data Analyst with 2 years of experience turning messy operational data into clear dashboards and recommendations. Strong in SQL, Excel and Power BI, with Python for data cleaning and statistics.
Experience
Junior Data Analyst - Greenleaf Grocers (fictional), Melbourne  Mar 2024 - Present
- Built 6 Power BI dashboards tracking sales and stock for 45 stores, used weekly by regional managers
- Automated a monthly Excel report with SQL and pivot tables, cutting preparation time from 2 days to 3 hours
- Cleaned and joined 3 years of transaction data (1.2 million rows) in Python with pandas
- Presented findings on slow-moving stock to stakeholders, leading to a 9% reduction in waste
Reporting Assistant - Greenleaf Grocers (fictional)  Jan 2023 - Feb 2024
- Maintained 12 weekly Excel reports with VLOOKUP and data validation
- Responsible for checking data quality before reports were sent
Education
Bachelor of Commerce (Business Analytics) - Monash University  2020 - 2022
Relevant units: Business Statistics, Data Management, Predictive Analytics, Data Visualisation
Projects
- Public transport usage analysis: cleaned 2 years of open data in Python and built a Power BI report showing peak-hour crowding by line
- Customer survey dashboard for a local charity, built in Excel with slicers, used to plan 3 fundraising events
Certifications
Google Data Analytics Certificate
Skills
SQL, Excel, Power BI, Python, pandas, statistics, data visualisation, data cleaning, stakeholder management, communication, attention to detail
"""),

# 08 ---------------------------------------------------------------- very good: software, quantified
dict(file="cv_08_very_good_software.pdf", role="Software Developer", tier="Very good", text="""
Ethan Walker
ethan.walker.demo@example.com | 0400 000 106 | Brisbane, QLD | github.com/ethan-demo
Professional summary
Software Developer with 3 years of experience building and testing web applications in Python and TypeScript. Writes clean, tested code and ships through CI/CD pipelines in Agile teams.
Experience
Software Developer - Tidewater Logistics (fictional), Brisbane  Feb 2023 - Present
- Built a REST API in Python and FastAPI that processes 50,000 delivery updates a day
- Developed React and TypeScript screens that cut dispatcher data entry time by 35%
- Wrote unit tests with pytest and Jest, raising test coverage from 48% to 85%
- Containerised 4 services with Docker and deployed them to AWS through GitHub Actions
- Reviewed pull requests and mentored 2 graduate developers
Graduate Developer - Peakline Software (fictional)  Feb 2022 - Jan 2023
- Fixed 120+ bugs in a Node.js and PostgreSQL booking system
- Improved slow SQL queries, reducing page load time from 4 seconds to under 1 second
- Wrote technical documentation and runbooks for 3 production services
Projects
- Open-source contributor: fixed 6 issues in a popular Python testing library, all merged
- Personal finance tracker: React and Node.js app with a REST API and JWT authentication, 200 monthly users
Education
Bachelor of Software Engineering - QUT  2018 - 2021
Certifications
AWS Certified Cloud Practitioner (2023)
Skills
Python, TypeScript, JavaScript, React, Node.js, FastAPI, REST APIs, object-oriented programming, data structures, unit testing, PostgreSQL, Docker, AWS, CI/CD, Git, Agile, problem solving, teamwork
"""),

# 09 ---------------------------------------------------------------- excellent: cyber analyst
dict(file="cv_09_excellent_cyber.docx", role="Cybersecurity Analyst", tier="Excellent", text="""
Noah Kowalski
noah.kowalski.demo@example.com | 0400 000 107 | Sydney, NSW | linkedin.com/in/noah-demo
Professional summary
Cybersecurity Analyst with 3 years of experience in a 24/7 security operations centre. Skilled in SIEM monitoring with Splunk, incident response, vulnerability management and network security, and holds CompTIA Security+.
Experience
SOC Analyst - Harbourline Bank (fictional), Sydney  Mar 2023 - Present
- Triaged 60+ Splunk SIEM alerts per shift and escalated 25 confirmed incidents a quarter
- Led incident response for 3 phishing campaigns, containing each within 4 hours
- Ran weekly Nessus vulnerability scans across 2,000 endpoints and tracked fixes to a 92% closure rate
- Wrote 15 detection rules mapped to MITRE ATT&CK, cutting false positives by 30%
- Hardened firewall rules on 12 Linux servers after a risk assessment
Security Operations Trainee - Fortis Health (fictional)  Jan 2022 - Feb 2023
- Investigated 200+ suspicious logins using Active Directory and MFA logs
- Built a Python script that flagged repeated failed logins, saving 5 hours of manual review a week
- Documented 30 incident playbooks in Confluence, used to onboard 4 new analysts
Projects
- Detection lab: built an ELK stack and Sysmon lab to test detections against simulated attacks with Metasploit
- Capture the flag: placed 3rd of 120 teams at a university cyber security competition
Education
Bachelor of Cyber Security - Macquarie University  2018 - 2021
Certifications
CompTIA Security+ (2022) | Cisco CyberOps Associate (2023)
Skills
SIEM (Splunk), incident response, vulnerability assessment, network security, firewalls, Linux, Python, threat modelling, risk assessment, identity and access management, Wireshark, communication, critical thinking
"""),

# 10 ---------------------------------------------------------------- best
dict(file="cv_10_best_data.pdf", role="Data Analyst", tier="Best", text="""
Sofia Mendes
sofia.mendes.demo@example.com | 0400 000 108 | Melbourne, VIC | github.com/sofia-demo
Professional summary
Data Analyst with 4 years of experience delivering SQL, Python and Power BI analysis that drives decisions. Turns complex data into clear dashboards and recommendations for senior stakeholders, with a strong grounding in statistics and data cleaning.
Experience
Data Analyst - Southern Cross Energy (fictional), Melbourne  Jan 2023 - Present
- Built 10 Power BI dashboards on energy use for 300,000 customers, adopted by 4 business units
- Designed ETL pipelines in SQL and Python that cut monthly reporting from 5 days to 1
- Analysed churn with statistics and regression analysis, informing a retention offer that saved $1.2M a year
- Cleaned and validated 8 data sources with pandas, reducing data errors by 70%
- Presented monthly insights to the executive team and trained 15 staff in Excel and Power BI
Junior Data Analyst - Bayside Retail Group (fictional), Melbourne  Feb 2021 - Dec 2022
- Automated 20 Excel reports with SQL and pivot tables, saving 10 hours a week
- Created Tableau dashboards tracking sales across 60 stores
- Ran A/B testing on email campaigns, lifting click-through rate by 18%
Projects
- Housing affordability model: regression analysis in Python on 10 years of public data, published on GitHub with a written summary
- Volunteer analyst for a food bank: built a Power BI dashboard that cut weekly stock planning from 3 hours to 30 minutes
Education
Bachelor of Science (Statistics) - University of Melbourne  2017 - 2020
Relevant units: Statistical Modelling, Databases, Data Visualisation, Machine Learning
Certifications
Microsoft Power BI Data Analyst (PL-300) | Google Data Analytics Certificate
Skills
SQL, Excel, Power BI, Tableau, Python, pandas, statistics, data visualisation, data cleaning, ETL, stakeholder management, communication, problem solving, attention to detail
"""),
# 11 ---------------------------------------------------------------- very weak: business analyst, duties and a long objective
dict(file="cv_11_very_weak_business_analyst.docx", role="Business Analyst", tier="Very weak", text="""
Grace Tan
grace.tan.demo@example.com
Objective
To obtain a challenging position as a business analyst in a reputable organisation where I can use my skills and grow my career while contributing to the success of the company.
Experience
Administration Officer - Riverbend Council (fictional)  2022 - 2024
- Responsible for taking meeting minutes
- Assisted with updating spreadsheets
- Was involved in a project to change the booking system
- Duties included answering emails and filing
Education
Bachelor of Business  2018 - 2021
Skills
Excel, Microsoft Word, good communication, team player, hard working
"""),

# 12 ---------------------------------------------------------------- weak: front-end developer, paragraphs instead of bullets
dict(file="cv_12_weak_frontend.pdf", role="Front-end Developer", tier="Weak", text="""
Lucas Moreau
Mobile 0400 000 201
About me
I am a self-taught web developer who enjoys making websites look nice. I have built a few sites for friends and I am looking for my first job in tech.
Experience
Freelance Web Designer, 2023 - 2025. I made websites for a cafe, a hairdresser and a local football club using HTML, CSS and JavaScript. I was responsible for the design and for keeping the sites updated. I also helped the clients with their social media and photos when they asked.
Retail Assistant, Sportsco (fictional), 2021 - 2023. Served customers, handled the register and stocked shelves.
Education
Certificate IV in Web Development, 2022 - 2023
I can use HTML, CSS, JavaScript, a bit of React, Photoshop and Git. I am creative and friendly.
"""),

# 13 ---------------------------------------------------------------- below average: network engineer, bullets without results
dict(file="cv_13_below_average_network.docx", role="Network Engineer", tier="Below average", text="""
Arjun Mehta
arjun.mehta.demo@example.com | 0400 000 202 | Adelaide, SA
Summary
Network support technician looking to move into a network engineer role.
Experience
Network Support Technician - Coastline Telecom (fictional)  Mar 2023 - Present
- Responsible for configuring switches and routers for business customers
- Worked on firewall changes with the senior engineer
- Helped with troubleshooting VPN problems
- Monitored the network using PRTG
- Updated network diagrams in Visio
Helpdesk Officer - Unity College (fictional)  Feb 2022 - Feb 2023
- Supported staff and students with Wi-Fi and printer issues
- Logged tickets and followed up
Education
Diploma of Information Technology (Networking) - TAFE SA  2020 - 2021
Certifications
CompTIA Network+
Skills
Networking, TCP/IP, DNS, DHCP, VLAN, Cisco IOS, firewalls, VPN, Windows Server, troubleshooting, communication
"""),

# 14 ---------------------------------------------------------------- average: QA / test engineer, some numbers
dict(file="cv_14_average_qa.pdf", role="QA / Test Engineer", tier="Average", text="""
Mei Lin Chow
meilin.chow.demo@example.com | 0400 000 203 | Melbourne, VIC
Professional summary
Software tester with 2 years of experience in manual testing and starting to automate tests. Careful, detail-oriented and comfortable working in Agile teams.
Experience
Software Tester - Bluestone Insurance (fictional), Melbourne  Feb 2024 - Present
- Wrote and ran test cases for the claims portal before each fortnightly release
- Logged defects in Jira and retested fixes with developers
- Responsible for regression testing of 3 web applications
- Tested REST APIs with Postman during sprint testing
- Started automating smoke tests with Selenium for the login and payment pages
Junior Tester - Applied Forms Co (fictional)  Mar 2023 - Jan 2024
- Performed user acceptance testing with business users
- Checked forms in different browsers and on mobile
Education
Bachelor of Computer Science - Deakin University  2019 - 2022
Certifications
ISTQB Foundation Level (CTFL)
Skills
Manual testing, test cases, regression testing, user acceptance testing, Selenium, Postman, API testing, SQL, Jira, Agile, attention to detail, communication
"""),

# 15 ---------------------------------------------------------------- fair: service desk analyst, entry level but quantified
dict(file="cv_15_fair_service_desk.docx", role="Service Desk Analyst", tier="Fair", text="""
Jack O'Brien
jack.obrien.demo@example.com | 0400 000 204 | Perth, WA
Professional summary
IT support officer with 1.5 years of experience on a busy help desk. Known for calm customer service and clear communication with non-technical staff.
Experience
IT Support Officer - Goldfields Health (fictional), Perth  Jun 2024 - Present
- Resolved around 25 tickets a day by phone, chat and in person in ServiceNow
- Reset passwords and managed accounts in Active Directory and Microsoft 365
- Set up Windows 11 laptops and phones for about 15 new starters a month with Intune
- Responsible for keeping the knowledge base up to date
- Escalated network and server issues to the infrastructure team
Customer Service Officer - Westside Phones (fictional)  Jan 2023 - May 2024
- Helped customers set up phones and email accounts
- Handled complaints and returns
Education
Certificate IV in Information Technology - North Metropolitan TAFE  2022
Certifications
CompTIA A+ | ITIL 4 Foundation (in progress)
Skills
IT support, help desk, Windows 11, Microsoft 365, Active Directory, ServiceNow, customer service, troubleshooting, communication, time management
"""),

# 16 ---------------------------------------------------------------- good: data scientist
dict(file="cv_16_good_data_scientist.pdf", role="Data Scientist", tier="Good", text="""
Hannah Schmidt
hannah.schmidt.demo@example.com | 0400 000 205 | Sydney, NSW | github.com/hannah-demo
Professional summary
Data scientist with 2 years of experience building machine learning models in Python and explaining the results to business teams. Strong in statistics, SQL and model evaluation.
Experience
Data Scientist - Harbour Insurance Group (fictional), Sydney  Mar 2024 - Present
- Built a claim fraud model with scikit-learn that flagged 18% more fraudulent claims at the same review cost
- Trained a text classification model on 40,000 customer emails, routing 70% of them automatically
- Wrote SQL to prepare features from 5 source tables and checked data quality with pandas
- Presented model results and their limits to claims managers in monthly reviews
Graduate Data Analyst - Metro Transport (fictional)  Feb 2023 - Feb 2024
- Analysed travel card data for 1.2 million trips a week using SQL and Python
- Created Tableau dashboards used by 3 planning teams
- Ran statistical tests on timetable changes, informing 2 service decisions
Projects
- Housing price prediction: regression and gradient boosting in Python, with a written model card on GitHub
Education
Master of Data Science - University of Sydney  2021 - 2022
Bachelor of Science (Mathematics) - UNSW  2017 - 2020
Skills
Python, SQL, pandas, NumPy, scikit-learn, machine learning, statistics, natural language processing, data visualisation, Tableau, Git, communication, critical thinking
"""),

# 17 ---------------------------------------------------------------- very good: data engineer
dict(file="cv_17_very_good_data_engineer.docx", role="Data Engineer", tier="Very good", text="""
Oliver Grant
oliver.grant.demo@example.com | 0400 000 206 | Melbourne, VIC | github.com/oliver-demo
Professional summary
Data Engineer with 3 years of experience building reliable data pipelines and warehouse models in SQL, Python and dbt on AWS. Cares about data quality, testing and clear documentation.
Experience
Data Engineer - Southern Grocers (fictional), Melbourne  Jan 2023 - Present
- Built 25 ETL pipelines in Python and Airflow that load 40 million rows a day into Snowflake
- Designed star schema models in dbt for sales and stock, used by 60 analysts
- Moved nightly batch jobs to Spark on Databricks, cutting run time from 6 hours to 45 minutes
- Added automated data quality tests that catch 95% of bad loads before reports refresh
- Deployed pipelines with Docker and GitHub Actions, with infrastructure in Terraform
Junior Data Engineer - Insight Media (fictional)  Feb 2022 - Dec 2022
- Wrote SQL and Python jobs that combined 8 marketing data sources into PostgreSQL
- Reduced failed nightly loads from 12 a month to 1 by adding retries and alerts
Projects
- Open data pipeline: Airflow and dbt project loading public transport data into BigQuery, documented on GitHub
Education
Bachelor of Computer Science - Monash University  2018 - 2021
Certifications
AWS Certified Cloud Practitioner
Skills
SQL, Python, ETL, data pipelines, data warehousing, Snowflake, BigQuery, data modelling, dbt, Apache Spark, Airflow, AWS, Docker, Terraform, PostgreSQL, Git, Linux, problem solving, teamwork, communication
"""),

# 18 ---------------------------------------------------------------- excellent: penetration tester
dict(file="cv_18_excellent_pentest.pdf", role="Penetration Tester", tier="Excellent", text="""
Zara Ahmed
zara.ahmed.demo@example.com | 0400 000 207 | Canberra, ACT | linkedin.com/in/zara-demo
Professional summary
Penetration Tester with 3 years of experience testing web applications, internal networks and cloud services. Holds OSCP and writes clear findings reports that developers can act on.
Experience
Penetration Tester - Ironclad Assurance (fictional), Canberra  Feb 2023 - Present
- Led 40 web application and network penetration tests for government and finance clients
- Found 12 critical vulnerabilities, including 3 authentication bypasses, all fixed before release
- Wrote findings reports with risk ratings, evidence and fixes, rated 4.8 of 5 by clients
- Built Python scripts that automated reconnaissance, saving 6 hours on each engagement
- Ran 5 scoped red team exercises and helped the blue team add 20 new detections
Security Analyst - Capital Data Services (fictional)  Jan 2022 - Jan 2023
- Ran Nessus vulnerability scans across 1,500 hosts and tracked fixes to a 90% closure rate
- Reviewed code against the OWASP Top 10 for 15 internal applications
Projects
- Hack The Box: ranked in the top 2% in Australia
- Published 2 write-ups on web application security, read by over 10,000 people
- Volunteer mentor: ran 6 workshops on secure coding for university students, attended by 150 people
Education
Bachelor of Cyber Security - University of Canberra  2018 - 2021
Certifications
OSCP (2023) | CompTIA Security+ (2022)
Skills
Penetration testing, ethical hacking, Burp Suite, Nmap, Metasploit, Kali Linux, OWASP, vulnerability assessment, networking, Linux, Python, threat modelling, cryptography, report writing, communication, critical thinking
"""),

# 19 ---------------------------------------------------------------- best: cloud / devops engineer
dict(file="cv_19_best_cloud_devops.docx", role="Cloud / DevOps Engineer", tier="Best", text="""
Sam Wilson
sam.wilson.demo@example.com | 0400 000 208 | Brisbane, QLD | github.com/sam-demo
Professional summary
Cloud / DevOps Engineer and Site Reliability Engineer with 4 years of experience automating AWS infrastructure with Terraform, running Kubernetes and building CI/CD pipelines. Focused on reliable releases, monitoring and lower cloud costs.
Experience
DevOps Engineer - Northern Payments (fictional), Brisbane  Jan 2023 - Present
- Built all AWS infrastructure as code with Terraform, managing 300 resources across 3 environments
- Moved 18 services to Docker and Kubernetes, cutting deployment time from 2 hours to 10 minutes
- Built CI/CD pipelines in GitHub Actions that run tests and deploy 40 times a week
- Set up Prometheus and Grafana monitoring and alerts, reducing outage time by 60%
- Reduced the monthly AWS bill by 28% by right-sizing instances and scheduling test environments
Cloud Engineer - Brightwave Software (fictional)  Feb 2021 - Dec 2022
- Automated Linux server builds with Ansible and Bash for 50 virtual machines
- Migrated 2 on-premises applications to AWS with no data loss
- Wrote Python tools that rotate keys and report on unused resources
Projects
- Home lab: Kubernetes cluster on 3 Raspberry Pis, deployed with Terraform and Helm
- Incident response playbooks: wrote 12 runbooks for on-call engineers, halving the time to restore service
Education
Bachelor of Information Technology (Networks and Security) - QUT  2017 - 2020
Certifications
AWS Certified Solutions Architect - Associate (2023) | Microsoft Azure Fundamentals (AZ-900)
Skills
AWS, Azure, Linux, Docker, Kubernetes, Terraform, Ansible, infrastructure as code, CI/CD, GitHub Actions, Prometheus, Grafana, Python, Bash, Git, networking, problem solving, teamwork
"""),
]


BULLET = "• "

def lines(cv):
    return [l for l in cv["text"].strip().splitlines()]

def make_docx(cv, path):
    d = docx.Document()
    st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
    ls = lines(cv)
    for i, l in enumerate(ls):
        if i == 0:
            r = d.add_paragraph().add_run(l); r.bold = True; r.font.size = Pt(18)
        elif l.startswith("# ") or (i > 1 and l in HEADINGS):
            p = d.add_paragraph(); p.paragraph_format.space_before = Pt(10)
            r = p.add_run(l.lstrip("# ")); r.bold = True; r.font.size = Pt(12.5)
        elif l.startswith("- "):
            p = d.add_paragraph(BULLET + l[2:]); p.paragraph_format.left_indent = Pt(12); p.paragraph_format.space_after = Pt(2)
        else:
            d.add_paragraph(l)
    d.save(path)

def make_pdf(cv, path):
    name = ParagraphStyle("n", fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=4)
    head = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=12.5, leading=16, spaceBefore=10, spaceAfter=3)
    body = ParagraphStyle("b", fontName="Helvetica", fontSize=10.5, leading=14, spaceAfter=3)
    bul = ParagraphStyle("u", parent=body, leftIndent=12, spaceAfter=2)
    flow = []
    for i, l in enumerate(lines(cv)):
        if i == 0:
            flow.append(Paragraph(escape(l), name))
        elif l.startswith("# ") or (i > 1 and l in HEADINGS):
            flow.append(Paragraph(escape(l.lstrip("# ")), head))
        elif l.startswith("- "):
            flow.append(Paragraph(escape(BULLET + l[2:]), bul))
        else:
            flow.append(Paragraph(escape(l), body))
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm,
                      title=f"CV - {lines(cv)[0]}", author="CareerPilot sample (fictional)").build(flow)

HEADINGS = {"Summary", "Professional summary", "Objective", "Experience", "Education", "Skills", "Projects",
            "Certifications", "Other"}

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
out.mkdir(parents=True, exist_ok=True)
import shutil
import subprocess
import tempfile

# PDFs are made the way a real user makes one: write the Word file, then "Save as PDF" with LibreOffice,
# which embeds the fonts (about 20-30 KB, like a real CV). Some resume-parser APIs reject the tiny PDFs
# ReportLab writes (2-3 KB), so ReportLab is only the fallback when LibreOffice isn't installed.
SOFFICE = (shutil.which("soffice") or shutil.which("libreoffice")
           or next((p for p in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe") if Path(p).exists()), None))


def make_pdf_via_word(cv, path):
    if not SOFFICE:
        print("  LibreOffice not found: using ReportLab (small PDF that some parser APIs reject)")
        return make_pdf(cv, path)
    with tempfile.TemporaryDirectory() as tmp:
        docx_path = Path(tmp) / (path.stem + ".docx")
        make_docx(cv, docx_path)
        subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", str(path.parent), str(docx_path)],
                       check=True, capture_output=True, timeout=120)


for cv in CVS:
    p = out / cv["file"]
    (make_pdf_via_word if p.suffix == ".pdf" else make_docx)(cv, p)
    print("wrote", p.name)
