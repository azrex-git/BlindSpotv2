import re
prompt = open("blindspot_reports/035/browser_interaction.md", encoding="utf-8").read()

# Find Objective
obj_match = re.search(r"Objective:\s*([^\n]+)", prompt)
print("obj_match:", obj_match.group(1) if obj_match else "None")
if obj_match:
    objective = obj_match.group(1).lower()
    print("objective:", repr(objective))
    words = ("submit a query", "search input", "primary search")
    for w in words:
        print(f"  '{w}' in objective?", w in objective)
