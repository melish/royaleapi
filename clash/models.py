from django.db import models
from django.utils.timezone import utc
from datetime import datetime


class Clan(models.Model):
    tag = models.CharField(max_length=16)
    name = models.CharField(max_length=128)

    def __str__(self):
        return "%s (%s)" % (self.name, self.tag)


class War(models.Model):
    seasonId = models.IntegerField()
    createdDate = models.DateField()
    clan = models.ForeignKey(
        Clan, null=True, on_delete=models.SET_NULL, related_name="players"
    )

    def __str__(self):
        date_str = self.createdDate.strftime("%Y-%m-%d") if self.createdDate else None
        return f"{self.seasonId} ({date_str})"


class PlayerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("clan").prefetch_related("wars")


class Player(models.Model):

    objects = PlayerManager()

    tag = models.CharField(max_length=16)
    name = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    clan = models.ForeignKey(Clan, null=True, on_delete=models.SET_NULL)
    role = models.CharField(max_length=16, blank=True)
    clanRank = models.IntegerField(default=0)
    trophies = models.IntegerField(default=0)

    # wars = models.ManyToManyField(War, related_name="players")
    wars = models.ManyToManyField(War, through="WarStats")

    lastSeen = models.DateTimeField(null=True)
    donations = models.IntegerField(default=0)
    donationsReceived = models.IntegerField(default=0)
    expLevel = models.IntegerField(default=0)

    # total misses for last 10 wars
    warMisses = models.IntegerField(default=0)

    # total participations for last 10 wars
    warCount = models.IntegerField(default=0)

    @property
    def total_wars(self):
        return self.wars.count()

    @property
    def win_ratio(self):
        wins = 0
        total = 0
        for w in self.warstats_set.all():
            wins += w.wins
            total += w.numberOfBattles
        return "{}%".format(int(100 * wins / total)) if total > 0 else "-"

    @property
    def collect_ratio(self):
        return (
            int(
                10
                * sum(w.collectionDayBattlesPlayed for w in self.warstats_set.all())
                / self.wars.count()
            ) / 10
            if self.wars.count() > 0
            else "-"
        )

    @property
    def total_misses(self):
        return sum(w.numberOfBattles - w.battlesPlayed for w in self.warstats_set.all())

    @property
    def idle_days(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        if not self.lastSeen:
            return 999
        delta = now - self.lastSeen
        return delta.days

    @property
    def age(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        delta = now - self.created_at
        return int(10*delta.total_seconds()/3600/24)/10

    @property
    def age_str(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        delta = now - self.created_at
        if delta.days > 3:
            return f"{delta.days}d"

        hours = int(delta.seconds/3600)
        return f"{delta.days}d {hours}h"

    @property
    def donation_ratio(self):
        return self.donations - self.donationsReceived

    def __str__(self):
        return "%s (%s)" % (self.name, self.tag)


class WarStats(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    war = models.ForeignKey(War, on_delete=models.CASCADE)

    numberOfBattles = models.IntegerField()
    battlesPlayed = models.IntegerField()
    wins = models.IntegerField()
    collectionDayBattlesPlayed = models.IntegerField()

    def __str__(self):
        return f"{self.war.seasonId} | {self.player.name}"
