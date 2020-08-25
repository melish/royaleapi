from datetime import datetime, timedelta

from django.contrib import admin
from django.contrib.admin import site, AdminSite, TabularInline
from django.utils.html import format_html
from django.utils.timezone import utc
from django.db.models import Min

# Register your models here.
from .models import Player, Clan, War, WarStats


@admin.register(Clan)
class ClanAdmin(admin.ModelAdmin):
    list_display = ('tag', 'name')

class WarStatsInline(admin.TabularInline):
    model = WarStats
    extra = 0



class IdleDaysFilter(admin.SimpleListFilter):
    title = 'Idle days'
    parameter_name = 'idle_days'

    def lookups(self, request, model_admin):
        now = datetime.utcnow().replace(tzinfo=utc)
        oldest = Player.objects.filter(
            clan__isnull=False,
        ).aggregate(
            oldest=Min('lastSeen')
        ).get('oldest', now)
        delta = now - oldest
        return (
            (k, k)
            for k in range(delta.days+1)
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        value = int(self.value())
        now = datetime.utcnow().replace(tzinfo=utc)

        date_min = now - timedelta(days=(value+1))
        date_max = now - timedelta(days=value)

        return queryset.filter(
            lastSeen__range=(date_min, date_max)
        )
        return queryset


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):

    def get_name(self, obj):
        bad_marker = obj.age > 2 and (
            obj.idle_days > 5 or
            obj.collect_ratio == '-' or
            int(obj.collect_ratio) < 2 or
            obj.warMisses > 1 or
            obj.total_misses > 5 or
            obj.warCount == 0 or
            obj.idle_days > 4
        )
        good_marker = (
            obj.role == 'member' and obj.donations > 330 or
            obj.role not in ('leader', 'coLeader') and obj.warCount >= 9
        )
        return format_html(
            '<b style="background:{};color:{}">{}</b>',
            'red' if bad_marker else 'green' if good_marker else 'white',
            'white' if bad_marker or good_marker else 'navy',
            f"{obj.name} ({obj.clanRank})"
        )
    get_name.short_description = 'Name'

    list_display = (
        "get_name",
        "role",
        "expLevel",
        "trophies",
        "idle_days",
        "win_ratio",
        "collect_ratio",
        "warMisses",
        "total_misses",
        "warCount",
        "total_wars",
        "donation_ratio",
        "age_str",
    )

    inlines = [WarStatsInline]

    ordering = ("clanRank",)
    list_filter = (
        "clan__name",
        "role",
        "warMisses",
        "expLevel",
        "warCount",
        IdleDaysFilter,
    )
    search_fields = ['name']
    readonly_fields = ('created_at', )


@admin.register(War)
class WarAdmin(admin.ModelAdmin):
    list_display = (
        "seasonId",
        "createdDate",
        "clan",
    )

    ordering = ("-seasonId",)
