#!/usr/bin/env python3
"""
Fix the status setting in monitor.py
"""

import re

# Read the file
with open('monitor.py', 'r') as f:
    content = f.read()

# Replace pattern - find result["status"] = "success" and replace with conditional
old_pattern = r'(\s+)result\["status"\] = "success"'
new_pattern = r'''\1# Set status based on whether analysis was performed
\1if result.get("analyzed"):
\1    result["status"] = "analyzed"
\1else:
\1    result["status"] = "success"'''

# Perform the replacement
new_content = re.sub(old_pattern, new_pattern, content)

# Write back
with open('monitor.py', 'w') as f:
    f.write(new_content)

print("Fixed monitor.py - status will now be set to 'analyzed' when analysis is performed")