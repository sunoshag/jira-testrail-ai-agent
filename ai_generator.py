from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam  # ← typed dict
import os, json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_test_case_from_jira(issue):
    key = issue.get("key")
    summary = issue.get("fields", {}).get("summary", "")
    description = issue.get("fields", {}).get("description", "")

    prompt = f"""
You are an expert QA engineer...
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

    # 👇 Correctly typed messages
    messages: list[ChatCompletionUserMessageParam] = [
        {"role": "user", "content": prompt}
    ]

    resp = client.chat.completions.create(
        model="gpt-5",
        messages=messages,           # ✅ satisfies the type checker
    )

    try:
        return json.loads(resp.choices[0].message.content)
    except json.JSONDecodeError:
        return []
