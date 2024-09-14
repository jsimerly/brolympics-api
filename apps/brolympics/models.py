from __future__ import annotations
from django.db import models
from django.contrib.auth import get_user_model
import random
from django.utils import timezone
from django.db.models import Q, Avg, Sum
from uuid import uuid4
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.db import transaction
from collections import defaultdict, Counter
from typing import Callable
from django.db.models import F, ExpressionWrapper, FloatField
from ckeditor.fields import RichTextField

from apps.custom_storage import FirebaseStorage

User = get_user_model()

# Create your models here.
def get_default_image(path, max=8):
    i = random.randint(1,max)
    return f'{path}/image_{str(i)}.webp'

class League(models.Model):
    name = models.CharField(max_length=120)
    league_owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False
    )
    founded = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    img = models.ImageField(storage=FirebaseStorage(), null=True)

    players = models.ManyToManyField(User, related_name='leagues', blank=True)

    def save(self, *args, **kwargs):
        if not self.img:
            self.img = get_default_image('default_league', 8)
        super().save(*args, **kwargs)


@receiver(pre_delete, sender=League)
def delete_players(sender, instance, **kwargs):
    instance.players.clear()


BROLYMPIC_IMAGES = [

]


class Brolympics(models.Model):
    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        null=False
    )
    name = models.CharField(max_length=60)

    is_registration_open = models.BooleanField(default=True)

    projected_start_date = models.DateTimeField(blank=True, null=True)
    projected_end_date = models.DateTimeField(blank=True, null=True)

    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)

    winner = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='winner'
    )

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    img = models.ImageField(storage=FirebaseStorage(), null=True)

    players = models.ManyToManyField(User, related_name='brolympics', blank=True,)

    def save(self, *args, **kwargs):
        if not self.img:
            self.img = get_default_image('default_league', 8)
        super().save(*args, **kwargs)

    def get_available_teams(self):
        return self.teams.filter(is_available=True)
    
    def get_all_events(self):
        h2h_events = self.event_h2h_set.all()
        ind_events = self.event_ind_set.all()
        team_events = self.event_team_set.all()

        return {'h2h':h2h_events, 'ind':ind_events, 'team':team_events}
    
    def get_active_events(self):
        h2h_events = self.event_h2h_set.filter(is_active=True)
        ind_events = self.event_ind_set.filter(is_active=True)
        team_events = self.event_team_set.filter(is_active=True)

        return {'h2h':h2h_events, 'ind':ind_events, 'team':team_events}
    
    def get_upcoming_events(self):
        h2h_events = self.event_h2h_set.filter(is_active=False, is_complete=False)
        ind_events = self.event_ind_set.filter(is_active=False, is_complete=False)
        team_events = self.event_team_set.filter(is_active=False, is_complete=False)

        return {'h2h':h2h_events, 'ind':ind_events, 'team':team_events}

    def _is_duplicate(self, team_1, team_2, pairs_set):
        return (team_1, team_2) in pairs_set or (team_2, team_1) in pairs_set
    
            
    def update_ranks(self):
        overall_rankings = self.overall_ranking.all()
        points_map = self._group_by_score(overall_rankings)
        ordered_teams = self._order_by_score(points_map)
        self._set_rankings(ordered_teams)

    def force_full_rankings_update(self):
        all_events = self.get_all_events()

        new_scores = defaultdict(int)
        for h2h_event in all_events['h2h']:
            for team_ranking in h2h_event.event_h2h_event_rankings.all():
                new_scores[team_ranking.team] += team_ranking.points

        for ind_event in all_events['ind']:
            for team_ranking in ind_event.event_ind_event_rankings.all():
                new_scores[team_ranking.team] += team_ranking.points

        for team_event in all_events['team']:
            for team_ranking in team_event.event_team_event_rankings.all():
                new_scores[team_ranking.team] += team_ranking.points

        overall_rankings = self.overall_ranking.all()
        for ranking in overall_rankings:
            ranking.total_points = new_scores[ranking.team]
            ranking.save()
    
        self.update_ranks()







    def _group_by_score(self, overall_rankings):
        score_to_team = {}

        for ranking in overall_rankings:
            score = ranking.total_points
            if score not in score_to_team:
                score_to_team[score] = []
            score_to_team[score].append(ranking)

        return score_to_team
    
    def _order_by_score(self, score_map):
        sorted_scores = sorted(score_map.keys(), reverse=True)
        return [score_map[score] for score in sorted_scores]
    
    def _set_rankings(self, ordered_teams):
        rank_counter = 1
        for ranking_group in ordered_teams:
            for team in ranking_group:
                team.rank=rank_counter
                team.save()

            rank_counter += len(ranking_group)
   

    def _create_ranking_objs(self):
        rankings = [
            OverallBrolympicsRanking(brolympics=self, team=team)
            for team in self.teams.all()
        ]
        OverallBrolympicsRanking.objects.bulk_create(rankings)

    def add_event_h2h(self, *args, **kwargs):
        Event_H2H.objects.create(
            brolympics=self,
            **kwargs
        )

    def add_event_ind(self, *args, **kwargs):
        Event_IND.objects.create(
            brolympics=self,
            **kwargs
        )

    def add_event_team(self, *args, **kwargs):
        Event_Team.objects.create(
            brolympics=self,
            **kwargs
        )


    def start(self):
        self.start_time = timezone.now()
        self.is_registration_open = False
        self.is_active = True
        self._create_ranking_objs()
        self.save()

    def end(self):
        self.end_time = timezone.now()
        self.is_active = False
        self.save()
        #finish ending

    def __str__(self):
        return self.name + ' - ' + self.league.name

class OverallBrolympicsRanking(models.Model):
    brolympics = models.ForeignKey(
        Brolympics,
        on_delete=models.CASCADE,
        related_name='overall_ranking'
    )
    rank = models.PositiveIntegerField(default=1)
    team = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
    )

    total_points = models.FloatField(default=0)

    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    ties = models.PositiveIntegerField(default=0)

    event_wins = models.PositiveIntegerField(default=0)
    event_podiums = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.team.name + ' - ' + self.brolympics.name

