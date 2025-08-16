import re

def extract_acceptance_criteria(issue):
    desc = issue.get("fields", {}).get("description") or ""
    text = desc if isinstance(desc, str) else str(desc)
    m = re.search(r"(?i)acceptance criteria[:\n]*([\s\S]+?)(?:\n\n|$)", text)
    if m:
        block = m.group(1).strip()
        items = re.split(r"\n\s*[-*•]|\n\s*\d+\.|\n\s*•", block)
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
        given = re.search(r"(?i)Given[:\s]*(.*?)(?=When|$)", ac_text)
        when = re.search(r"(?i)When[:\s]*(.*?)(?=Then|$)", ac_text)
        then = re.search(r"(?i)Then[:\s]*(.*?)(?=$)", ac_text)
        steps = []
        if given: steps.append({"content": "Precondition: " + given.group(1).strip(), "expected": ""})
        if when: steps.append({"content": "Action: " + when.group(1).strip(), "expected": ""})
        expected = then.group(1).strip() if then else ""
        if expected == "" and len(steps)==1: expected = steps[0]["content"]
        return steps, expected
    lines = [ln.strip() for ln in re.split(r"\n|;|\.|\*|-", ac_text) if ln.strip()]
    if len(lines) == 1: return ([{"content": lines[0], "expected": ""}], lines[0])
    steps = [{"content": l, "expected": ""} for l in lines]
    expected = steps[-1]["content"] if steps else ""
    return steps, expected