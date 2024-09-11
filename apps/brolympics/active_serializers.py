from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.brolympics.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from apps.brolympics.serializers import CompetitionSerializer_H2h, CompetitionSerializer_Ind, CompetitionSerializer_Team, BracketCompetitionSerializer_H2h, PlayerSerializer

class HomeEventSerializer_H2h(serializers.ModelSerializer):
    percent_complete = serializers.SerializerMethodField()

    class Meta:
        model = Event_H2H
        fields = ['name', 'uuid', 'percent_complete', 'start_time']

    def get_percent_complete(self, obj):
        return obj.get_percent_complete()
    
class HomeEventSerializer_Ind(serializers.ModelSerializer):
    percent_complete = serializers.SerializerMethodField()

    class Meta:
        model = Event_IND
        fields = ['name', 'uuid', 'percent_complete', 'start_time']

    def get_percent_complete(self, obj):
        return obj.get_percent_complete()
    
class HomeEventSerializer_Team(serializers.ModelSerializer):
    percent_complete = serializers.SerializerMethodField()

    class Meta:
        model = Event_Team
        fields = ['name', 'uuid', 'percent_complete', 'start_time']

    def get_percent_complete(self, obj):
        return obj.get_percent_complete()
    

class CompetitionMScoresSerializer_H2h(CompetitionSerializer_H2h):
    max_score = serializers.SerializerMethodField()
    min_score = serializers.SerializerMethodField()

    class Meta(CompetitionSerializer_H2h.Meta):
        fields = CompetitionSerializer_H2h.Meta.fields + ['max_score', 'min_score']

    def get_max_score(self, obj):
        return obj.event.max_score

    def get_min_score(self, obj):
        return obj.event.min_score
    
class CompetitionMScoresSerializer_Bracket(BracketCompetitionSerializer_H2h):
    max_score = serializers.SerializerMethodField()
    min_score = serializers.SerializerMethodField()

    class Meta(BracketCompetitionSerializer_H2h.Meta):
        fields = BracketCompetitionSerializer_H2h.Meta.fields + ['max_score', 'min_score']

    def get_max_score(self, obj):
        return obj.event.max_score

    def get_min_score(self, obj):
        return obj.event.min_score
    
class CompetitionMScoresSerializer_Ind(CompetitionSerializer_Ind):
    max_score = serializers.SerializerMethodField()
    min_score = serializers.SerializerMethodField()

    class Meta(CompetitionSerializer_Ind.Meta):
        fields = CompetitionSerializer_Ind.Meta.fields + ['max_score', 'min_score']

    def get_max_score(self, obj):
        return obj.event.max_score

    def get_min_score(self, obj):
        return obj.event.min_score
    
class CompetitionMScoresSerializer_Team(CompetitionSerializer_Team):
    max_score = serializers.SerializerMethodField()
    min_score = serializers.SerializerMethodField()

    class Meta(CompetitionSerializer_Team.Meta):
        fields = CompetitionSerializer_Team.Meta.fields + ['max_score', 'min_score']

    def get_max_score(self, obj):
        return obj.event.max_score

    def get_min_score(self, obj):
        return obj.event.min_score
    

class EventRankingSerializer_H2h(serializers.ModelSerializer):
    comps = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    decimal_places = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    class Meta:
        model = EventRanking_H2H
        fields = ['rank', 'points', 'wins', 'losses', 'ties', 'win_rate', 'score_for', 'score_against', 'sos_wins', 'sos_losses', 'sos_ties', 'is_final', 'comps', 'type', 'name', 'decimal_places', 'is_active', 'uuid']

    def get_comps(self, obj):
        comps = Competition_H2H.objects.filter(
            Q(team_1=obj.team) | Q(team_2=obj.team),
            event=obj.event
        )
        return CompetitionSerializer_H2h(comps, many=True).data
    
    def get_type(self, obj):
        return 'h2h'

    def get_name(self, obj):
        return obj.event.name

    def get_decimal_places(self,obj):
        event_dec = obj.event.score_type
        if event_dec == 'B':
            return -1
        if event_dec == 'I':
            return 0
        if event_dec == 'F':
            return 16
        return int(event_dec)
    
    def get_is_active(self, obj):
        return obj.event.is_active
    
    def get_event_uuid(self, obj):
        return obj.event.uuid

