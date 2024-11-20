import os

# Path to credentials.json
credentials_path = os.path.join(os.getcwd(), 'credentials.json')

# Check if file exists
if os.path.exists(credentials_path):
    print("The credentials.json file exists and is accessible.")
else:
    print("The credentials.json file is missing or inaccessible.")
