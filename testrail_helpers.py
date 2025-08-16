import requests
from config import TESTRAIL_BASE, TESTRAIL_PROJECT_ID, TESTRAIL_SUITE_ID, testrail_auth

def testrail_get_sections(project_id=TESTRAIL_PROJECT_ID, suite_id=TESTRAIL_SUITE_ID):
    url = f"{TESTRAIL_BASE}/index.php?/api/v2/get_sections/{project_id}&suite_id={suite_id}"
    r = requests.get(url, auth=testrail_auth, timeout=20)
    r.raise_for_status()
    return r.json()  # returns dict with key "sections"

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
    for s in all_sections:
        if isinstance(s, dict) and s.get("name") == name:
            return s
    return None