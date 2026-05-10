import re, json

def parse_storyboard(text):
    """Strip markdown code fences and parse JSON from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
    return json.loads(text)
