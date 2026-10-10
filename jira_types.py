import os, requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()
url = 'https://j8goncalves.atlassian.net/rest/api/3/project/DS'
email = os.getenv('JIRA_EMAIL')
token = os.getenv('JIRA_API_TOKEN')

if not email or not token:
    print("No creds in .env")
    exit(1)

res = requests.get(url, auth=HTTPBasicAuth(email, token))
if res.status_code == 200:
    data = res.json()
    types = data.get('issueTypes', [])
    for t in types:
        print(f"ID: {t['id']}, Name: {t['name']}")
else:
    print('Error:', res.text)
