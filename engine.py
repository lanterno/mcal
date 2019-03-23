from datetime import datetime, timedelta
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def setup():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


class Week:
    """
    Abstracts operations to calculate the beginning, and the end of a week, based on any day on that week.
    """
    def __init__(self, today):
        self.today = today
        self.current_week_day = self.today.isoweekday()
        self._week_start = None
        self._week_end = None

    @property
    def start(self):
        if not self._week_start:
            self._week_start = self.today - timedelta(days=self.current_week_day - 1)
        return self._week_start

    @property
    def end(self):
        if not self._week_end:
            self._week_end = self.start + timedelta(days=6)
        return self._week_end


def main():
    """
    returns the number of hours used in meetings this week.
    For documentation:
     - https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.events.html#list
     - https://developers.google.com/calendar/v3/reference/events/list
    """
    creds = setup()
    service = build('calendar', 'v3', credentials=creds)

    this_week = Week(datetime.utcnow())
    # Call the Calendar API
    print("Getting this week's events")
    events_result = service.events().list(
        calendarId='primary',
        timeMin=this_week.start.isoformat() + 'Z', timeMax=this_week.end.isoformat() + 'Z',
        maxResults=2500, singleEvents=True, orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')

    total_hours_this_week = timedelta()
    for event in events:
        end = datetime.fromisoformat(event['end']['dateTime'])
        start = datetime.fromisoformat(event['start']['dateTime'])
        total_hours_this_week += end - start
    print(f"total meetings time for selected week: {total_hours_this_week}")
    time_left_for_work = timedelta(hours=40) - total_hours_this_week
    print(f"time left for work: {time_left_for_work}")
    print("Percentage of time left to work is: ~{}%".format(int(time_left_for_work.total_seconds()*100/(40*3600))))


if __name__ == '__main__':
    main()
