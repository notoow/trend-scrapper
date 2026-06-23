import json
import base64
import os

# Read the .env.example file
with open("c:/Users/alpha/Desktop/WOOTAN/@Programming/260623 urology-recka/.env.example", "r", encoding="utf-8") as f:
    content = f.read()

# Extract GEMINI_API_KEY
gemini_key = ""
for line in content.split("\n"):
    if line.startswith("GEMINI_API_KEY="):
        gemini_key = line.split("=", 1)[1].strip()
        break

# Extract GROQ_API_KEY
groq_key = ""
for line in content.split("\n"):
    if line.startswith("GROQ_API_KEY="):
        groq_key = line.split("=", 1)[1].strip()
        break

# Extract GOOGLE_SHEETS_ID
sheets_id = ""
for line in content.split("\n"):
    if line.startswith("GOOGLE_SHEETS_ID="):
        sheets_id = line.split("=", 1)[1].strip()
        break

# Extract NEWSAPI_KEY
newsapi_key = ""
for line in content.split("\n"):
    if line.startswith("NEWSAPI_KEY="):
        newsapi_key = line.split("=", 1)[1].strip()
        break

# Extract the JSON block
json_start = content.find("GOOGLE_SERVICE_ACCOUNT_JSON={")
json_end = content.find("}", json_start) + 1
json_str = content[json_start + len("GOOGLE_SERVICE_ACCOUNT_JSON="):json_end].strip()

# Base64 encode the JSON string to avoid multi-line env parsing issues
json_bytes = json_str.encode('utf-8')
b64_json = base64.b64encode(json_bytes).decode('utf-8')

# Write to .env
env_content = f"""GEMINI_API_KEY={gemini_key}
GROQ_API_KEY={groq_key}
GOOGLE_SHEETS_ID={sheets_id}
GOOGLE_SERVICE_ACCOUNT_JSON={b64_json}
NEWSAPI_KEY={newsapi_key}
"""

with open("c:/Users/alpha/Desktop/WOOTAN/@Programming/260623 urology-recka/.env", "w", encoding="utf-8") as f:
    f.write(env_content)

print("Successfully generated .env file with Base64 encoded Service Account JSON!")