score_type = (
    ('B', 'Binary'),
    ('I', 'Integer'),
    ('1', 'Decimal_1'),
    ('2', 'Decimal_2'),
    ('3', 'Decimal_3'),
    ('4', 'Decimal_4'),
    ('F', 'Decimal_Float'),
)
class EventAbstactBase(models.Model):
    brolympics = models.ForeignKey(
        Brolympics,
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )

    name = models.CharField(max_length=60)

    score_type = models.CharField(max_length=1, choices=score_type, default='I')
    is_high_score_wins = models.BooleanField(default=True)
    max_score = models.FloatField(default=None, null=True, blank=True)
    min_score = models.FloatField(default=0, null=True, blank=True)

    projected_start_date = models.DateTimeField(blank=True, null=True)
    projected_end_date = models.DateTimeField(blank=True, null=True)

    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    location = models.CharField(max_length=260,null=True, blank=True)
    rules = RichTextField(null=True, blank=True)

    class Meta:
        abstract = True

    def start(self):
        self.start_time = timezone.now()
        self.is_active = True
        self.is_available = True
        self.create_child_objects()
        self.save()

    def _get_score_to_rank(self, team_n_override=None):
        score_map = defaultdict()
        n_teams = len(self.brolympics.teams.all())
        if team_n_override:
            n_teams = team_n_override

        for i in range(n_teams):
            rank = i+1
            score = n_teams - i
            if rank == 1:
                score += 4
            if rank == 2:
                score += 2
            if rank == 3:
                score += 1
            
            score_map[rank] = score         

        return score_map

    def finalize(self):
        self.end_time = timezone.now()
        self.is_active = False
        self.is_available = False
        self.is_complete = True
        self.finalize_rankings()
        self.save()

    def get_percent_complete(self):
        return self._get_percent_complete()
    

    def get_decimal_value(self):
        score_type_mapping = {
            'I': 0,
            'B': -1,
            '1': 1,
            '2': 2,
            '3': 3,
            '4': 4,
            'F': 16,
        }

        return score_type_mapping[self.score_type]


    def __str__(self):
        return self.name + ' - ' + self.brolympics.name


class Event_Team(EventAbstactBase):
    display_avg_scores = models.BooleanField(default=True)
    
    n_competitions = models.PositiveIntegerField(default=1)
    n_active_limit = models.PositiveIntegerField(blank=True, null=True)
    is_available = models.BooleanField(default=False)

    ## Initialization  ##
    def _get_percent_complete(self):
        all_comps = Competition_Team.objects.filter(event=self)
        total_count = all_comps.count()
        if total_count == 0:
            return 0
        completed_count = all_comps.filter(is_complete=True).count()
        return round((completed_count / total_count) * 100)

    def create_child_objects(self):
        self._create_competitions_and_ranking_objs_team()

    def _create_competitions_and_ranking_objs_team(self):
        competitions = []
        rankings = []
        for team in self.brolympics.teams.all():
            for _ in range(self.n_competitions):
                competitions.append(Competition_Team(event=self, team=team))
            rankings.append(EventRanking_Team(event=self, team=team))

        Competition_Team.objects.bulk_create(competitions)
        EventRanking_Team.objects.bulk_create(rankings)

    ## End of Initialization ##

    ## Utility ##

    def find_available_comps(self, user):
        comps = Competition_Team.objects.filter(
            Q(event=self),
            Q(is_complete=False),
            (
                Q(team__is_available=True, team__player_1=user) |
                Q(team__is_available=True, team__player_2=user)
            )
        )

        return comps
    
    def find_active_comps(self):
        comps = Competition_Team.objects.filter(
            event=self,
            is_active=True,
        )
        return comps
    
    def full_update_event_rankings_team(self):
        team_rankings = list(self.event_team_event_rankings.all())
        self._wipe_rankings(self, team_rankings)

    def _get_completed_event_comps_team(self):
        return Competition_Team.objects.filter(
            event=self,
            is_complete=True
        )

    def _wipe_rankings(self, rankings):
        rankings.update(
            team_total_score=0,
            team_avg_score=0,
        )
    
    ## End of Utility ##

    ## Life Cycle ## 

    def is_event_available(self):
        if self.is_complete:
            self.is_available = False
        else:
            self.is_available = self.n_active_limit is None or self._get_n_active_comps() < self.n_active_limit

        self.save()
        return self.is_available
    
    def _get_n_active_comps(self):
        active_comps = self.comp.filter(is_active=True)
        return active_comps.count()
    
    def get_team_next_comp_team(self, team):
        uncompleted_competitions = Competition_Team.objects.filter(
            event=self,
            team=team,
            is_complete=False,
            is_active=False
        )
        return uncompleted_competitions.first()
 
    def update_event_rankings_team(self):
        team_rankings = self.event_team_event_rankings.all()
        self._update_average_score(team_rankings)
        #get the new updated scores
        team_rankings = self.event_team_event_rankings.all()

        score_to_team_map = self._group_by_score(team_rankings)
        ordered_grouped_teams = self._order_by_score(score_to_team_map)
        self._set_rankings_and_points(ordered_grouped_teams)   

    def _update_average_score(self, team_rankings):
        competitions = self.comp.filter(is_complete=True)

        averages = competitions.values('team').annotate(
            team_avg_score=Avg('team_score')
        )

        averages_dict = {avg['team']: avg for avg in averages}

        for ranking in team_rankings:
            avg = averages_dict.get(ranking.team.id)
            if avg:
                ranking.team_avg_score = avg['team_avg_score']
                ranking.save()
    
    def _group_by_score(self, team_rankings):
        score_to_team = {}

        for ranking in team_rankings:
            score = ranking.team_avg_score
            if score not in score_to_team:
                score_to_team[score] = []
            score_to_team[score].append(ranking)

        return score_to_team
    
    def _order_by_score(self, score_map):
        reverse_order = self.is_high_score_wins
        sorted_scores = sorted(score_map.keys(), key=lambda x: x or 0, reverse=reverse_order)

        return [score_map[score] for score in sorted_scores]
    
    def _set_rankings_and_points(self, ordered_teams):
        score_map = self._get_score_to_rank()
        rank_counter = 1

        for ranking_group in ordered_teams:
            n_teams_in_group = len(ranking_group)

            total_points = 0
            for i in range(n_teams_in_group):
                current_rank = rank_counter + 1
                current_points = score_map[current_rank-1+i]
                total_points += current_points

            points_per_team = total_points / n_teams_in_group if n_teams_in_group != 0 else 0
            
            for team in ranking_group:
                team.points = points_per_team
                team.rank = rank_counter
                team.save()

            rank_counter += n_teams_in_group

    def check_for_completion(self):
        if self.start_time == None or self.is_complete:
            return None
        
        uncompleted = self.comp.filter(is_complete=False)
        if len(uncompleted) == 0:
            self.is_complete = True
            self.is_active = False
            self.is_available = False
            self.finalize_rankings()
            self.save()

            return True
        return False
    
    ## End of Life Cycle  ##

    ## Clean Up ##
    def finalize_rankings(self):
        with transaction.atomic():
            self.update_event_rankings_team()
            self._set_event_rankings_final()
            self.update_overall_rankings()

    def _set_event_rankings_final(self):
        self.event_team_event_rankings.all().update(is_final=True)

    def update_overall_rankings(self):
        overall_rankings = self.brolympics.overall_ranking.all()
        for ranking in overall_rankings:
            event_ranking = EventRanking_Team.objects.get(
                event=self,
                team=ranking.team
            )
            if event_ranking.rank <= 3:
                ranking.event_podiums += 1
            if event_ranking.rank == 1:
                ranking.event_wins += 1

            ranking.total_points += event_ranking.points
            ranking.save()

        self.brolympics.update_ranks()

    ## End of Clean Up

