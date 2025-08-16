import requests
from config import JIRA_BASE, JIRA_BOARD_ID, jira_auth

def jira_get_active_sprint(board_id=JIRA_BOARD_ID):
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