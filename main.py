from config import     TESTRAIL_PROJECT_ID, TESTRAIL_SUITE_ID, JIRA_BOARD_ID

from testrail_helpers import testrail_add_section, testrail_add_case, find_section_by_name

from jira_helpers import jira_get_active_sprint, jira_get_sprint_issues

from ac_parser import extract_acceptance_criteria, ac_to_steps_and_expected

def process_active_sprint():
    sprint = jira_get_active_sprint(JIRA_BOARD_ID)
    if not sprint:
        print("No active sprint found.")
        return

    sprint_id = sprint.get("id")
    sprint_name = sprint.get("name", f"Sprint {sprint_id}")
    print(f"Processing active sprint: {sprint_name}")

    # Stop if sprint section already exists
    sprint_section = find_section_by_name(TESTRAIL_PROJECT_ID, TESTRAIL_SUITE_ID, sprint_name)
    if sprint_section:
        print("Sprint section already exists. Exiting...")
        return

    # Otherwise, create the sprint section
    sprint_section_id = testrail_add_section(
        TESTRAIL_PROJECT_ID,
        sprint_name,
        TESTRAIL_SUITE_ID,
        description=f"Auto-created for Jira sprint {sprint_id}"
    )["id"]
    print(f"🆕 Created sprint section: {sprint_name}")

    # Process issues
    issues = jira_get_sprint_issues(sprint_id)
    for issue in issues:
        key = issue.get("key")
        issue_section_name = issue.get("fields", {}).get("summary", "")
        
        issue_section_id = testrail_add_section(
            TESTRAIL_PROJECT_ID,
            issue_section_name,
            TESTRAIL_SUITE_ID,
            parent_id=sprint_section_id,
            description=f"Tests for {issue_section_name}"
        )["id"]
        print(f"   🆕 Created section for {key}")

        # Create test cases from AC
        ac_list = extract_acceptance_criteria(issue)
        for idx, ac in enumerate(ac_list, start=1):
            steps, expected = ac_to_steps_and_expected(ac)
            payload_case = {
                "title": f"Test case {idx}: {ac[:80]}",
                "template_id": 2,
                "type_id": 1,
                "priority_id": 2,
                "refs": key,
                "custom_preconds": (issue.get("fields", {}).get("description") or "")[:2000],
                "custom_steps_separated": steps,
                "custom_expected":"Expected result goes here"
        }
            if expected:
                payload_case["custom_expected"] = expected
            testrail_add_case(issue_section_id, payload_case)
            print(f"      🆕 Created case: {key} - AC {idx}")

# --- Startup: automatically process active sprint ---
if __name__ == "__main__":
    process_active_sprint()  # <--- runs immediately on script start