class Event_IND(EventAbstactBase):
    display_avg_scores = models.BooleanField(default=True)
    
    n_competitions = models.PositiveIntegerField(default=1)
    n_active_limit = models.PositiveIntegerField(blank=True, null=True)
    is_available = models.BooleanField(default=False)

    ## Initialization

    def create_child_objects(self):
        self._create_competition_and_ranking_objs_ind()

    def _create_competition_and_ranking_objs_ind(self):
        competitions = []
        rankings = []
        for team in self.brolympics.teams.all():
            for _ in range(self.n_competitions):
                competitions.append(Competition_Ind(event=self, team=team, display_avg_score=self.display_avg_scores))
            rankings.append(EventRanking_Ind(event=self, team=team))

        Competition_Ind.objects.bulk_create(competitions)
        EventRanking_Ind.objects.bulk_create(rankings)
   
    ## End of Initialization ##

    ## Event Utility ##
    def find_available_comps(self, user):
        comps = Competition_Ind.objects.filter(
            Q(event=self),
            Q(is_complete=False),
            (
                Q(team__is_available=True, team__player_1=user) |
                Q(team__is_available=True, team__player_2=user)
            )
        )

        return comps
    
    def find_active_comps(self):
        comps = Competition_Ind.objects.filter(
            event=self,
            is_active=True,
        )
        return comps
    
    def _get_percent_complete(self):
        all_comps = Competition_Ind.objects.filter(event=self)
        total_count = all_comps.count()
        if total_count == 0:
            return 0
        completed_count = all_comps.filter(is_complete=True).count()
        return round((completed_count / total_count) * 100)

    def full_update_event_rankings_ind(self):
        team_rankings = list(self.event_ind_event_rankings.all())
        self._wipe_rankings(self, team_rankings)
        # need to update rankings n stuff for all teams


    def _get_completed_event_comps_ind(self):
        return Competition_Ind.objects.filter(
            event=self,
            is_complete=True
        )
    
    def _wipe_rankings(self, rankings):
        rankings.update(
            player_1_total_score=0,
            player_1_avg_score=0,
            player_2_total_score=0,
            player_2_avg_score=0,
            team_total_score=0,
            team_avg_score=0,
        )

    ## End of Event Utility

    ## Event Life Cycle ##
    def is_event_available(self):
        if self.is_complete:
            self.is_available = False
        else:
            self.is_available = self.n_active_limit is None or self._get_n_active_comps() < self.n_active_limit

        self.save()
        return self.is_available

    def _get_n_active_comps(self):
        active_comps = self.comp.filter(is_active=True)
        return active_comps.count()
    
    def get_team_next_comp_ind(self, team):
        uncompleted_competitions = Competition_Ind.objects.filter(
            event=self,
            team=team,
            is_complete=False,
            is_active=False
        )
        return uncompleted_competitions.first()
    
    def update_event_rankings_ind(self):
        team_rankings = self.event_ind_event_rankings.all()
        self._update_average_score(team_rankings)
        #get the new updated scores
        team_rankings = self.event_ind_event_rankings.all()

        score_to_team_map = self._group_by_score(team_rankings)
        ordered_grouped_teams = self._order_by_score(score_to_team_map)
        self._set_rankings_and_points(ordered_grouped_teams)
        return ordered_grouped_teams
        
    def _update_average_score(self, team_rankings):
        competitions = self.comp.filter(is_complete=True)

        averages = competitions.values('team').annotate(
            player_1_avg_score=Avg('player_1_score'),
            player_2_avg_score=Avg('player_2_score'),
            team_avg_score=Avg('team_score')
        )

        averages_dict = {avg['team']: avg for avg in averages}

        for ranking in team_rankings:
            avg = averages_dict.get(ranking.team.id)
            if avg:
                ranking.player_1_avg_score = avg['player_1_avg_score']
                ranking.player_2_avg_score = avg['player_2_avg_score']
                ranking.team_avg_score = avg['team_avg_score']
                ranking.save()


    def _group_by_score(self, team_rankings):
        score_to_team = {}

        for ranking in team_rankings:
            score = ranking.team_avg_score
            if score not in score_to_team:
                score_to_team[score] = []
            score_to_team[score].append(ranking)

        return score_to_team

    def _order_by_score(self, score_map):
        reverse_order = self.is_high_score_wins
        sorted_scores = sorted(score_map.keys(), key=lambda x: x or 0, reverse=reverse_order)

        return [score_map[score] for score in sorted_scores]
    
    def _set_rankings_and_points(self, ordered_teams):
        score_map = self._get_score_to_rank()
        rank_counter = 1

        for ranking_group in ordered_teams:
            n_teams_in_group = len(ranking_group)

            total_points = 0
            for i in range(n_teams_in_group):
                current_rank = rank_counter + 1
                current_points = score_map[current_rank-1+i]
                total_points += current_points

            points_per_team = total_points / n_teams_in_group if n_teams_in_group != 0 else 0
            
            for team in ranking_group:
                team.points = points_per_team
                team.rank = rank_counter
                team.save()

            rank_counter += n_teams_in_group

    def check_for_completion(self):
        if self.start_time == None or self.is_complete:
            return None
        
        uncompleted = self.comp.filter(is_complete=False)
        if len(uncompleted) == 0:
            self.is_complete = True
            self.is_available = False
            self.is_active = False
            self.finalize_rankings()
            self.save()

            return True
        return False

    ## End of Life Cycle

    ## Event Clean Up ##
    def finalize_rankings(self):
        with transaction.atomic():
            self.update_event_rankings_ind()
            self._set_event_rankings_final()
            self.update_overall_rankings()

    def _set_event_rankings_final(self):
        self.event_ind_event_rankings.all().update(is_final=True)

    def update_overall_rankings(self):
        overall_rankings = self.brolympics.overall_ranking.all()
        for ranking in overall_rankings:
            event_ranking = EventRanking_Ind.objects.get(
                event=self,
                team=ranking.team
            )
            if event_ranking.rank <= 3:
                ranking.event_podiums += 1
            if event_ranking.rank == 1:
                ranking.event_wins += 1

            ranking.total_points += event_ranking.points
            ranking.save()

        self.brolympics.update_ranks()


    ## End of Life Cylce ##               
            
