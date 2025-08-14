# Jira → TestRail AI Agent

An automation service that listens for Jira sprint start events, fetches issues in that sprint, and creates corresponding sections and manual test cases in TestRail — automatically generating test steps from issue descriptions and acceptance criteria.

## Features
- **Automatic Sprint Setup** – Creates a new TestRail section for each sprint.
- **Subsection per Jira Task** – Groups test cases under each Jira issue.
- **Acceptance Criteria Parsing** – Generates test case steps and expected results from Jira issue descriptions.
- **References Linking** – Links each test case to its Jira issue via the `refs` field in TestRail.
- **Idempotent** – Avoids creating duplicate sections or cases if they already exist.

## How It Works
1. Jira sends a webhook when a sprint starts.
2. The agent calls the Jira Agile API to list issues in that sprint.
3. It creates a new **Sprint section** in TestRail.
4. For each Jira issue:
   - Creates a **child section**.
   - Parses description & acceptance criteria.
   - Generates and posts manual test cases.

## Requirements
- **Python 3.10+**
- Jira API token with read access to issues & sprints.
- TestRail API key with permission to create sections and cases.
- Ability to create a Jira webhook or Automation rule for “Sprint started” events.

## Installation

```bash
# Clone the repo
git clone https://github.com/<your-username>/jira-testrail-ai-agent.git
cd jira-testrail-ai-agent

# Install dependencies
pip install -r requirements.txt