class EventRankingSerializer_Ind(serializers.ModelSerializer):
    comps = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    decimal_places = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    class Meta:
        model = EventRanking_Ind
        fields = ['rank', 'points', 'is_final', 'comps', 'type', 'name', 'score', 'decimal_places', 'is_active', 'uuid']

    def get_comps(self, obj):
        comps = Competition_Ind.objects.filter(team=obj.team, event=obj.event)
        return CompetitionSerializer_Ind(comps, many=True).data
    
    def get_type(self, obj):
        return 'ind'

    def get_name(self, obj):
        return obj.event.name
    
    
    def get_score(self, obj):
        if obj.event.display_avg_scores:
            score = obj.team_avg_score
        else:
            score = obj.team_total_score

        if score is None:
            return None

        return round(score, obj.event.get_decimal_value())
    
    def get_decimal_places(self,obj):
        event_dec = obj.event.score_type
        if event_dec == 'B':
            return -1
        if event_dec == 'I':
            return 0
        if event_dec == 'F':
            return 16
        return int(event_dec)
    
    def get_is_active(self, obj):
        return obj.event.is_active
    
    def get_event_uuid(self, obj):
        return obj.event.uuid


class EventRankingSerializer_Team(serializers.ModelSerializer):
    comps = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    decimal_places = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = EventRanking_Team
        fields = ['rank', 'points', 'is_final', 'comps', 'type', 'name', 'score', 'decimal_places', 'is_active', 'is_final', 'uuid']

    def get_comps(self, obj):
        comps = Competition_Team.objects.filter(team=obj.team, event=obj.event)
        return CompetitionSerializer_Team(comps, many=True).data
    
    def get_type(self, obj):
        return 'team'
    
    def get_name(self, obj):
        return obj.event.name
    
    def get_score(self, obj):
        if obj.event.display_avg_scores:
            score = obj.team_avg_score
        else:
            score = obj.team_total_score

        if score is None:
            return None

        return round(score, obj.event.get_decimal_value())
    
    def get_decimal_places(self,obj):
        event_dec = obj.event.score_type
        if event_dec == 'B':
            return -1
        if event_dec == 'I':
            return 0
        if event_dec == 'F':
            return 16
        return int(event_dec)
    
    def get_is_active(self, obj):
        return obj.event.is_active

    def get_event_uuid(self, obj):
        return obj.event.uuid

class OverallRankingTeamPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverallBrolympicsRanking
        fields = ['rank', 'total_points', 'event_wins', 'event_podiums']
class TeamPageSerailizer(serializers.ModelSerializer):
    overall_ranking = serializers.SerializerMethodField()
    player_1 = PlayerSerializer()
    player_2 = PlayerSerializer()
    class Meta:
        model = Team
        fields = ['name', 'player_1', 'player_2', 'overall_ranking', 'img']

    def get_overall_ranking(self, obj):
        bro_rankings = obj.brolympics.overall_ranking.filter(team=obj)
        if bro_rankings.exists():
            return OverallRankingTeamPageSerializer(bro_rankings.first()).data

        return None

class SmallTeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = ['name', 'uuid', 'img']

class EventRankingPageSerailzier_AbstractBase(serializers.ModelSerializer):
    event = serializers.SerializerMethodField()
    is_complete = serializers.SerializerMethodField()
    team = SmallTeamSerializer()
    class Meta:
        fields = ['rank', 'points', 'uuid', 'team',]

    def get_event(self, obj):
        return obj.event.name

    def get_is_active(self, obj):
        return obj.event.is_complete
    

class EventPageSerializer_h2h(EventRankingPageSerailzier_AbstractBase):

    class Meta:
        model = EventRanking_H2H
        fields = ['wins', 'losses', 'ties'] + EventRankingPageSerailzier_AbstractBase.Meta.fields


    