class Event_H2H(EventAbstactBase):
    #add validation that it's an even number and no more than n_teams-1
    n_matches = models.PositiveIntegerField(null=False, blank=False, default=4)
    n_active_limit = models.PositiveIntegerField(blank=True, null=True)
    n_bracket_teams = models.PositiveIntegerField(default=4)

    is_available = models.BooleanField(default=False)
    is_round_robin_complete = models.BooleanField(default=False)


    ## Initialization ## 
    def create_child_objects(self):   #used by parent for start()
        self.create_competition_objs_h2h()
        self.create_event_ranking_h2h()
        self.create_bracket()

    def create_competition_objs_h2h(self):
        pairs = self._create_team_pairs()
        competitions = [
            Competition_H2H(event=self, team_1=pair[0], team_2=pair[1])
            for pair in pairs
        ]
        Competition_H2H.objects.bulk_create(competitions)

    def create_competition_objs_h2h(self):
        teams = list(self.brolympics.teams.all())
        random.shuffle(teams)
        matchups = self.create_matchups(teams)
        
        competitions = []
        for team1, team2 in matchups:
            competitions.append(Competition_H2H(event=self, team_1=team1, team_2=team2))
        
        Competition_H2H.objects.bulk_create(competitions)


    def create_matchups(self, teams):
        n_team = len(teams)
        left_overs = []
        matchups_per_round = n_team//2
        n_matches = self.n_matches

        matchups = []
        for i in range(n_matches):
            top = [-1] * matchups_per_round
            bottom = [-1] * matchups_per_round
            on_top = True
            count = 0

            for team in teams:
                if on_top and count >= matchups_per_round:
                    count = 0
                    on_top = False
                elif not on_top and count >= matchups_per_round:
                    left_overs.append(team)
                    break

                if on_top:
                    top[count] = team
                else:
                    bottom[matchups_per_round-1-count] = team

                count += 1

            teams = [teams[-1]] + teams[:-1]
            round = [comp for comp in zip(top, bottom)]
            matchups.extend(round)

        for i in range(0, len(left_overs), 2):
            matchups.append((left_overs[i], left_overs[i+1]))

        return matchups

    def create_event_ranking_h2h(self):
        ranking_objs = [
            EventRanking_H2H(event=self, team=team)
            for team in self.brolympics.teams.all()
        ]
        EventRanking_H2H.objects.bulk_create(ranking_objs)

    def create_bracket(self):
        bracket_obj = Bracket_4.objects.create(event=self)
        bracket_obj.create_matchups()



    ## End of Initialization ##

    ## Utility ## 
    def _get_percent_complete(self):
        all_h2h_comps = Competition_H2H.objects.filter(event=self)
        all_bracket_comps = BracketMatchup.objects.filter(event=self)
        total_count = all_h2h_comps.count() + all_bracket_comps.count()
        
        if total_count == 0:
            return 0
        
        completed_count = all_h2h_comps.filter(is_complete=True).count() + all_bracket_comps.filter(is_complete=True).count()

        return round((completed_count / total_count) * 100)

    def full_update_event_rankings_h2h(self):
        team_rankings = list(self.event_h2h_event_rankings.all())

        self._wipe_win_loss_sos_h2h(team_rankings)
        
        #need a loop through and updated wins
        self._update_sos(team_rankings)
       

    def _get_completed_event_comps_h2h(self):
        return Competition_H2H.objects.filter(
            event=self,
            is_complete=True,
        )

    def _wipe_win_loss_sos_h2h(self, rankings):
        rankings.update(
            wins = 0,
            losses = 0,
            ties = 0,
            score_for = 0,
            score_against = 0,
            sos_wins = 0,
            sos_losses = 0,
            sos_ties = 0,
        )

    
    def flatten_1(self, lst):
        result = []
        for i in lst:
            if isinstance(i, list):
                result.extend(self.flatten_1(i))
            else:
                result.append(i)
        return result


    def flatten_2(self, lst):
        holder = []
        self._flatten_2(lst, holder)

        return holder


    def _flatten_2(self, element, result, parent_element=None):
        if not isinstance(element, list):
            if parent_element not in result:
                result.append(parent_element)
        else:
            for nested_element in element:
                self._flatten_2(nested_element, result, element)

    ## End of Utility ## 

    ## Event Life Cycle ##    
    def _find_available_standard_comps(self):
        return Competition_H2H.objects.filter(
            event=self,
            team_1__is_available=True,
            team_2__is_available=True,
            is_complete=False,
        )   
    
    def _find_available_bracket_comps(self):
        return BracketMatchup.objects.filter(
            bracket=self.bracket_4,
            team_1__isnull=False,
            team_2__isnull=False,
            is_complete=False
        )
    
    def find_available_comps(self, user):
        comps = Competition_H2H.objects.filter(
            Q(event=self) & Q(is_complete=False) & Q(team_1__isnull=False) & Q(team_2__isnull=False) &
            (
                Q(team_1__is_available=True, team_1__player_1=user) |
                Q(team_1__is_available=True, team_1__player_2=user) |
                Q(team_2__is_available=True, team_2__player_1=user) |
                Q(team_2__is_available=True, team_2__player_2=user)
            )
        )

        bracket = BracketMatchup.objects.filter(
            Q(event=self) & Q(is_complete=False) & Q(team_1__isnull=False) & Q(team_2__isnull=False) &
            (
                Q(team_1__is_available=True, team_1__player_1=user) |
                Q(team_1__is_available=True, team_1__player_2=user) |
                Q(team_2__is_available=True, team_2__player_1=user) |
                Q(team_2__is_available=True, team_2__player_2=user)
            )
        )

        return {'std': comps, 'bracket': bracket}

    
    def find_active_comps(self):
        comps = Competition_H2H.objects.filter(
            event=self,
            is_active=True,
        )
        bracket = BracketMatchup.objects.filter(
            event=self,
            is_active=True
        )

        return {'std': comps, 'bracket': bracket}      


    def update_event_rankings_h2h(self, team_rankings=None):
        if team_rankings == None:
            team_rankings = list(self.event_h2h_event_rankings.all())
        team_rankings = sorted(team_rankings, key=lambda x: x.win_rate, reverse=True)

        self._update_sos(team_rankings)
        tie_broken_teams = self.break_ties(team_rankings)
        self._set_rankings_and_points(tie_broken_teams)
        self._update_bracket()

        update_fields = ['rank', 'points']
        EventRanking_H2H.objects.bulk_update(team_rankings, update_fields)
        

    def _update_sos(self, team_rankings):
        team_to_wlt = {
            team_ranking.team: {
                'wins': team_ranking.wins,
                'losses': team_ranking.losses,
                'ties': team_ranking.ties,
            } 
            for team_ranking in team_rankings
        }

        for team_ranking in team_rankings:
            team = team_ranking.team
            team_completed_competitions = Competition_H2H.objects.filter(
                Q(team_1=team) | Q(team_2=team), 
                event=self, 
                is_complete=True
            )
            
            team_ranking.sos_wins = 0
            team_ranking.sos_losses = 0
            team_ranking.sos_ties = 0
            for comp in team_completed_competitions:
                if comp.team_1 == team:
                    opponent = comp.team_2
                else:
                    opponent = comp.team_1

                team_ranking.sos_wins += team_to_wlt[opponent]['wins']
                team_ranking.sos_losses += team_to_wlt[opponent]['losses']
                team_ranking.sos_ties += team_to_wlt[opponent]['ties']

            team_ranking.save()

    def break_ties(self, team_rankings: list[EventRanking_H2H]):
        return self.mergeSort(team_rankings)
    
    def mergeSort(self, teams):
        if len(teams) <= 1:
            return teams
        
        mid = len(teams)//2
        left = self.mergeSort(teams[:mid])
        right = self.mergeSort(teams[mid:])

        return self.merge(left, right)

    def merge(self, left, right):
        l, r = 0, 0

        new_team_order = []
        while l < len(left) and r < len(right):
            if self.isTeam1AboveTeam2(left[l], right[r]):
                new_team_order.append(left[l])
                l += 1
            else:
                new_team_order.append(right[r])
                r += 1
        if l < len(left):
            new_team_order.extend(left[l:])
        if r < len(right):
            new_team_order.extend(right[r:])
        return new_team_order

    def isTeam1AboveTeam2(self, team1: EventRanking_H2H, team2: EventRanking_H2H):
        # 0) Win rate
        if team1.win_rate != team2.win_rate:
            return team1.win_rate > team2.win_rate

        # 1) Head to head wins
        h2h_comps = self.competition_h2h_set.filter(
            is_complete=True,
            team_1__in=[team1.team, team2.team],
            team_2__in=[team1.team, team2.team]
        )
        team1_h2h_wins = sum(1 for comp in h2h_comps if comp.winner == team1.team)
        team2_h2h_wins = sum(1 for comp in h2h_comps if comp.winner == team2.team)
        if team1_h2h_wins != team2_h2h_wins:
            return team1_h2h_wins > team2_h2h_wins

        # 2) Won games total
        if team1.wins != team2.wins:
            return team1.wins > team2.wins

        # 3) Victory margin
        team1_margin = team1.score_for - team1.score_against
        team2_margin = team2.score_for - team2.score_against
        if team1_margin != team2_margin:
            return team1_margin > team2_margin

        # 4) Strength of schedule
        team1_sos = (team1.sos_wins + team1.sos_ties * 0.5) / (team1.sos_wins + team1.sos_losses + team1.sos_ties) if (team1.sos_wins + team1.sos_losses + team1.sos_ties) > 0 else 0
        team2_sos = (team2.sos_wins + team2.sos_ties * 0.5) / (team2.sos_wins + team2.sos_losses + team2.sos_ties) if (team2.sos_wins + team2.sos_losses + team2.sos_ties) > 0 else 0
        if team1_sos != team2_sos:
            return team1_sos > team2_sos

        # 5) Strength of schedule wins
        if team1.sos_wins != team2.sos_wins:
            return team1.sos_wins > team2.sos_wins

        # 6) Randomized
        return random.random() < 0.5

    
    def _set_rankings_and_points(self, team_rankings):
        score_map = self._get_score_to_rank()

        top_teams = team_rankings[:self.n_bracket_teams]
        bottom_teams = team_rankings[self.n_bracket_teams:]

        for i, ranking in enumerate(top_teams):
            ranking.rank = i + 1
            ranking.points = score_map[i+1]

        tied_rank = self.n_bracket_teams+1
        tied_points_total = 0
        tied_rankings = []

        
        for i, ranking in enumerate(bottom_teams):
            tied_rankings.append(ranking)
            tied_points_total += score_map[self.n_bracket_teams + i + 1]

            if i+1 < len(bottom_teams):
                if ranking.win_rate == bottom_teams[i+1].win_rate:
                    continue
            
            for ranking in tied_rankings:
                ranking.rank = tied_rank
                ranking.points = tied_points_total / len(tied_rankings)

            tied_rankings=[]
            tied_points_total=0
            tied_rank=self.n_bracket_teams + i + 2

        return team_rankings

    def check_for_round_robin_completion(self):
        if self.is_round_robin_complete:
            return None
                
        uncompleted = Competition_H2H.objects.filter(event=self, is_complete=False)
        if uncompleted.count() == 0:
            self.is_round_robin_complete = True
            self.bracket_4.is_active = True

            with transaction.atomic():
                self.update_event_rankings_h2h()
                self._update_bracket()

            self.save()
            return True
        return False
        

    def _update_bracket(self):
        top_4_rankings = self.event_h2h_event_rankings.all().order_by('rank')[:self.n_bracket_teams]
        self.bracket_4.update_teams(top_4_rankings)
        
    ## End of Life Cycle ##

    ## Event Clean Up ##
    def finalize_rankings(self): #used by parent for finalize()
        team_rankings = list(self.event_h2h_event_rankings.all().order_by('rank'))

        bracket_teams = [
            self.bracket_4.championship.winner,
            self.bracket_4.championship.loser,
            self.bracket_4.loser_bracket_finals.winner,
            self.bracket_4.loser_bracket_finals.loser,
        ]
        back_half_teams = team_rankings[self.n_bracket_teams:]


        bracket_team_rankings = [
            EventRanking_H2H.objects.get(event=self, team=team) 
            for team in bracket_teams
        ]
        final_rankings = bracket_team_rankings  + back_half_teams

        with transaction.atomic():
            self._set_event_rankings_final(final_rankings)
            self._update_overall_rankings()

        self.is_complete = True
        self.is_active = False
        self.is_available = False

        self.save()

    def _set_event_rankings_final(self, final_rankings):
        final_rankings = self._set_rankings_and_points(final_rankings)
        EventRanking_H2H.objects.bulk_update(final_rankings, ['rank', 'points'])
        self.event_h2h_event_rankings.all().update(is_final=True)

    def _update_overall_rankings(self):
        overall_rankings = self.brolympics.overall_ranking.all()
        for ranking in overall_rankings:
            event_ranking = EventRanking_H2H.objects.get(
                event=self,
                team=ranking.team
            )

            if event_ranking.rank <= 3:
                ranking.event_podiums += 1
            if event_ranking.rank == 1:
                ranking.event_wins += 1

            ranking.wins += event_ranking.wins
            ranking.losses += event_ranking.losses
            ranking.ties += event_ranking.ties
            ranking.total_points += event_ranking.points

            ranking.save()


        self.brolympics.update_ranks()

    ## End of Event Clean Up


