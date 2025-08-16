import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

# --- Jira ---
JIRA_BASE = os.getenv("JIRA_BASE")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_BOARD_ID = int(os.getenv("JIRA_BOARD_ID", "1"))
jira_auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

# --- TestRail ---
TESTRAIL_BASE = os.getenv("TESTRAIL_BASE")
TESTRAIL_USER = os.getenv("TESTRAIL_USER")
TESTRAIL_API_KEY = os.getenv("TESTRAIL_API_KEY")
TESTRAIL_PROJECT_ID = int(os.getenv("TESTRAIL_PROJECT_ID", "1"))
TESTRAIL_SUITE_ID = int(os.getenv("TESTRAIL_SUITE_ID", "1"))
testrail_auth = HTTPBasicAuth(TESTRAIL_USER, TESTRAIL_API_KEY)