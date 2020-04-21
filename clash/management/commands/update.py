import logging
import json
import requests
import os
from datetime import datetime

from collections import defaultdict
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from clash.models import Clan, Player, War, WarStats

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)

logger = logging.getLogger(__name__)

API_TOKEN = settings.API_TOKEN


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y%m%dT%H%M%S.%f%z")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("clan_tag", nargs="?", help="Clan tag without #")
        parser.add_argument(
            "--no-cache",
            action="store_true",
            default=False,
            help="Don't use cached data",
        )

    def handle(self, *args, **options):
        if options["clan_tag"]:
            clans = [options["clan_tag"]]
        else:
            clans = [clan.tag for clan in Clan.objects.all()]

        for clan_tag in clans:
            members_data = self.init_data(clan_tag, "members", options["no_cache"])
            war_data = self.init_data(clan_tag, "warlog", options["no_cache"])
            self.process_data(clan_tag, members_data, war_data)

    def init_data(self, clan_tag, api_method, no_cache):
        cache_dir = ".cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        filename = os.path.join(cache_dir, f"{clan_tag}_{api_method}.json")
        if not os.path.isfile(filename) or no_cache:
            logger.debug(f"Downloading data for {api_method}")
            r = self.make_request(clan_tag, api_method)
            data = r.json()
            if r.status_code == 200:
                with open(filename, "w") as f:
                    json.dump(data, f, indent=2)
                return data
            else:
                raise CommandError(f"API error {r.status_code}: {api_method} {data}")
        else:
            logger.debug(f"Using cached data for {api_method}")
            with open(filename) as json_file:
                return json.load(json_file)

    def make_request(self, clan_tag, api_method):
        r = requests.get(
            f"https://api.clashroyale.com/v1/clans/%23{clan_tag}/{api_method}",
            headers={
                "Accept": "application/json",
                "authorization": f"Bearer {API_TOKEN}",
            },
        )
        logger.debug(f"API request {api_method}, status_code={r.status_code}")
        return r

    def process_data(self, clan_tag, members_data, war_data):
        # compute war data for each member
        players = {}
        clan, _ = Clan.objects.get_or_create(tag=clan_tag)
        logger.debug(f"Processing clan {clan.name}")
        for member in members_data["items"]:
            tag = member["tag"]
            player, created = Player.objects.get_or_create(tag=tag,)
            players[tag] = player
            player.clan = clan
            attrs = (
                "name",
                "role",
                "clanRank",
                "donations",
                "donationsReceived",
                "expLevel",
                "trophies",
            )
            for attr in attrs:
                setattr(player, attr, member[attr])
            player.lastSeen = parse_date(member["lastSeen"])
            player.save()

        # remove members no longer here
        Player.objects.filter(
            clan=clan,
        ).exclude(
            tag__in=players.keys(),
        ).update(
            clan=None,
            clanRank=999,
            role='',
        )

        # to store number of misses for last 10 wars
        # key=player tag, value = {'misses': x, 'warCount': y}
        globalstats = defaultdict(lambda: defaultdict(int))

        for war in war_data["items"]:
            war_date = parse_date(war["createdDate"])
            warObj, _ = War.objects.get_or_create(
                seasonId=war["seasonId"],
                createdDate=war_date,
                defaults={
                    "seasonId": war["seasonId"],
                    "createdDate": war_date,
                    "clan": clan,
                },
            )
            logger.debug(f"Processing war on {warObj.createdDate}")

            # key=player tag, value=number of missed battles

            for player_data in war["participants"]:
                tag = player_data["tag"]
                if tag not in players:
                    player, created = Player.objects.get_or_create(
                        tag=tag, defaults={"name": player_data["name"], "clanRank": 99,}
                    )
                    players[tag] = player
                    if not created:
                        # player used to be a member, but not anymore
                        player.clanRank = 99
                        player.role = ""
                        player.clan = None
                        player.save()

                player = players[tag]

                player_war_data, _ = WarStats.objects.get_or_create(
                    war=warObj,
                    player=player,
                    defaults={
                        key: player_data[key]
                        for key in (
                            "numberOfBattles",
                            "battlesPlayed",
                            "wins",
                            "collectionDayBattlesPlayed",
                        )
                    },
                )
                globalstats[tag]["created_at"] = min(war_date, player.created_at)
                globalstats[tag]["lastSeen"] = (
                    max(war_date, player.lastSeen) if player.lastSeen else war_date
                )
                globalstats[tag]["warMisses"] += (
                    player_data["numberOfBattles"] - player_data["battlesPlayed"]
                )
                globalstats[tag]["warCount"] += 1

        # update global stats for players
        for tag in globalstats:
            player = players[tag]
            attrs = (
                "created_at",
                "warMisses",
                "warCount",
                "lastSeen",
            )
            for attr in attrs:
                setattr(player, attr, globalstats[tag][attr])
            players[tag].save()