TEAM_IMAGES = [
    'default_team/image1.jpg',
    'default_team/image2.jpg',
    # Add the rest of your default images paths here
]

class Team(models.Model):
    brolympics = models.ForeignKey(
        Brolympics,
        on_delete=models.CASCADE,
        related_name='teams'
    )

    name = models.CharField(max_length=120)

    player_1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='player_1_set',
        null=True,
        blank=True,
    )

    player_2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='player_2_set',
    )

    is_available = models.BooleanField(default=True)

    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    ties = models.PositiveIntegerField(default=0)

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    img = models.ImageField(storage=FirebaseStorage(), null=True)

    def save(self, *args, **kwargs):
        if not self.img:
            self.img = get_default_image('default_league', 8)
        super().save(*args, **kwargs)


    def add_player(self, player):
        if player == self.player_1 or player == self.player_2:
            raise ValueError("This player is already on this team.")
        
        if self.player_1 is None:
            self.player_1 = player
            self.save()
            return
        
        if self.player_2 is None:
            self.player_2 = player
            self.save()
            return
        
        raise ValueError("Both player slots are already filled.")
    
    def remove_player(self, player):
        if self.player_1 == player:
            self.player_1 = self.player_2
            self.player_2 = None
            self.save()
        
        elif self.player_2 == player:
            self.player_2 = None
            self.save()
        else:
            raise ValueError("Neither player is on this team.")

        if self._is_empty_team():
            self.delete()

    def start_comp(self):
        self.is_available = False
        if self.player_1:
            self.player_1.is_available = False
            self.player_1.save()
        if self.player_2:
            self.player_2.is_available = False
            self.player_2.save()
        self.save()

    def end_comp(self):
        self.is_available = True
        if self.player_1:
            self.player_1.is_available = True
            self.player_1.save()
        if self.player_2:
            self.player_2.is_available = True
            self.player_2.save()
        self.save()      

    
    def _is_empty_team(self):
        return self.player_1 is None and self.player_2 is None
    
    def __str__(self):
        return self.name + ' - ' + str(self.brolympics.name)
    
