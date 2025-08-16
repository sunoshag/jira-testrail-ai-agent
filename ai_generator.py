from openai import OpenAI
import os

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_test_case_from_jira(issue):
    """
    Uses AI to analyze Jira issue and generate test cases
    """
    key = issue.get("key")
    summary = issue.get("fields", {}).get("summary", "")
    description = issue.get("fields", {}).get("description", "")

    prompt = f"""
    You are an expert QA engineer.
    Analyse the following Jira ticket and generate one or more manual test cases.

    Jira Key: {key}
    Summary: {summary}
    Description: {description}

    Output format (JSON):
    [
      {{
        "title": "Test Case Title",
        "steps": ["Step 1", "Step 2", "..."],
        "expected_result": "Expected outcome"
      }}
    ]
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    try:
        return eval(response.choices[0].message.content)  # parse JSON string into Python object
    except:
        return []