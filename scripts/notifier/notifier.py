import google.generativeai as genai
import os
import os.path
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

model = genai.GenerativeModel("gemini-1.5-flash")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_calendar_service() -> build:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        return build("calendar", "v3", credentials=creds)
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def get_calendar_events() -> list:
    service = get_calendar_service()
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    print("[i] Getting the upcoming 10 events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=100,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    res = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        res.append({
            "date": start,
            "summary": event["summary"]
        })
    return res




def test_generate_content():
    response = model.generate_content("Write a story about a magic backpack.")
    print(response.text)


if __name__ == "__main__":
    # test_generate_content()
    events = get_calendar_events()
    print(events[0])