class Competition_Team(models.Model):
    event = models.ForeignKey(
        Event_Team,
        on_delete=models.CASCADE,
        related_name='comp',
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='team_competition_team',
    )

    display_avg_score = models.BooleanField(default=True)
    team_score = models.FloatField(blank=True, null=True)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    def start(self):
        if not self.team.is_available:
            raise ValueError("This team is not currently available")
        
        self.start_time = timezone.now()
        self.is_active = True
        self.team.start_comp()
        self.save()

    def cancel(self):
        if self.is_complete:
            raise ValueError('This event has already been completed.')
        
        self.team.end_comp()
        self.is_active = False
        self.save()

    def admin_end(self, team_score):
        team_score = float(team_score)

        self.team_score = team_score
        self.is_active = False
        self.is_complete = True

        self.team.end_comp()
        self.save()

        team_ranking = EventRanking_Team.objects.get(event=self.event, team=self.team)
        team_ranking.update_scores()

        self.event.update_event_rankings_team()
        self.event.check_for_completion()

    def end(self, team_score):
        self.end_time = timezone.now()

        self.team_score = team_score

        self.is_active = False
        self.is_complete = True

        self.team.end_comp()
        self.save()

        team_ranking = EventRanking_Team.objects.get(event=self.event, team=self.team)
        team_ranking.update_scores()

        self.event.update_event_rankings_team()
        self.event.check_for_completion()

    def __str__(self):
        return self.event.name + ' - ' + self.team.name
        

class Competition_Ind(models.Model):
    event = models.ForeignKey(
        Event_IND,
        on_delete=models.CASCADE,
        related_name='comp',
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='ind_competition_team',
    )

    player_1_score = models.FloatField(blank=True, null=True)
    player_2_score = models.FloatField(blank=True, null=True)

    display_avg_score = models.BooleanField(default=True)
    team_score = models.FloatField(blank=True, null=True)
    avg_score = models.FloatField(blank=True, null=True)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    def start(self):
        if not self.team.is_available:
            raise ValueError("This team is not currently available")
        
        self.start_time = timezone.now()
        self.is_active = True

        self.team.start_comp()
        self.save()

    def cancel(self):
        if self.is_complete:
            raise ValueError('This event has already been completed.')
        
        self.team.end_comp()
        self.is_active = False
        self.save()

    def admin_end(self, player_1_score, player_2_score):
        player_1_score = float(player_1_score)
        player_2_score = float(player_2_score)

        self.player_1_score = player_1_score
        self.player_2_score = player_2_score

        total = player_1_score + player_2_score
        self.team_score = total
        self.avg_score = total / 2    

        self.is_active = False
        self.is_complete = True

        self.team.end_comp()
        self.save()

        team_ranking = EventRanking_Ind.objects.get(event=self.event, team=self.team)
        team_ranking.update_scores()

        self.event.update_event_rankings_ind()
        self.event.check_for_completion()

    def end(self, player_1_score, player_2_score):
        self.end_time = timezone.now()
        player_1_score = float(player_1_score)
        player_2_score = float(player_2_score)

        self.player_1_score = player_1_score
        self.player_2_score = player_2_score
        total = player_1_score + player_2_score

        self.team_score = total
        self.avg_score = total / 2    

        self.is_active = False
        self.is_complete = True

        self.team.end_comp()
        self.save()

        team_ranking = EventRanking_Ind.objects.get(event=self.event, team=self.team)
        team_ranking.update_scores()

        self.event.update_event_rankings_ind()
        self.event.check_for_completion()

    def __str__(self):
        return self.event.name + ' - ' + self.team.name
    
        



