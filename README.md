# Google Drive Monitoring Script
This Python script monitors a user’s Google Drive, checks file permissions, and adjusts them if necessary. It uses the Google Drive API to achieve this functionality.


## Flow
1. **Monitoring new created files**
The script monitors the files using Google Drive Activity API v2 [https://developers.google.com/drive/activity/v2]
the app queries for the last 5 (approximatly) requests of file creation. If action occure in the last 60 seconds, it will trigger the next step.
2. **Public Access determinition**
To determine public access, the script queries Google Drive API v3 ([https://developers.google.com/drive/api/guides/about-sdk])
by queriing the file permissions, it was found that permission id "anyoneWithLink" means that everyone with "webViewLink" is allowed to access the file.
3. **change its permissions to private**
To change permissions, it removes permission ID "anyoneWithLink".


## Necessary Permissions:
| functionality | permission | description |
| ------ | ------ | ------ |
| Monitoring new created files | https://www.googleapis.com/auth/drive.activity.readonly | The script monitors the files using Google Drive Activity API v2, and requires readonly access to the activities
| Public Access determinition | https://www.googleapis.com/auth/drive.metadata.readonly | To determine public access, the script queries Google Drive API v3 and querying file permissions, therefore requires readonly access to the drive metadata
| change its permissions to private | https://www.googleapis.com/auth/drive | To change permissions, it is required to receive access to View and manage all of your Drive files.


## requirements
- Python 3.10.7 or greater
- pip package management tool
- A Google Cloud project
- A Google account with Google Drive enabled

## Prerequisites
1. Install required packages:
```
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

2. Create a project in the Google Developers Console.
3. Enable the Google Drive API and create OAuth 2.0 credentials.
4. Download the `credentials.json` file and place it in the same directory as the script.



## Usage
1. Run the script:
```python3 drive_monitor.py```
2. On the first usage, a web browser will pop up and will require to authorize access to the relevant google user.
3. The script will start its action.

## Usage example
```
> python3 activityquickstart.py
[*] started! Checking for new files...
[*] New item was found to be created with the id 1NXYetOliKxfouKUeaipyNkst4_TjOjxf
[1NXYetOliKxfouKUeaipyNkst4_TjOjxf] Checking if file is publicly accessible...
[*] retreived file metadata
[1NXYetOliKxfouKUeaipyNkst4_TjOjxf] is_file_publicly_accessible: Yes
[1NXYetOliKxfouKUeaipyNkst4_TjOjxf] Checking if parent folder is publicly accessible
[1NXYetOliKxfouKUeaipyNkst4_TjOjxf] Removing public access...
[1NXYetOliKxfouKUeaipyNkst4_TjOjxf] permissions removed: Successfully
[*] started! Checking for new files...
[!] No new files found.
[*] started! Checking for new files...
[!] No new files found.
```

## Known Issues
- Rate Limits: The Google Drive API has rate limits, which could affect the frequency of monitoring.
- Handling Large Drives: For users with a large number of files, efficiently monitoring all files might require optimizations.
- Authorization Flow: Users need to authenticate the script with their Google account, which might be inconvenient or pose security concerns.
- Only a single user is monitored at the same time

## Interesting Attack Surfaces:
- by default, API key is unrestricted. To prevent unauthorized use and quota theft, restrict your key to limit how it can be used.
- **Unauthorized Access**: If the script's OAuth2 tokens are compromised, an attacker could gain unauthorized access to the user's Google Drive. The script stores the credentials within a file, but it is your responsibility to store it safely.
- **Data Leakage**: If sensitive files are mistakenly shared publicly, they could be accessed by unauthorized users who may have access to a publicly available folder or file.
- **API Abuse**: Malicious actors could potentially abuse the Google Drive API to perform unauthorized actions or gather information about users' files. 
Because in order to simply remove a permission, it requires to allow view and manage to all drive files:
https://www.googleapis.com/auth/drive
instead of simply allowing to only remove permissions (something that should be in https://www.googleapis.com/auth/drive.metadata)
this is documented at:
https://developers.google.com/drive/api/reference/rest/v3/permissions/delete
In case of intrusion to the app, threat actors may end up with permission to access, modify and create files files of all users of the app
- **Impersonation**: actions are made on behalf of the logged on user who allowed the permissions. Malicious threat actor may abuse this functionality to perform actions by the app and make them look like the logged in user was doing them.
