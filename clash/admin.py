from django.contrib import admin
from django.contrib.admin import site, AdminSite, TabularInline
from django.utils.html import format_html


# Register your models here.
from .models import Player, Clan, War, WarStats


@admin.register(Clan)
class ClanAdmin(admin.ModelAdmin):
    list_display = ('tag', 'name')

class WarStatsInline(admin.TabularInline):
    model = WarStats
    extra = 0


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):

    def get_name(self, obj):
        marker = obj.age > 2 and (
            obj.idle_days > 5 or
            obj.collect_ratio == '-' or
            int(obj.collect_ratio) < 50 or
            obj.warMisses > 2 or
            obj.total_misses > 5 or
            obj.warCount == 0
        )
        return format_html(
            '<b style="background:{};color:{}">{}</b>',
            'red' if marker else 'white',
            'white' if marker else 'navy',
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
        "age",
    )

    inlines = [WarStatsInline]

    ordering = ("clanRank",)
    list_filter = (
        "clan__name",
        "role",
        "warMisses",
        "expLevel",
        "warCount",
    )


@admin.register(War)
class WarAdmin(admin.ModelAdmin):
    list_display = (
        "seasonId",
        "createdDate",
        "clan",
    )

    ordering = ("-seasonId",)