class Competition_H2H_Base(models.Model):
    event = models.ForeignKey(
        Event_H2H,
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )

    team_1 = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_comp_team_1',
        null=True, # allowed to be null because this is also used in bracket
        blank=True
    )

    team_2 = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_comp_team_2',
        null=True,
        blank=True
    )

    team_1_score = models.FloatField(blank=True, null=True)
    team_2_score = models.FloatField(blank=True, null=True)

    winner = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_comp_wins',
        null=True,
        blank=True,
        default=None
    )
    loser = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='%(class)s_comp_losses',
        null=True,
        blank=True,
        default=None
    )

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    class Meta:
        abstract = True
    

    def start(self):
        if not self.team_1.is_available:
            raise ValueError(f"{self.team_1.name} is not currently available")
        
        if not self.team_2.is_available:
            raise ValueError(f"{self.team_2.name} is not currently available")

        self.team_1.start_comp()
        self.team_2.start_comp()

        self.start_time = timezone.now()
        self.is_active = True
        self.team_1.is_available, self.team_2.is_available = False, False

        self.save()

    def cancel(self):
        if self.is_complete:
            raise ValueError('This event has already been completed.')
        
        self.team_1.end_comp()
        self.team_2.end_comp()
        self.is_active=False
        self.save()


    def admin_end(self, team_1_score, team_2_score):
        team_1_score = float(team_1_score)
        team_2_score = float(team_2_score)
        self.team_1_score = team_1_score
        self.team_2_score = team_2_score

        winner, loser = self.determine_winner(team_1_score, team_2_score)

        self.winner = winner
        self.loser = loser
        self.is_complete=True
        self.is_active=False

        self.save()
        self.team_1.end_comp()
        self.team_2.end_comp()


    def end(self, team_1_score, team_2_score):
        team_1_score = float(team_1_score)
        team_2_score = float(team_2_score)
        self.team_1_score = team_1_score
        self.team_2_score = team_2_score

        winner, loser = self.determine_winner(team_1_score, team_2_score)

        self.winner = winner
        self.loser = loser

        team_1_ranking = EventRanking_H2H.objects.get(event=self.event, team=self.team_1)
        team_2_ranking = EventRanking_H2H.objects.get(event=self.event, team=self.team_2)

        if team_1_ranking.team == winner:
            team_1_ranking.wins += 1
            team_2_ranking.losses += 1
        elif team_2_ranking.team == winner:
            team_1_ranking.losses += 1
            team_2_ranking.wins += 1
        else:
            team_1_ranking.ties += 1
            team_2_ranking.ties += 1

        team_1_ranking.score_for += team_1_score
        team_1_ranking.score_against += team_2_score
        team_2_ranking.score_for += team_2_score
        team_2_ranking.score_against += team_1_score
        
        team_1_ranking.win_rate = team_1_ranking.get_win_rate()
        team_2_ranking.win_rate = team_2_ranking.get_win_rate()

        team_1_ranking.save()
        team_2_ranking.save()
        self.team_1.end_comp()
        self.team_2.end_comp()

        self.is_complete=True
        self.is_active=False
        self.save()

    def determine_winner(self, team_1_score, team_2_score):
        if team_1_score == team_2_score:
            winner, loser = None, None

        elif (team_1_score > team_2_score) == self.event.is_high_score_wins:
            winner, loser = self.team_1, self.team_2
        else:
            winner, loser = self.team_2, self.team_1

        
        return winner, loser
    
    def __str__(self):
        name = self.event.name
        if self.team_1:
            name += ' - ' + self.team_1.name
        if self.team_2:
            name += ' vs ' + self.team_2.name
        return name

class Competition_H2H(Competition_H2H_Base):
    def end(self, team_1_score, team_2_score):
        super().end(team_1_score, team_2_score)
        self.event.update_event_rankings_h2h()
        self.event.check_for_round_robin_completion()

    def admin_end(self, team_1_score, team_2_score):
        super().admin_end(team_1_score, team_2_score)
        team_1_ranking = EventRanking_H2H.objects.filter(team=self.team_1, event=self.event)
        if team_1_ranking.exists():
            team_1_ranking.first().recalculate_wl_sf()
        
        team_2_ranking = EventRanking_H2H.objects.filter(team=self.team_2, event=self.event)
        if team_2_ranking.exists():
            team_2_ranking.first().recalculate_wl_sf()

        self.event.update_event_rankings_h2h()
        self.event.check_for_round_robin_completion()

class EventRankingAbstractBase(models.Model):
    event = models.ForeignKey(
        Event_IND,
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )

    rank = models.PositiveIntegerField(default=1)
    points = models.FloatField(default=0)

    is_final = models.BooleanField(default=False)

    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)
    class Meta:
        abstract = True


class EventRanking_Team(models.Model):
    event = models.ForeignKey(
        Event_Team,
        on_delete=models.CASCADE,
        related_name='event_team_event_rankings'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='team_team_event_rankings'
    )
    
    team_total_score = models.FloatField(blank=True, null=True)
    team_avg_score = models.FloatField(blank=True, null=True)
    
    rank = models.PositiveIntegerField(default=1)
    points = models.FloatField(default=0)

    is_final = models.BooleanField(default=False)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    def update_scores(self):
        all_completed_comps = Competition_Team.objects.filter(
            event=self.event,
            team=self.team,
            is_complete=True,
        )

        team_total_score = 0
        counter = 0
        for comp in all_completed_comps:
            score = comp.team_score
            if score is not None:
                team_total_score += score
                counter += 1

        team_avg_score = team_total_score / counter if counter != 0 else None
        self.team_total_score = team_total_score
        self.team_avg_score = team_avg_score

        self.save()

    def __str__(self):
        return self.event.name + ' Ranking: ' + self.team.name
    


class EventRanking_Ind(models.Model):
    event = models.ForeignKey(
        Event_IND,
        on_delete=models.CASCADE,
        related_name='event_ind_event_rankings'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='team_ind_event_rankings'
    )

    player_1_total_score = models.FloatField(blank=True, null=True)
    player_1_avg_score = models.FloatField(blank=True, null=True)
    player_2_total_score = models.FloatField(blank=True, null=True)
    player_2_avg_score = models.FloatField(blank=True, null=True)
    
    team_total_score = models.FloatField(blank=True, null=True)
    team_avg_score = models.FloatField(blank=True, null=True)
    
    rank = models.PositiveIntegerField(default=1)
    points = models.FloatField(default=0)

    is_final = models.BooleanField(default=False)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    def update_scores(self):
        all_completed_comps = Competition_Ind.objects.filter(
            event=self.event,
            team=self.team,
            is_complete=True,
        )

        team_total_score = 0
        team_avg_total_score = 0
        counter = 0
        for comp in all_completed_comps:
            score = comp.team_score
            avg_score = comp.avg_score
            if score is not None:
                team_total_score += score
                team_avg_total_score += avg_score
                counter += 1

        team_avg_score = team_avg_total_score / counter if counter != 0 else None
        self.team_total_score = team_total_score
        self.team_avg_score = team_avg_score

        aggregates = all_completed_comps.aggregate(
            player_1_total_score=Sum('player_1_score'),
            player_1_avg_score=Avg('player_1_score'),
            player_2_total_score=Sum('player_2_score'),
            player_2_avg_score=Avg('player_2_score'),
        )

        for key, value in aggregates.items():
            setattr(self, key, value or None)

        self.save()

    def __str__(self):
        return self.event.name + ' Ranking: ' + self.team.name

         
