from __future__ import annotations
from collections import defaultdict
from functools import partial
import random


class TieBreaker:
    def __init__(self, event):
        self.event = event
    
    def break_tie(self, team_rankings):
        grouped_teams = self._group_by_win_rate(team_rankings)
        tie_break_order = [
            self._break_head_to_head_wins,
            self._break_won_games_total,
            self._break_victory_margin,
            self._break_strength_of_schedule,
            self._break_strength_of_schedule_wins,
        ]

        return [team for group in grouped_teams for team in self._tie_break_group(group, tie_break_order)]

    def _group_by_win_rate(self, tied_teams, tie_breakers):       
        if len(tied_teams) == 1:
            return tied_teams

        for tie_breaker in tie_breakers:
            subgroups = self._apply_tie_breaker(tied_teams, tie_breaker)
            if len(subgroups) > 1:
                return [team for subgroup in subgroups for team in self._tie_break_group(subgroup, tie_breakers)]

        random.shuffle(tied_teams)
        return tied_teams
    
    def _apply_tie_breaker(self, teams, tie_breaker):
        values = tie_breaker(teams)
        return self._group_by_value(teams, values)
    
    @staticmethod
    def _group_by_value(teams, values):
        groups = defaultdict(list)
        for team, value in zip(teams, values):
            groups[value].append(team)
        return [groups[value] for value in sorted(groups, reverse=True)]
    
    @staticmethod
    def _group_by_win_rate(teams):
        return TieBreaker._group_by_value(teams, [team.win_rate for team in teams])
    
    def _break_head_to_head_wins(self, teams):
        head_to_head_comps = self._get_head_to_head_comps(teams)
        wins = defaultdict(int)
        games_played = defaultdict(int)

        for comp in head_to_head_comps:
            if comp.winner:
                wins[comp.winner] += 1
            games_played[comp.team_1] += 1
            games_played[comp.team_2] += 1

        if len(set(games_played.values())) > 1:
            return [0] * len(teams)  # Return zeros if not all teams played each other equally

        return [wins[team.team] for team in teams]
    
    def _get_head_to_head_comps(self, teams):
        team_ids = [team.team.id for team in teams]
        return Competition_H2H.objects.filter(
            event=self.event,
            is_complete=True,
            team_1__in=team_ids,
            team_2__in=team_ids
        )
        
    

