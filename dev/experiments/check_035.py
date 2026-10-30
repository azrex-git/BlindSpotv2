import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
content = open("blindspot_reports/035/browser_interaction.md", encoding="utf-8").read()

idx1 = content.find("### Step 1:")
idx2 = content.find("### Step 2:")
idx3 = content.find("### Step 3:")

print("Step 1 snippet:")
print(content[idx1:idx1+300])
print("\nStep 2 snippet:")
print(content[idx2:idx2+300])
print("\nStep 3 snippet:")
print(content[idx3:idx3+300])