class EventRanking_H2H(models.Model):
    event = models.ForeignKey(
        Event_H2H,
        on_delete=models.CASCADE,
        related_name='event_h2h_event_rankings'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='team_h2h_event_rankings'
    )

    rank = models.PositiveIntegerField(default=1)
    points = models.FloatField(default=0)

    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    ties = models.PositiveIntegerField(default=0)
    win_rate = models.FloatField(default=0)

    score_for = models.FloatField(default=0)
    score_against = models.FloatField(default=0)

    sos_wins = models.PositiveIntegerField(default=0)
    sos_losses = models.PositiveIntegerField(default=0)
    sos_ties = models.PositiveIntegerField(default=0)

    is_final = models.BooleanField(default=False)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    def get_win_rate(self):
        if (self.wins + self.ties + self.losses) > 0:
            win_rate = (self.wins + (0.5 * self.ties)) / (self.wins + self.ties + self.losses)
        else:
            win_rate = 0

        return win_rate
    
    def recalculate_wl_sf(self):
        self.wins = 0
        self.losses = 0
        self.ties = 0
        self.win_rate = 0
        self.score_for = 0
        self.score_against = 0

        comps = Competition_H2H.objects.filter(
            Q(team_1=self.team) | Q(team_2=self.team),
            event=self.event, 
            is_complete=True
        )

        for comp in comps:
            if self.team == comp.winner:
                self.wins += 1
            elif self.team == comp.loser:
                self.losses += 1
            else:
                self.ties += 1

            is_team_1 = self.team == comp.team_1

            if is_team_1:
                self.score_for += comp.team_1_score
                self.score_against += comp.team_2_score
            else:
                self.score_for += comp.team_2_score
                self.score_against += comp.team_1_score

        self.win_rate = self.get_win_rate()

        self.save()

            
    
    def __str__(self):
        return self.event.name + ' Ranking: ' + self.team.name


class BracketMatchup(Competition_H2H_Base):
    bracket = models.ForeignKey(
        'Bracket_4',
        on_delete=models.CASCADE
    )

    winner_node = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='won_matchups'
    )

    loser_node = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lost_matchups'
    )

    left = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='right_matchups'
    )
    right = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='left_matchups'
    )
    
    team_1_seed = models.PositiveIntegerField(null=True, blank=True)
    team_2_seed = models.PositiveIntegerField(null=True, blank=True)
    
    def update_teams(self, higher_seed, lower_seed):
        self.team_1 = higher_seed
        self.team_2 = lower_seed
        self.save()

    def start(self):
        if self.bracket.is_active:
            super().start()
        else:
            raise ValueError('Bracket is not active yet.')
        
    def end(self, team_1_score, team_2_score):
        team_1_score = float(team_1_score)
        team_2_score = float(team_2_score)
        if team_1_score == team_2_score:
            raise Exception

        super().end(team_1_score, team_2_score)

        if self.winner_node is None:
            if self._check_for_completion_during_end():
                self.bracket.finalize()
            return
        
        if self == self.bracket.championship or self == self.bracket.loser_bracket_finals:
            return


        if self == self.bracket.championship.left:
            self.winner_node.team_1 = self.winner
            self.loser_node.team_1 = self.loser

            if self.winner == self.team_1:
                self.winner_node.team_1_seed = self.team_1_seed
                self.loser_node.team_1_seed = self.team_2_seed
            else:
                self.winner_node.team_1_seed = self.team_2_seed
                self.loser_node.team_1_seed = self.team_1_seed
        else:
            self.winner_node.team_2 = self.winner
            self.loser_node.team_2 = self.loser

            if self.winner == self.team_1:
                self.winner_node.team_2_seed = self.team_1_seed
                self.loser_node.team_2_seed = self.team_2_seed
            else:
                self.winner_node.team_2_seed = self.team_2_seed
                self.loser_node.team_2_seed = self.team_1_seed




        self.winner_node.save()
        self.loser_node.save()
        self.save()

    def _check_for_completion_during_end(self):
        if self.bracket.championship == self and self.bracket.loser_bracket_finals.is_complete:
            return True
        elif self.bracket.loser_bracket_finals == self and self.bracket.championship.is_complete:
            return True
        return False

            

class Bracket_4(models.Model):
    event = models.OneToOneField(Event_H2H, on_delete=models.CASCADE)

    n_player = models.PositiveIntegerField(default=4)
    
    championship = models.ForeignKey(
        BracketMatchup,
        on_delete=models.CASCADE,
        related_name='root',
        null=True
    )

    loser_bracket_finals = models.ForeignKey(
        BracketMatchup,
        on_delete=models.CASCADE,
        related_name='loser_root',
        null=True
    )
    
    is_active = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    is_losers_bracket = models.BooleanField(default=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid4)

    def finalize(self):
        c_win_bool = self.championship.winner is not None
        c_lose_bool = self.championship.loser is not None
        l_win_bool = self.loser_bracket_finals.winner is not None
        l_lose_bool = self.loser_bracket_finals.loser is not None

        if c_win_bool and c_lose_bool and l_win_bool and l_lose_bool:
            self.is_active=False
            self.is_complete=True
            self.save()

            self.event.finalize()

    def create_matchups(self):
        championship = BracketMatchup.objects.create(
            bracket=self, event=self.event
        )
        loser_bracket_finals = BracketMatchup.objects.create(
            bracket=self, event=self.event
        )

        one_four = BracketMatchup.objects.create(
            bracket=self, 
            event=self.event,
            team_1_seed=1, 
            team_2_seed=4, 
            winner_node=championship,
            loser_node=loser_bracket_finals
        )
        
        two_three = BracketMatchup.objects.create(
            bracket=self,
            event=self.event,
            team_1_seed=3, 
            team_2_seed=2,
            winner_node=championship,
            loser_node=loser_bracket_finals
        )

        championship.left = one_four
        championship.right = two_three

        self.loser_bracket_finals = loser_bracket_finals
        self.championship = championship #root

        self.championship.save()
        self.loser_bracket_finals.save()
        self.save()

    def update_teams(self, playoff_teams):
        seed_1 = playoff_teams[0].team
        seed_2 = playoff_teams[1].team
        seed_3 = playoff_teams[2].team
        seed_4 = playoff_teams[3].team

        self.championship.left.team_1 = seed_1
        self.championship.left.team_2 = seed_4

        self.championship.right.team_1 = seed_3
        self.championship.right.team_2 = seed_2

        self.championship.left.save()
        self.championship.right.save()
        self.save()
        
    def __str__(self):
        return self.event.name + ' Bracket'

    






