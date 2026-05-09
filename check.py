import os
from datetime import datetime, timezone, timedelta
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_CHANNEL_ID = os.environ["SLACK_CHANNEL_ID"]
API_URL = os.environ["API_URL"]
TIMESTAMP_FIELD = os.environ.get("TIMESTAMP_FIELD", "timestamp")
TIMEZONE = os.environ["TIMEZONE"]
THRESHOLD_MINUTES = 120
SITES = [
    { 'table': "north_fork_0",  'label': "North Fork 0" },
    { 'table': "scnf010",       'label': "North Fork 1 (Wickson Footbridge)" },
    { 'table': "south_fork_0",  'label': "South Fork 0" },
    { 'table': "south_fork_1",  'label': "South Fork 1" },
    { 'table': "south_fork_2",  'label': "South Fork 2" },
    { 'table': "south_fork_3",  'label': "South Fork 3" },
    { 'table': "university_house", 'label': "University House" },
    { 'table': "oxford",        'label': "Oxford Street" },
    { 'table': "codornices",    'label': "Codornices Creek" },
    { 'table': "kingman_hall",    'label': "Kingman Hall" },
    { 'table': "botanical_garden",    'label': "Botanical Garden" },
  ]
slack = WebClient(token=SLACK_BOT_TOKEN)


# def get_nested_field(data: dict, path: str):
#     """Resolve dot-notation field paths e.g. 'data.meta.updatedAt'"""
#     for key in path.split("."):
#         if not isinstance(data, dict):
#             return None
#         data = data.get(key)
#     return data


# def format_age(minutes: float) -> str:
#     if minutes < 60:
#         return f"{round(minutes)} minutes"
#     hours = int(minutes // 60)
#     mins = round(minutes % 60)
#     return f"{hours}h {mins}m"


def send_alert(message: str):
    try:
        res = slack.chat_postMessage(channel=SLACK_CHANNEL_ID, text=message)
        print(f"{res['ts']}: Alert sent to Slack.")
    except SlackApiError as e:
        print(f"Failed to send Slack message: {e.response['error']}")

def delete_alert(ts: str):
    try:
        slack.chat_delete(channel=SLACK_CHANNEL_ID, ts=ts)
        print("Alert deleted from the Channel.")
    except SlackApiError as e:
        print(f"Failed to delete Slack message: {e.response['error']}")

def check_timestamp():
    # Fetch data from API
    send_alert(f"[{datetime.now(timezone.utc).astimezone(ZoneInfo(TIMEZONE)).replace(microsecond=0)}]\n🦦 Running daily check...")
    print(f"[{datetime.now(timezone.utc).astimezone(ZoneInfo(TIMEZONE)).replace(microsecond=0)}] 🦦 Running daily check...")
    stale_sensors = []

    for site in SITES:
        try:
            url = f"https://www.strawberrycreek.org/api/creek-data/?site={site['table']}&start={(datetime.now(timezone.utc) - timedelta(minutes=THRESHOLD_MINUTES)).isoformat()}&end={datetime.now(timezone.utc).isoformat()}&vars=Meter_Hydros21_Cond,Meter_Hydros21_Depth,Meter_Hydros21_Temp,EnviroDIY_Mayfly_Batt"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not len(data):
                stale_sensors.append(site['label'])
        except requests.RequestException as e:
            send_alert(f":x: *API Request Failed*\nCould not reach `{API_URL}`\n*Error:* {e}")
            return

    if len(stale_sensors) == 0:
        send_alert("All the sensors look good!")
    else:
        send_alert(f"There are (${len(stale_sensors)}) sensors that haven't updated in the past 2 hours:\n" + '\n'.join(stale_sensors))

    # # Extract timestamp field
    # raw_timestamp = get_nested_field(data, TIMESTAMP_FIELD)
    # if raw_timestamp is None:
    #     send_alert(
    #         f":warning: *Missing Timestamp*\n"
    #         f"Field `{TIMESTAMP_FIELD}` not found in API response.\n"
    #         f"*Response:* ```{str(data)[:500]}```"
    #     )
    #     return

    # Parse timestamp
    # try:
    #     object_time = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
    # except (ValueError, AttributeError):
    #     send_alert(f":warning: *Invalid Timestamp*\nCould not parse `{TIMESTAMP_FIELD}`: `{raw_timestamp}`")
    #     return

    # # Compare with current time
    # now = datetime.now(timezone.utc)
    # diff_minutes = (now - object_time).total_seconds() / 60

    # if diff_minutes > THRESHOLD_MINUTES:
    #     age = format_age(diff_minutes)
        # send_alert(
        #     f":rotating_light: *Stale Timestamp Detected*\n"
        #     f"*Field:* `{TIMESTAMP_FIELD}`\n"
        #     f"*Object time:* {object_time.isoformat()}\n"
        #     f"*Current time:* {now.isoformat()}\n"
        #     f"*Age:* {age} *(threshold: {THRESHOLD_MINUTES} min)*"
        # )
    # else:
    #     print(f"Timestamp is fresh ({diff_minutes:.1f} min old). No alert sent.")


if __name__ == "__main__":
    check_timestamp()