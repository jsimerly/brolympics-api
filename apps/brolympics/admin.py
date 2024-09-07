from django.contrib import admin
from apps.brolympics.models import *

# Register your models here.
admin.site.register(League)
admin.site.register(Brolympics)
admin.site.register(Event_IND)
admin.site.register(Event_H2H)
admin.site.register(Event_Team)
admin.site.register(OverallBrolympicsRanking)
admin.site.register(Team)
admin.site.register(Competition_Ind)
admin.site.register(Competition_H2H)
admin.site.register(Competition_Team)
admin.site.register(EventRanking_Ind)
admin.site.register(EventRanking_H2H)
admin.site.register(EventRanking_Team)
admin.site.register(Bracket_4)
admin.site.register(BracketMatchup)