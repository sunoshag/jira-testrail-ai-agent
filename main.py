# save as testrail_agent.py
import os
import requests
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI, Request, Header, HTTPException
import uvicorn
import re
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- CONFIG from env ---
JIRA_BASE = os.getenv("JIRA_BASE")  # e.g. https://your-domain.atlassian.net
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_BOARD_ID = int(os.getenv("JIRA_BOARD_ID", "1"))  # Jira board ID to fetch active sprint

TESTRAIL_BASE = os.getenv("TESTRAIL_BASE")  # e.g. https://your-company.testrail.io
TESTRAIL_USER = os.getenv("TESTRAIL_USER")
TESTRAIL_API_KEY = os.getenv("TESTRAIL_API_KEY")
TESTRAIL_PROJECT_ID = int(os.getenv("TESTRAIL_PROJECT_ID", "1"))
TESTRAIL_SUITE_ID = int(os.getenv("TESTRAIL_SUITE_ID", "1"))

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")

jira_auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
testrail_auth = HTTPBasicAuth(TESTRAIL_USER, TESTRAIL_API_KEY)

# --- Jira helpers ---
def jira_get_active_sprint(board_id):
    url = f"{JIRA_BASE}/rest/agile/1.0/board/{board_id}/sprint?state=active"
    r = requests.get(url, auth=jira_auth, timeout=30)
    r.raise_for_status()
    sprints = r.json().get("values", [])
    if sprints:
        return sprints[0]
    return None

