import json
import logging
import requests

from collections import defaultdict

CLAN_TAG = "PQVYL0G2"
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImRlNWY4NzI4LWVkYjYtNGVhOS1iMGRhLTY1MWRkODgxOWM2OSIsImlhdCI6MTU4NzM2MDcwOCwic3ViIjoiZGV2ZWxvcGVyLzAyYjZhMTE0LTM2Y2QtOTJlNi1hOGNhLWE2NjRlNWQ4OTlhYSIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyI1LjEyLjgxLjI1MSIsIjUuMi4xNTguMjQzIl0sInR5cGUiOiJjbGllbnQifV19.ixaU_oTwQ9UbUV4y__OYPubcfxTMkCJj0rGCina848XHFPiIsGdQWBPXUmUUcXdmKmLyTRd2lfffUIdy0RPh-A"

logging.basicConfig(filename='debug.log',level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

def make_request(api_method):
    r = requests.get(
        f"https://api.clashroyale.com/v1/clans/%23{CLAN_TAG}/{api_method}",
        headers={
            "Accept": "application/json",
            "authorization": f"Bearer {API_TOKEN}",
        },
    )
    logging.debug(f"API request {api_method}, status_code={r.status_code}")
    return r


# war_data = make_request('warlog').json()
# members_data = make_request('members').json()

with open('members.json') as json_file:
    members_data = json.load(json_file)

with open('warlog.json') as json_file:
    war_data = json.load(json_file)

# compute war data for each member
player_data = defaultdict(lambda: {
    key: {} for key in ('war',) 
})

for member in members_data['items']:
    tag = member['tag']
    player_data[tag] = {
        k: member[k]
        for k in ('tag', 'name', 'lastSeen', 'donations', 'donationsReceived', 'expLevel', 'role')
    }
    player_data[tag]['war'] = {}

for war in war_data['items']:
    for player in war['participants']:
        tag = player['tag']
        player_data[tag]['war'][war['seasonId']] = {
            k: player[k]
            for k in ('numberOfBattles', 'battlesPlayed', 'wins', 'collectionDayBattlesPlayed')
        }

with open("output.json" , "w") as outfile:
    json.dump(player_data, outfile, indent=2)


# print(json.dumps(r.json(), indent = 2))
# with open("output.json", "w") as outfile:
#     json.dump(r.json(), outfile, indent=2)
