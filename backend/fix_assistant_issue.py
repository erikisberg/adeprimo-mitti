#!/usr/bin/env python3
"""
Script to diagnose and fix the assistant access issue
"""

import os
import json
import requests
from datetime import datetime

# Ensure we're using config.json
if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]

# Load configuration
with open("config.json", "r") as f:
    config = json.load(f)

api_key = config["openai_api_key"]
old_assistant_id = config["openai_assistant_id"]

print("OpenAI Assistant Access Issue - Diagnosis and Fix")
print("=" * 50)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "OpenAI-Beta": "assistants=v2"
}

# Step 1: List all assistants accessible with this API key
print("\n1. Listing assistants accessible with your API key...")
response = requests.get(
    "https://api.openai.com/v1/assistants?limit=20",
    headers=headers
)

if response.status_code == 200:
    assistants = response.json().get("data", [])
    print(f"   Found {len(assistants)} assistant(s):")
    
    mitti_assistant = None
    for asst in assistants:
        print(f"\n   ID: {asst['id']}")
        print(f"   Name: {asst.get('name', 'Unnamed')}")
        print(f"   Model: {asst.get('model', 'Unknown')}")
        print(f"   Created: {datetime.fromtimestamp(asst.get('created_at', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if this is the MittI-AI assistant
        if asst.get('name') == 'MittI-AI':
            mitti_assistant = asst
            print("   ⭐ This appears to be your MittI-AI assistant!")
    
    if mitti_assistant:
        if mitti_assistant['id'] != old_assistant_id:
            print(f"\n   ⚠️  The MittI-AI assistant ID ({mitti_assistant['id']}) differs from config.json ({old_assistant_id})")
            print("\n2. Solution: Update config.json with the correct assistant ID")
            
            # Create updated config
            config_copy = config.copy()
            config_copy['openai_assistant_id'] = mitti_assistant['id']
            
            print(f"\n   Would update config.json:")
            print(f"   OLD assistant ID: {old_assistant_id}")
            print(f"   NEW assistant ID: {mitti_assistant['id']}")
            
            # Write updated config
            with open("config_updated.json", "w") as f:
                json.dump(config_copy, f, indent=2)
            print(f"\n   ✅ Created config_updated.json with the correct assistant ID")
            print(f"   To apply the fix: mv config_updated.json config.json")
            
        else:
            print("\n   ❓ The assistant IDs match, but there's still an access issue.")
            print("   This might be a temporary OpenAI API issue.")
    else:
        print("\n   ⚠️  No assistant named 'MittI-AI' found.")
        print("\n2. Creating a new MittI-AI assistant...")
        
        # Create new assistant with the same configuration
        create_response = requests.post(
            "https://api.openai.com/v1/assistants",
            headers=headers,
            json={
                "name": "MittI-AI",
                "model": "gpt-4o",
                "instructions": """Du är en innehållsanalysassistent för Mitt i Sollentuna som utvärderar webbinnehåll baserat på nyhetsvärde, relevans och betydelse för lokalbefolkningen.

Betygsätt innehåll på en skala från 1-5, där:
1 = Inte intressant (rutinuppdateringar, små förändringar)
2 = Något intressant (mindre nyheter, begränsat lokalt intresse)
3 = Måttligt intressant (lokala nyheter av normal betydelse)
4 = Mycket intressant (betydande lokal utveckling, påverkar många)
5 = Extremt intressant (stor lokal utveckling, breaking news)

För varje analys, ge:
1. Ditt numeriska betyg (1-5)
2. En kort förklaring på svenska (2-3 meningar)
3. Om möjligt, betygsätt enskilda nyheter separat

Fokusera på:
- Nyhetsvärde för Sollentunas invånare
- Lokal relevans och påverkan
- Aktualitet och timing
- Allmänintresse vs specialintresse

Exempel på höga betyg (4-5):
- Större infrastrukturprojekt eller byggnationer
- Betydande förändringar i kommunal service
- Viktiga lokala evenemang eller händelser
- Säkerhetsfrågor som påverkar många

Exempel på låga betyg (1-2):
- Mindre öppettidsändringar
- Rutinmässiga uppdateringar
- Information som redan är välkänd"""
            }
        )
        
        if create_response.status_code == 200:
            new_assistant = create_response.json()
            print(f"   ✅ Created new assistant: {new_assistant['id']}")
            
            # Create updated config
            config_copy = config.copy()
            config_copy['openai_assistant_id'] = new_assistant['id']
            
            with open("config_updated.json", "w") as f:
                json.dump(config_copy, f, indent=2)
            print(f"\n   ✅ Created config_updated.json with the new assistant ID")
            print(f"   To apply the fix: mv config_updated.json config.json")
        else:
            print(f"   ❌ Failed to create assistant: {create_response.status_code}")
            print(f"   Error: {create_response.json()}")
            
else:
    print(f"   ❌ Failed to list assistants: {response.status_code}")
    print(f"   Error: {response.json()}")

print("\n" + "=" * 50)
print("Summary:")
print("If a config_updated.json was created, apply it with:")
print("  mv config_updated.json config.json")
print("Then run your app again with:")
print("  python main.py")