def jira_get_sprint_issues(sprint_id):
    url = f"{JIRA_BASE}/rest/agile/1.0/sprint/{sprint_id}/issue"
    params = {"fields": "summary,description"}
    r = requests.get(url, auth=jira_auth, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("issues", [])

# --- TestRail helpers ---
def testrail_get_sections(project_id=TESTRAIL_PROJECT_ID, suite_id=TESTRAIL_SUITE_ID):
    url = f"{TESTRAIL_BASE}/index.php?/api/v2/get_sections/{project_id}&suite_id={suite_id}"
    r = requests.get(url, auth=testrail_auth, timeout=20)
    r.raise_for_status()
    return r.json()  # contains keys like offset, size, sections

def testrail_add_section(project_id, name, suite_id, parent_id=None, description=None):
    url = f"{TESTRAIL_BASE}/index.php?/api/v2/add_section/{project_id}"
    data = {"suite_id": suite_id, "name": name}
    if parent_id: data["parent_id"] = parent_id
    if description: data["description"] = description
    r = requests.post(url, auth=testrail_auth, json=data, timeout=20)
    r.raise_for_status()
    return r.json()

def testrail_add_case(section_id, case_payload):
    url = f"{TESTRAIL_BASE}/index.php?/api/v2/add_case/{section_id}"
    r = requests.post(url, auth=testrail_auth, json=case_payload, timeout=20)
    r.raise_for_status()
    return r.json()

def find_section_by_name(project_id, suite_id, name):
    response = testrail_get_sections(project_id, suite_id)
    all_sections = response.get("sections", [])
    print("all sections:", all_sections)

    for s in all_sections:
        if isinstance(s, dict) and s.get("name") == name:
            return s

    return None

# --- TestRail helpers (extended) ---
def testrail_get_cases(project_id, suite_id, section_id=None):
    url = f"{TESTRAIL_BASE}/index.php?/api/v2/get_cases/{project_id}&suite_id={suite_id}"
    if section_id:
        url += f"&section_id={section_id}"
    r = requests.get(url, auth=testrail_auth, timeout=20)
    r.raise_for_status()
    return r.json()

# --- AC parser ---
def extract_acceptance_criteria(issue):
    desc = issue.get("fields", {}).get("description") or ""
    text = desc if isinstance(desc, str) else str(desc)
    m = re.search(r"(?i)acceptance criteria[:\\n]*([\\s\\S]+?)(?:\\n\\n|$)", text)
    if m:
        block = m.group(1).strip()
        items = re.split(r"\\n\\s*[-*•]|\\n\\s*\\d+\\.|\\n\\s*•", block)
        items = [it.strip() for it in items if it.strip()]
        if items: return items
        return [block]
    gwm = re.search(r"(?s)(Given.*?When.*?Then.*?$)", text, re.I)
    if gwm: return [gwm.group(1).strip()]
    summary = issue.get("fields", {}).get("summary", "")
    if text.strip():
        return [summary + " — " + (text[:600] + "..." if len(text) > 600 else text)]
    return [summary]

def ac_to_steps_and_expected(ac_text):
    if re.search(r"Given", ac_text, re.I) and re.search(r"When", ac_text, re.I):
        given = re.search(r"(?i)Given[:\\s]*(.*?)(?=When|$)", ac_text)
        when = re.search(r"(?i)When[:\\s]*(.*?)(?=Then|$)", ac_text)
        then = re.search(r"(?i)Then[:\\s]*(.*?)(?=$)", ac_text)
        steps = []
        if given: steps.append({"content": "Precondition: " + given.group(1).strip(), "expected": ""})
        if when: steps.append({"content": "Action: " + when.group(1).strip(), "expected": ""})
        expected = then.group(1).strip() if then else ""
        if expected == "" and len(steps)==1: expected = steps[0]["content"]
        return steps, expected
    lines = [ln.strip() for ln in re.split(r"\\n|;|\\.|\\*|-", ac_text) if ln.strip()]
    if len(lines) == 1: return ([{"content": lines[0], "expected": ""}], lines[0])
    steps = [{"content": l, "expected": ""} for l in lines]
    expected = steps[-1]["content"] if steps else ""
    return steps, expected

# --- Core: fetch active sprint and create TestRail sections/cases ---
def process_active_sprint():
    sprint = jira_get_active_sprint(JIRA_BOARD_ID)
    if not sprint:
        print("No active sprint found.")
        return

    sprint_id = sprint["id"]
    sprint_name = sprint.get("name", f"Sprint {sprint_id}")
    print(f"Processing active sprint: {sprint_name}")

    # ✅ Check if sprint section already exists
    sprint_section = find_section_by_name(TESTRAIL_PROJECT_ID, TESTRAIL_SUITE_ID, sprint_name)
    print("Section.........:",sprint_section)
    if sprint_section:
        print(f"⚡ Sprint section '{sprint_name}' already exists in TestRail. Exiting...")
        return  # <--- stop everything here

    # Otherwise, create the sprint section
    sprint_section_id = testrail_add_section(
        TESTRAIL_PROJECT_ID,
        sprint_name,
        TESTRAIL_SUITE_ID,
        description=f"Auto-created for Jira sprint {sprint_id}"
    )["id"]
    print(f"🆕 Created sprint section: {sprint_name}")

    # Process issues only if sprint section was just created
    issues = jira_get_sprint_issues(sprint_id)
    for issue in issues:
        key = issue.get("key")
        summary = issue.get("fields", {}).get("summary", "")
        issue_section_name = f"{key} - {summary}"

        issue_section_id = testrail_add_section(
            TESTRAIL_PROJECT_ID,
            issue_section_name,
            TESTRAIL_SUITE_ID,
            parent_id=sprint_section_id,
            description=f"Tests for {key}"
        )["id"]
        print(f"   🆕 Created section for {key}")

        # Create test cases from AC
        ac_list = extract_acceptance_criteria(issue)
        for idx, ac in enumerate(ac_list, start=1):
            steps, expected = ac_to_steps_and_expected(ac)
            payload_case = {
                "title": f"{key} - AC {idx}: {ac[:80]}",
                "template_id": 2,
                "type_id": 1,
                "priority_id": 2,
                "refs": key,
                "custom_preconds": issue.get("fields", {}).get("description", "")[:2000],
                "custom_steps_separated": steps,
            }
            if expected:
                payload_case["custom_expected"] = expected
            testrail_add_case(issue_section_id, payload_case)
            print(f"      🆕 Created case: {key} - AC {idx}")

# --- Startup: automatically process active sprint ---
if __name__ == "__main__":
    process_active_sprint()  # <--- runs immediately on script start