class EventPageSerializer_ind(EventRankingPageSerailzier_AbstractBase):
    score = serializers.SerializerMethodField()
    class Meta:
        model = EventRanking_Ind
        fields = ['score'] + EventRankingPageSerailzier_AbstractBase.Meta.fields

    def get_score(self, obj):        
        if obj.event.display_avg_scores:
            score = obj.team_avg_score
        else:
            score = obj.team_total_score

        if score is None:
            return None

        return round(score, obj.event.get_decimal_value())

class EventPageSerializer_team(EventRankingPageSerailzier_AbstractBase):
    score = serializers.SerializerMethodField()
    class Meta:
        model = EventRanking_Team
        fields = ['score'] + EventRankingPageSerailzier_AbstractBase.Meta.fields

    def get_score(self, obj):
        if obj.event.display_avg_scores:
            score = obj.team_avg_score
        else:
            score = obj.team_total_score

        if score is None:
            return None

        return round(score, obj.event.get_decimal_value())
        

class BracketMatchupSerializer(serializers.ModelSerializer):
    team_1 = serializers.SerializerMethodField()
    team_2 = serializers.SerializerMethodField()
    winner = serializers.SerializerMethodField()

    class Meta:
        model = BracketMatchup
        fields = ['team_1_seed', 'team_2_seed', 'team_1', 'team_2', 'team_1_score', 'team_2_score', 'uuid', 'winner']

    def get_team_1(self, obj):
        return SmallTeamSerializer(obj.team_1, context=self.context).data
    
    def get_team_2(self, obj):
        return SmallTeamSerializer(obj.team_2, context=self.context).data
    
    def get_winner(self, obj):
        return SmallTeamSerializer(obj.winner, context=self.context).data


class BracketSerializer(serializers.ModelSerializer):
    event = serializers.SerializerMethodField()
    match_1 = serializers.SerializerMethodField()
    match_2 = serializers.SerializerMethodField()
    championship = BracketMatchupSerializer()
    loser_bracket_finals = BracketMatchupSerializer()
    class Meta:
        model = Bracket_4
        fields = ['championship', 'loser_bracket_finals', 'is_complete', 'uuid', 'match_1', 'match_2', 'is_active','event']

    def get_event(self, obj):
        return obj.event.name

    def get_match_1(self, obj):
        match_serailizer = BracketMatchupSerializer(obj.championship.left, context=self.context)
        return match_serailizer.data

    def get_match_2(self, obj):
        match_serailizer = BracketMatchupSerializer(obj.championship.right, context=self.context)
        return match_serailizer.data
    
class OverallRankingSerializer(serializers.ModelSerializer):
    team = serializers.SerializerMethodField()
    class Meta:
        model = OverallBrolympicsRanking
        fields = ['team', 'rank', 'total_points', 'wins', 'losses', 'ties']

    def get_team(self, obj):
        return SmallTeamSerializer(obj.team, context=self.context).data



class EventCompSerailizer_h2h(serializers.ModelSerializer):
    comps = serializers.SerializerMethodField()
    class Meta:
        model = Event_H2H
        fields = ['name', 'comps']

    def get_comps(self, obj):
        comps = Competition_H2H.objects.filter(event=obj)
        comps_data = CompetitionSerializer_H2h(comps, many=True).data
        return comps_data
    
class EventCompSerailizer_ind(serializers.ModelSerializer):
    comps = serializers.SerializerMethodField()
    class Meta:
        model = Event_IND
        fields = ['name', 'comps']

    def get_comps(self, obj):
        comps = Competition_Ind.objects.filter(event=obj)
        comps_data = CompetitionSerializer_Ind(comps, many=True).data
        return comps_data
    
class EventCompSerailizer_Team(serializers.ModelSerializer):
    comps = serializers.SerializerMethodField()
    class Meta:
        model = Event_Team
        fields = ['name', 'comps']

    def get_comps(self, obj):
        comps = Competition_Team.objects.filter(event=obj)
        comps_data = CompetitionSerializer_Team(comps, many=True).data
        return comps_data

