from django.test import TestCase
from django.utils import timezone
from apps.brolympics.models import *
from django.contrib.auth import get_user_model
from unittest.mock import patch
from collections import defaultdict

User = get_user_model()

# Create your tests here.
class BrolympicsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.team1 = Team.objects.create(brolympics=self.brolympics, name='Team 1', is_available=True, player_1=self.user)
        self.team2 = Team.objects.create(brolympics=self.brolympics, name='Team 2', is_available=False, player_1=self.user)
        self.team3 = Team.objects.create(brolympics=self.brolympics, name='Team 3', is_available=True, player_1=self.user)
        self.team4 = Team.objects.create(brolympics=self.brolympics, name='Team 4', is_available=False, player_1=self.user)

    def test_start(self):
        self.brolympics.start()
        self.assertIsNotNone(self.brolympics.start_time)
        self.assertFalse(self.brolympics.is_registration_open)
        self.assertLessEqual(self.brolympics.start_time, timezone.now())
        self.assertEqual(self.brolympics.overall_ranking.count(), 4)

    def test_end(self):
        self.brolympics.end()
        self.assertLessEqual(self.brolympics.end_time, timezone.now())
        self.assertIsNone(self.brolympics.winner)


    def test_get_available_teams(self):
        self.assertEqual(list(self.brolympics.get_available_teams()), [self.team1, self.team3])

    def test_update_ranks(self):
        pass

    def test_group_by_score(self):
        self.brolympics.start()
        all_rankings = self.brolympics.overall_ranking.all()
        for i, ranking in enumerate(all_rankings):
            ranking.total_points = i+1
            ranking.save()

        all_rankings = self.brolympics.overall_ranking.all()
        result = self.brolympics._group_by_score(all_rankings)

        expected_result = {
            4: [all_rankings[3]],
            3: [all_rankings[2]],
            2: [all_rankings[1]],
            1: [all_rankings[0]],
        }

        self.assertEqual(result, expected_result)

        for i, ranking in enumerate(all_rankings):
            ranking.total_points = i%2 + 1
            ranking.save()

        all_rankings = self.brolympics.overall_ranking.all()
        result = self.brolympics._group_by_score(all_rankings)

        expected_result = {
            1: [all_rankings[0], all_rankings[2]],
            2: [all_rankings[1], all_rankings[3]],
        }
                                                 

    def test_order_by_score(self):
        self.brolympics.start()
        all_rankings = self.brolympics.overall_ranking.all()
        score_map = {
            4: [all_rankings[3]],
            3: [all_rankings[2]],
            2: [all_rankings[1]],
            1: [all_rankings[0]],
        }

        result = self.brolympics._order_by_score(score_map)
        expected_result = [[all_rankings[3]],[all_rankings[2]],[all_rankings[1]],[all_rankings[0]]]

        self.assertEqual(expected_result, result)

        score_map = {
            1: [all_rankings[0], all_rankings[2]],
            2: [all_rankings[1], all_rankings[3]],
        }

        result = self.brolympics._order_by_score(score_map)
        expected_result = [[all_rankings[1], all_rankings[3]], [all_rankings[0],all_rankings[2]]]
        self.assertEqual(expected_result, result)


    def test_set_rankings(self):
        self.brolympics.start()
        all_rankings = self.brolympics.overall_ranking.all()
        ordered_teams = [[all_rankings[3]],[all_rankings[2]],[all_rankings[1]],[all_rankings[0]]]

        self.brolympics._set_rankings(ordered_teams)

        rank_1 = all_rankings[3]
        rank_2 = all_rankings[2]
        rank_3 = all_rankings[1]
        rank_4 = all_rankings[0]

        self.assertEqual(rank_1.rank, 1)
        self.assertEqual(rank_2.rank, 2)
        self.assertEqual(rank_3.rank, 3)
        self.assertEqual(rank_4.rank, 4)

        ordered_teams = [[all_rankings[1], all_rankings[3]], [all_rankings[0],all_rankings[2]]]

        self.brolympics._set_rankings(ordered_teams)

        rank_1a = all_rankings[3]
        rank_1b = all_rankings[1]
        rank_3a = all_rankings[2]
        rank_3b = all_rankings[0]

        self.assertEqual(rank_1a.rank, 1)
        self.assertEqual(rank_1b.rank, 1)
        self.assertEqual(rank_3a.rank, 3)
        self.assertEqual(rank_3b.rank, 3)

    def test_is_duplicate(self):
        pairs_set = {(self.team1, self.team2)}
        self.assertTrue(self.brolympics._is_duplicate(self.team1, self.team2, pairs_set))
        self.assertTrue(self.brolympics._is_duplicate(self.team2, self.team1, pairs_set))
        self.assertFalse(self.brolympics._is_duplicate(self.team1, self.team3, pairs_set))

    def test_create_ranking_objs(self):
        self.brolympics._create_ranking_objs()
        self.assertEqual(OverallBrolympicsRanking.objects.count(), 4)
        self.assertTrue(OverallBrolympicsRanking.objects.filter(brolympics=self.brolympics, team=self.team1).exists())
        self.assertTrue(OverallBrolympicsRanking.objects.filter(brolympics=self.brolympics, team=self.team2).exists())
        self.assertTrue(OverallBrolympicsRanking.objects.filter(brolympics=self.brolympics, team=self.team3).exists())
        self.assertTrue(OverallBrolympicsRanking.objects.filter(brolympics=self.brolympics, team=self.team4).exists())


class Event_TeamInitializationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            uid='1',
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', is_available=(i%2==0), player_1=self.user) for i in range(8)]

        self.team_event = Event_Team.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_competitions=1,
        )

    def test_create_competition_and_ranking_objs_team_1(self):
        self.team_event._create_competitions_and_ranking_objs_team()

        self.assertEqual(Competition_Team.objects.count(), self.team_event.n_competitions * self.brolympics.teams.count())
        self.assertEqual(EventRanking_Team.objects.count(), self.brolympics.teams.count())

        for comp in Competition_Team.objects.filter(event=self.team_event):
            self.assertEqual(comp.event, self.team_event)
            self.assertIn(comp.team, self.brolympics.teams.all())
        
        for ranking in EventRanking_Team.objects.filter(event=self.team_event):
            self.assertEqual(ranking.event, self.team_event)
            self.assertIn(ranking.team, self.brolympics.teams.all())

    def test_create_competition_and_ranking_objs_team_4(self):
        self.team_event.n_competitions = 4
        self.team_event.save()

        self.team_event._create_competitions_and_ranking_objs_team()

        self.assertEqual(Competition_Team.objects.count(), self.team_event.n_competitions * self.brolympics.teams.count())
        self.assertEqual(EventRanking_Team.objects.count(), self.brolympics.teams.count())

        for comp in Competition_Team.objects.filter(event=self.team_event):
            self.assertEqual(comp.event, self.team_event)
            self.assertIn(comp.team, self.brolympics.teams.all())
        
        for ranking in EventRanking_Team.objects.filter(event=self.team_event):
            self.assertEqual(ranking.event, self.team_event)
            self.assertIn(ranking.team, self.brolympics.teams.all())

class Event_TeamUtilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            uid='1',
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', is_available=(i%2==0), player_1=self.user) for i in range(8)]

        self.team_event = Event_Team.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_competitions=1,
        )

    def test_get_completed_event_comps_ind(self):
        all_comps = [Competition_Team.objects.create(
            team=self.teams[i],
            event=self.team_event,
            is_complete=i%2
        )
            for i in range(4)
        ]

        completed_comps = self.team_event._get_completed_event_comps_team()
        self.assertEqual(completed_comps.count(), 2)
        self.assertEqual(len(all_comps), 4)

    def test_wipe_rankings(self):
        for i in range(1,4):
            EventRanking_Team.objects.create(
                event=self.team_event,
                team=self.teams[i],
                team_total_score=10*i,
                team_avg_score=10*i,
            )
    
        all_rankings = self.team_event.event_team_event_rankings.all()
        for ranking in all_rankings:
            self.assertNotEqual(ranking.team_total_score, 0)
            self.assertNotEqual(ranking.team_avg_score, 0)

        self.team_event._wipe_rankings(all_rankings)
            
        all_rankings = self.team_event.event_team_event_rankings.all()

        for ranking in all_rankings:
            self.assertEqual(ranking.team_total_score, 0)
            self.assertEqual(ranking.team_avg_score, 0)

    def test_get_score_to_rank(self):
        score_to_rank = self.team_event._get_score_to_rank()
        expected_score_to_rank = {
            1: 10, 
            2: 8, 
            3: 7,  
            4: 5,  
            5: 4,  
            6: 3,  
            7: 2,  
            8: 1,
        }
        self.assertEqual(score_to_rank, expected_score_to_rank)

class Event_TeamLifeCycleTests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid='1',
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.team_event = Event_Team.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_competitions=2,
        )
        self.team_event.start()

    def test_is_event_available_no_limit(self):
        self.assertEqual(self.team_event.is_available, True)
        self.team_event.is_complete = True
        self.team_event.save()
        self.assertEqual(self.team_event.is_event_available(), False)
        self.assertEqual(self.team_event.is_available, False)
        
        self.team_event.is_complete = False
        self.team_event.save()
        self.assertEqual(self.team_event.is_event_available(), True)
        self.assertEqual(self.team_event.is_available, True)

    def test_is_event_available_limit(self):
        self.team_event.n_active_limit = 4
        self.team_event.save()

        with patch.object(Event_Team, '_get_n_active_comps', return_value=6):
            self.assertEqual(self.team_event.is_event_available(), False)
            self.assertEqual(self.team_event.is_available, False)

        with patch.object(Event_Team, '_get_n_active_comps', return_value=4):
            self.assertEqual(self.team_event.is_event_available(), False)
            self.assertEqual(self.team_event.is_available, False)

        with patch.object(Event_Team, '_get_n_active_comps', return_value=3):
            self.assertEqual(self.team_event.is_event_available(), True)
            self.assertEqual(self.team_event.is_available, True)

    def test_get_n_active_comps(self):
        self.team_event.n_active_limit = 3
        self.team_event.save()

        all_comps = self.team_event.comp.all()
        for i in range(3):
            comp = all_comps[i]
            comp.is_active = True
            comp.save()

        self.assertEqual(self.team_event._get_n_active_comps(), 3)

        all_comps.update(is_active=False)

        self.assertEqual(self.team_event._get_n_active_comps(), 0)

    def test_update_event_rankings_team(self):
        pass

    def test_update_average_score(self):
        all_team1_comps = Competition_Team.objects.filter(
            event=self.team_event,
            team=self.teams[0],
        )

        for i, comp in enumerate(all_team1_comps):
            comp.team_score = i+15
            comp.is_complete = True
            comp.save()

        team_rankings = EventRanking_Team.objects.filter(team=self.teams[0], event=self.team_event)
        
        self.team_event._update_average_score(team_rankings)

        team_ranking = team_rankings.first()
        self.assertEqual(team_ranking.team_avg_score, 15.5)


    def test_group_by_score(self):
        team_rankings = self.team_event.event_team_event_rankings.all()
        for i, team in enumerate(team_rankings):
            team.team_avg_score = i
            team.save()

        expected_result = {
            0: [team_rankings[0]],
            1: [team_rankings[1]],
            2: [team_rankings[2]],
            3: [team_rankings[3]],
            4: [team_rankings[4]],
            5: [team_rankings[5]],
            6: [team_rankings[6]],
            7: [team_rankings[7]],
        }

        team_rankings = self.team_event.event_team_event_rankings.all()
        score_to_team_map = self.team_event._group_by_score(team_rankings)

        self.assertEqual(expected_result, score_to_team_map)

        for i, team in enumerate(team_rankings):
            team.team_avg_score = i%2
            team.save()

        expected_result = {
            0: [team_rankings[0],team_rankings[2],team_rankings[4],team_rankings[6],],
            1: [team_rankings[1],team_rankings[3],team_rankings[5],team_rankings[7],],
        }

        team_rankings = self.team_event.event_team_event_rankings.all()
        score_to_team_map = self.team_event._group_by_score(team_rankings)

        self.assertEqual(expected_result, score_to_team_map)

    def test_order_by_score(self):
        team_rankings = self.team_event.event_team_event_rankings.all()
        score_map = {
            0: [team_rankings[0]],
            1: [team_rankings[1]],
            2: [team_rankings[2]],
            3: [team_rankings[3]],
            4: [team_rankings[4]],
            5: [team_rankings[5]],
            6: [team_rankings[6]],
            7: [team_rankings[7]],
        }

        team_rankings = self.team_event.event_team_event_rankings.all()
        ordeded_scores = self.team_event._order_by_score(score_map)

        expected_result = [[team_rankings[7]],[team_rankings[6]],[team_rankings[5]],[team_rankings[4]],[team_rankings[3]],[team_rankings[2]],[team_rankings[1]],[team_rankings[0]],]

        self.assertEqual(expected_result, ordeded_scores)

        self.team_event.is_high_score_wins = False
        self.team_event.save()

        reverse_ordeded_scores = self.team_event._order_by_score(score_map)
        expected_result.reverse()
        self.assertEqual(expected_result, reverse_ordeded_scores)

        score_map = {
            0: [team_rankings[0],team_rankings[2],team_rankings[4],team_rankings[6],],
            1: [team_rankings[1],team_rankings[3],team_rankings[5],team_rankings[7],],
        }

        expected_result = [[team_rankings[0],team_rankings[2],team_rankings[4],team_rankings[6],], [team_rankings[1],team_rankings[3],team_rankings[5],team_rankings[7],]]

        grouped_ordered_scores = self.team_event._order_by_score(score_map)
        self.assertEqual(expected_result, grouped_ordered_scores)

    def test_set_rankings_and_points(self):
        team_rankings = self.team_event.event_team_event_rankings.all()
        ordered_teams = [[team_rankings[0],team_rankings[2],team_rankings[4],team_rankings[6],], [team_rankings[1],team_rankings[3],team_rankings[5],team_rankings[7],]]

        self.team_event._set_rankings_and_points(ordered_teams)
        team_rankings = self.team_event.event_team_event_rankings.all()

        for i, team in enumerate(team_rankings):
            expected_points = 7.5 if i%2 == 0 else 2.5
            expected_rank = 1 if i%2 == 0 else 5
            self.assertEqual(team.points, expected_points)
            self.assertEqual(team.rank, expected_rank)

        single_ordered_teams = [[team_rankings[0]],[team_rankings[1]],[team_rankings[2]],[team_rankings[3]],[team_rankings[4]],[team_rankings[5]],[team_rankings[6]],[team_rankings[7]],]

        expected_points_map = {
            1: 10, 
            2: 8, 
            3: 7,  
            4: 5,  
            5: 4,  
            6: 3,  
            7: 2,  
            8: 1,
        }

        self.team_event._set_rankings_and_points(single_ordered_teams)

        for i, team in enumerate(team_rankings):
            expected_points = expected_points_map[i+1]
            expected_rank = i+1
            self.assertEqual(team.points, expected_points)
            self.assertEqual(team.rank, expected_rank)

    def test_check_for_completion(self):
        self.assertFalse(self.team_event.check_for_completion())

        self.team_event.comp.all().update(is_complete=True)
        self.assertTrue(self.team_event.check_for_completion())

        self.team_event.start_time = None
        self.team_event.save()
        self.assertIsNone(self.team_event.check_for_completion())


class Event_INDInitializationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            uid='1',
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', is_available=(i%2==0), player_1=self.user) for i in range(8)]

        self.ind_event = Event_IND.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_competitions=1,
        )
    
    def test_create_competition_and_ranking_objs_ind_1(self):
        self.ind_event._create_competition_and_ranking_objs_ind()

        self.assertEqual(Competition_Ind.objects.count(), self.ind_event.n_competitions * self.brolympics.teams.count())
        self.assertEqual(EventRanking_Ind.objects.count(), self.brolympics.teams.count())

        for comp in Competition_Ind.objects.filter(event=self.ind_event):
            self.assertEqual(comp.event, self.ind_event)
            self.assertIn(comp.team, self.brolympics.teams.all())
        
        for ranking in EventRanking_Ind.objects.filter(event=self.ind_event):
            self.assertEqual(ranking.event, self.ind_event)
            self.assertIn(ranking.team, self.brolympics.teams.all())

    def test_create_competition_and_ranking_objs_ind_4(self):
        self.ind_event.n_competitions = 4
        self.ind_event.save()

        self.ind_event._create_competition_and_ranking_objs_ind()

        self.assertEqual(Competition_Ind.objects.count(), self.ind_event.n_competitions * self.brolympics.teams.count())
        self.assertEqual(EventRanking_Ind.objects.count(), self.brolympics.teams.count())

        for comp in Competition_Ind.objects.filter(event=self.ind_event):
            self.assertEqual(comp.event, self.ind_event)
            self.assertIn(comp.team, self.brolympics.teams.all())
        
        for ranking in EventRanking_Ind.objects.filter(event=self.ind_event):
            self.assertEqual(ranking.event, self.ind_event)
            self.assertIn(ranking.team, self.brolympics.teams.all())

class Event_INDUtilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', is_available=(i%2==0), player_1=self.user) for i in range(8)]

        self.ind_event = Event_IND.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_competitions=1,
        )

    def test_get_completed_event_comps_ind(self):
        all_comps = [Competition_Ind.objects.create(
            team=self.teams[i],
            event=self.ind_event,
            is_complete=i%2
        )
            for i in range(4)
        ]

        completed_comps = self.ind_event._get_completed_event_comps_ind()
        self.assertEqual(completed_comps.count(), 2)
        self.assertEqual(len(all_comps), 4)

    def test_wipe_rankings(self):
        for i in range(1,4):
            EventRanking_Ind.objects.create(
                event=self.ind_event,
                team=self.teams[i],
                player_1_total_score=10*i,
                player_1_avg_score=10*i,
                player_2_total_score=10*i,
                player_2_avg_score=10*i,
                team_total_score=10*i,
                team_avg_score=10*i,
            )
    
        all_rankings = self.ind_event.event_ind_event_rankings.all()
        for ranking in all_rankings:
            self.assertNotEqual(ranking.player_1_total_score, 0)
            self.assertNotEqual(ranking.player_2_total_score, 0)
            self.assertNotEqual(ranking.player_1_avg_score, 0)
            self.assertNotEqual(ranking.player_2_avg_score, 0)
            self.assertNotEqual(ranking.team_total_score, 0)
            self.assertNotEqual(ranking.team_avg_score, 0)

        self.ind_event._wipe_rankings(all_rankings)
            
        all_rankings = self.ind_event.event_ind_event_rankings.all()

        for ranking in all_rankings:
            self.assertEqual(ranking.player_1_total_score, 0)
            self.assertEqual(ranking.player_2_total_score, 0)
            self.assertEqual(ranking.player_1_avg_score, 0)
            self.assertEqual(ranking.player_2_avg_score, 0)
            self.assertEqual(ranking.team_total_score, 0)
            self.assertEqual(ranking.team_avg_score, 0)

    def test_get_score_to_rank(self):
        score_to_rank = self.ind_event._get_score_to_rank()
        expected_score_to_rank = {
            1: 10, 
            2: 8, 
            3: 7,  
            4: 5,  
            5: 4,  
            6: 3,  
            7: 2,  
            8: 1,
        }
        self.assertEqual(score_to_rank, expected_score_to_rank)


class Event_INDLifeCycleTests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.ind_event = Event_IND.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_competitions=2,
        )
        self.ind_event.start()

    def test_is_event_available_no_limit(self):
        self.assertEqual(self.ind_event.is_available, True)
        self.ind_event.is_complete = True
        self.ind_event.save()
        self.assertEqual(self.ind_event.is_event_available(), False)
        self.assertEqual(self.ind_event.is_available, False)
        
        self.ind_event.is_complete = False
        self.ind_event.save()
        self.assertEqual(self.ind_event.is_event_available(), True)
        self.assertEqual(self.ind_event.is_available, True)

    def test_is_event_available_limit(self):
        self.ind_event.n_active_limit = 4
        self.ind_event.save()

        with patch.object(Event_IND, '_get_n_active_comps', return_value=6):
            self.assertEqual(self.ind_event.is_event_available(), False)
            self.assertEqual(self.ind_event.is_available, False)

        with patch.object(Event_IND, '_get_n_active_comps', return_value=4):
            self.assertEqual(self.ind_event.is_event_available(), False)
            self.assertEqual(self.ind_event.is_available, False)

        with patch.object(Event_IND, '_get_n_active_comps', return_value=3):
            self.assertEqual(self.ind_event.is_event_available(), True)
            self.assertEqual(self.ind_event.is_available, True)

        
    def test_get_n_active_comps(self):
        self.ind_event.n_active_limit = 3
        self.ind_event.save()

        all_comps = self.ind_event.comp.all()
        for i in range(3):
            comp = all_comps[i]
            comp.is_active = True
            comp.save()

        self.assertEqual(self.ind_event._get_n_active_comps(), 3)

        all_comps.update(is_active=False)

        self.assertEqual(self.ind_event._get_n_active_comps(), 0)


    def test_update_event_rankings_ind(self):
        pass
   

    def test_update_average_score(self):
        all_team1_comps = Competition_Ind.objects.filter(
            event=self.ind_event,
            team=self.teams[0],
        )

        for i, comp in enumerate(all_team1_comps):
            comp.player_1_score = i+7
            comp.player_2_score = i+8
            comp.team_score = comp.player_1_score + comp.player_2_score
            comp.is_complete = True
            comp.save()

        team_rankings = EventRanking_Ind.objects.filter(team=self.teams[0], event=self.ind_event)
        
        self.ind_event._update_average_score(team_rankings)

        team_ranking = team_rankings.first()
        self.assertEqual(team_ranking.player_1_avg_score, 7.5)
        self.assertEqual(team_ranking.player_2_avg_score, 8.5)
        self.assertEqual(team_ranking.team_avg_score, 16)

    def test_group_by_score(self):
        team_rankings = self.ind_event.event_ind_event_rankings.all()
        for i, team in enumerate(team_rankings):
            team.team_avg_score = i
            team.save()

        expected_result = {
            0: [team_rankings[0]],
            1: [team_rankings[1]],
            2: [team_rankings[2]],
            3: [team_rankings[3]],
            4: [team_rankings[4]],
            5: [team_rankings[5]],
            6: [team_rankings[6]],
            7: [team_rankings[7]],
        }

        team_rankings = self.ind_event.event_ind_event_rankings.all()
        score_to_team_map = self.ind_event._group_by_score(team_rankings)

        self.assertEqual(expected_result, score_to_team_map)

        for i, team in enumerate(team_rankings):
            team.team_avg_score = i%2
            team.save()

        expected_result = {
            0: [team_rankings[0],team_rankings[2],team_rankings[4],team_rankings[6],],
            1: [team_rankings[1],team_rankings[3],team_rankings[5],team_rankings[7],],
        }

        team_rankings = self.ind_event.event_ind_event_rankings.all()
        score_to_team_map = self.ind_event._group_by_score(team_rankings)

        self.assertEqual(expected_result, score_to_team_map)

    def test_order_by_score(self):
        team_rankings = self.ind_event.event_ind_event_rankings.all()
        score_map = {
            0: [team_rankings[0]],
            1: [team_rankings[1]],
            2: [team_rankings[2]],
            3: [team_rankings[3]],
            4: [team_rankings[4]],
            5: [team_rankings[5]],
            6: [team_rankings[6]],
            7: [team_rankings[7]],
        }

        team_rankings = self.ind_event.event_ind_event_rankings.all()
        ordeded_scores = self.ind_event._order_by_score(score_map)

        expected_result = [[team_rankings[7]],[team_rankings[6]],[team_rankings[5]],[team_rankings[4]],[team_rankings[3]],[team_rankings[2]],[team_rankings[1]],[team_rankings[0]],]

        self.assertEqual(expected_result, ordeded_scores)

        self.ind_event.is_high_score_wins = False
        self.ind_event.save()

        reverse_ordeded_scores = self.ind_event._order_by_score(score_map)
        expected_result.reverse()
        self.assertEqual(expected_result, reverse_ordeded_scores)

        score_map = {
            0: [team_rankings[0],team_rankings[2],team_rankings[4],team_rankings[6],],
            1: [team_rankings[1],team_rankings[3],team_rankings[5],team_rankings[7],],
        }

        expected_result = [[team_rankings[0],team_rankings[2],team_rankings[4],team_rankings[6],], [team_rankings[1],team_rankings[3],team_rankings[5],team_rankings[7],]]

        grouped_ordered_scores = self.ind_event._order_by_score(score_map)
        self.assertEqual(expected_result, grouped_ordered_scores)

    def test_set_rankings_and_points(self):

        team_rankings = self.ind_event.event_ind_event_rankings.all()
        ordered_teams = [[team_rankings[0],team_rankings[2],team_rankings[4],team_rankings[6],], [team_rankings[1],team_rankings[3],team_rankings[5],team_rankings[7],]]

        self.ind_event._set_rankings_and_points(ordered_teams)
        team_rankings = self.ind_event.event_ind_event_rankings.all()

        for i, team in enumerate(team_rankings):
            expected_points = 7.5 if i%2 == 0 else 2.5
            expected_rank = 1 if i%2 == 0 else 5

            self.assertEqual(team.points, expected_points)
            self.assertEqual(team.rank, expected_rank)

        single_ordered_teams = [[team_rankings[0]],[team_rankings[1]],[team_rankings[2]],[team_rankings[3]],[team_rankings[4]],[team_rankings[5]],[team_rankings[6]],[team_rankings[7]],]

        expected_points_map = {
            1: 10, 
            2: 8, 
            3: 7,  
            4: 5,  
            5: 4,  
            6: 3,  
            7: 2,  
            8: 1,
        }

        self.ind_event._set_rankings_and_points(single_ordered_teams)

        for i, team in enumerate(team_rankings):
            expected_points = expected_points_map[i+1]
            expected_rank = i+1
            self.assertEqual(team.points, expected_points)
            self.assertEqual(team.rank, expected_rank)

    def test_check_for_completion(self):
        self.assertFalse(self.ind_event.check_for_completion())

        self.ind_event.comp.all().update(is_complete=True)
        self.assertTrue(self.ind_event.check_for_completion())

        self.ind_event.start_time = None
        self.ind_event.save()
        self.assertIsNone(self.ind_event.check_for_completion())

class Event_INDCleanUpTests(TestCase):
    pass


class Event_H2HInitializationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', is_available=(i%2==0), player_1=self.user) for i in range(9)]
        self.h2h_event = Event_H2H.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_matches=4,
        )

    def test_create_competition_objs_h2h(self):
        self.h2h_event.create_competition_objs_h2h()
        
        # Get all competitions for this event
        competitions = Competition_H2H.objects.filter(event=self.h2h_event)
        
        # Count the number of competitions each team is involved in
        team_competition_count = {}
        for comp in competitions:
            team_competition_count[comp.team_1] = team_competition_count.get(comp.team_1, 0) + 1
            team_competition_count[comp.team_2] = team_competition_count.get(comp.team_2, 0) + 1
        
        # Check that each team participates in exactly n_matches competitions
        for team in self.brolympics.teams.all():
            self.assertEqual(
                team_competition_count.get(team, 0),
                self.h2h_event.n_matches,
                f"Team {team} should participate in exactly {self.h2h_event.n_matches} competitions"
        )
    
        # Additional check for the total number of competitions (optional, but good to keep)
        n_teams = len(self.brolympics.teams.all())
        expected_comps = (self.h2h_event.n_matches * n_teams) // 2 
        self.assertEqual(
            expected_comps,
            competitions.count(),
            f"Total number of competitions should be {expected_comps}"
        )

    def test_create_matchups(self):
        teams = list(self.brolympics.teams.all())
        matchups = self.h2h_event.create_matchups(teams)

        # Test proper number of matches created
        n_teams = len(teams)
        expected_matches = self.h2h_event.n_matches * n_teams / 2
        self.assertEqual(len(matchups), expected_matches)

        # Test if there are any duplicate matches
        seen_pairs = set()
        duplicates = []

        for matchup in matchups:
            frozen_matchup = frozenset(matchup)
            if frozen_matchup in seen_pairs:
                duplicates.append(matchup)
            else:
                seen_pairs.add(frozen_matchup)

        self.assertEqual([], duplicates)


        # Test Teams have correct number of matches
        counter = defaultdict(int)
        for t1, t2 in matchups:
            counter[t1] += 1
            counter[t2] += 1

        self.assertEqual(max(counter.values()), min(counter.values()))
        self.assertEqual(self.h2h_event.n_matches, max(counter.values()))
        

    def test_create_event_ranking_h2h(self):
        self.h2h_event.create_event_ranking_h2h()
        ranking_objs = EventRanking_H2H.objects.filter(event=self.h2h_event)
        self.assertEqual(len(ranking_objs), self.brolympics.teams.count()) #2 because they were created in set up

    def test_create_bracket(self):
        self.h2h_event.create_bracket()
        self.assertIsNotNone(self.h2h_event.bracket_4)

class Event_H2HUtilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', is_available=(i%2==0), player_1=self.user) for i in range(8)]
        self.h2h_event = Event_H2H.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_matches=4,
        )

    def test_get_completed_event_comps_h2h(self):
        for _ in range(3):
            Competition_H2H.objects.create(event=self.h2h_event, is_complete=True)

        completed_events = self.h2h_event._get_completed_event_comps_h2h()

        self.assertEqual(len(completed_events), 3)

    def test_wipe_win_loss_sos_h2h(self):
        ranking = EventRanking_H2H.objects.create(event=self.h2h_event, team=self.teams[0])
        ranking.wins = 5
        ranking.losses = 3
        ranking.ties = 1
        ranking.score_for = 100
        ranking.score_against = 80
        ranking.sos_wins = 10
        ranking.sos_losses = 7
        ranking.sos_ties = 2
        ranking.save()

        ranking_qs = EventRanking_H2H.objects.filter(pk=ranking.pk)
        self.h2h_event._wipe_win_loss_sos_h2h(ranking_qs)
        ranking.refresh_from_db()

        # Assert that the values are reset to 0
        self.assertEqual(ranking.wins, 0)
        self.assertEqual(ranking.losses, 0)
        self.assertEqual(ranking.ties, 0)
        self.assertEqual(ranking.score_for, 0)
        self.assertEqual(ranking.score_against, 0)
        self.assertEqual(ranking.sos_wins, 0)
        self.assertEqual(ranking.sos_losses, 0)
        self.assertEqual(ranking.sos_ties, 0)

    def test_get_score_to_rank(self):
        score_to_rank = self.h2h_event._get_score_to_rank()
        expected_score_to_rank = {
            1: 10, 
            2: 8, 
            3: 7,  
            4: 5,  
            5: 4,  
            6: 3,  
            7: 2,  
            8: 1,
        }
        self.assertEqual(score_to_rank, expected_score_to_rank)

    def test_flatten_1(self):
        nested_list = [1, [2, 3, [4, 5]], [6, [7, 8]], 9, [10]]
        flattened_list = self.h2h_event.flatten_1(nested_list)
        expected_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(flattened_list, expected_list)

    def test_flatten_2(self):
        nested_list = [[1], [[2, 3], [4, 5]], [[6], [7, 8]], [9], [10]]
        flattened_list = self.h2h_event.flatten_2(nested_list)
        expected_list = [[1], [2, 3], [4, 5], [6], [7, 8], [9], [10]]
        self.assertEqual(flattened_list, expected_list)


class Event_H2HLifeCycleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.h2h_event = Event_H2H.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_matches=4,
        )
        self.h2h_event.start()
    

    def test_find_available_standard_comps(self):
        comps = self.h2h_event._find_available_standard_comps()
        self.assertEqual(len(comps), 16)

        self.teams[0].is_available = False
        self.teams[0].save()

        comps = self.h2h_event._find_available_standard_comps()
        self.assertEqual(len(comps), 12)

    def test_find_available_bracket_comps(self):
        comps = self.h2h_event._find_available_bracket_comps()
        self.assertEqual(len(comps), 0)

        self.h2h_event.bracket_4.championship.left.team_1 = self.teams[0]
        self.h2h_event.bracket_4.championship.left.team_2 = self.teams[1]
        self.h2h_event.bracket_4.championship.left.save()

        comps = self.h2h_event._find_available_bracket_comps()
        self.assertEqual(len(comps), 1)

    def test_find_available_comps_no_comps(self):
        self.h2h_event.is_round_robin_complete = False
        comps = self.h2h_event._find_available_standard_comps()
        self.assertEqual(len(comps), 16)

        self.h2h_event.is_round_robin_complete = True
        self.h2h_event.save()

        comps = self.h2h_event._find_available_bracket_comps()
        self.assertEqual(len(comps), 0)

    def test_update_event_rankings_h2h(self):
        t_1_rankings = EventRanking_H2H.objects.get(team=self.teams[0])
        t_2_rankings = EventRanking_H2H.objects.get(team=self.teams[1])
        t_3_rankings = EventRanking_H2H.objects.get(team=self.teams[2])
        t_4_rankings = EventRanking_H2H.objects.get(team=self.teams[3])

        t_1_rankings.wins = 4
        t_2_rankings.wins = 3
        t_3_rankings.wins = 2
        t_4_rankings.wins = 1

        t_1_rankings.save()
        t_2_rankings.save()
        t_3_rankings.save()
        t_4_rankings.save()

        self.h2h_event.update_event_rankings_h2h()

        rank_1 = EventRanking_H2H.objects.get(rank=1)
        rank_2 = EventRanking_H2H.objects.get(rank=2)
        rank_3 = EventRanking_H2H.objects.get(rank=3)
        rank_4 = EventRanking_H2H.objects.get(rank=4)

        t_1_rankings.refresh_from_db()
        t_2_rankings.refresh_from_db()
        t_3_rankings.refresh_from_db()
        t_4_rankings.refresh_from_db()

        self.assertEqual(rank_1, t_1_rankings)
        self.assertEqual(rank_2, t_2_rankings)
        self.assertEqual(rank_3, t_3_rankings)
        self.assertEqual(rank_4, t_4_rankings)
        self.assertEqual(10, t_1_rankings.points)
        self.assertEqual(8, t_2_rankings.points)
        self.assertEqual(7, t_3_rankings.points)
        self.assertEqual(5, t_4_rankings.points)
        pass

    def test_update_sos(self):
        team_1 = self.teams[0]
        team_2 = self.teams[1]
        team_3 = self.teams[2]

        Competition_H2H.objects.create(event=self.h2h_event, team_1=team_1, team_2=team_2, is_complete=True)
        Competition_H2H.objects.create(event=self.h2h_event, team_1=team_1, team_2=team_3, is_complete=True)

        team_2_ranking = EventRanking_H2H.objects.get(team=team_2)
        team_2_ranking.wins = 3
        team_2_ranking.losses = 1
        team_2_ranking.save()
        team_3_ranking = EventRanking_H2H.objects.get(team=team_3)
        team_3_ranking.wins = 1
        team_3_ranking.losses = 2
        team_3_ranking.ties = 1
        team_3_ranking.save()

        team_1_ranking = EventRanking_H2H.objects.get(team=team_1)

        team_rankings = [team_1_ranking, team_2_ranking, team_3_ranking]

        self.h2h_event._update_sos(team_rankings)

        self.assertEqual(team_1_ranking.sos_wins, 4)
        self.assertEqual(team_1_ranking.sos_losses, 3)
        self.assertEqual(team_1_ranking.sos_ties, 1)

    def test_isTeam1AboveTeam2(self):
        # Create base rankings
        team1 = self.teams[0]
        team2 = self.teams[1]
        t1_ranking = EventRanking_H2H.objects.create(
            event=self.h2h_event, 
            team= team1, 
            wins=0, 
            losses=0, 
            ties=0,
            score_for=0,
            score_against=0,
            sos_wins=0,
            sos_losses=0,
            sos_ties=0
        )
        t2_ranking = EventRanking_H2H.objects.create(
            event=self.h2h_event, 
            team=team2, 
            wins=0, 
            losses=0, 
            ties=0,
            score_for=0,
            score_against=0,
            sos_wins=0,
            sos_losses=0,
            sos_ties=0
        )

        # Test 1: Win rate
        t1_ranking.win_rate = 0.8
        t2_ranking.win_rate = 0.7
        self.assertTrue(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))
        t1_ranking.win_rate = .7
        t2_ranking.win_rate = .9
        self.assertFalse(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))

        # Reset win rates for next tests
        t1_ranking.win_rate = 0.5
        t2_ranking.win_rate = 0.5

        # Test 2: Head to head wins
        Competition_H2H.objects.create(event=self.h2h_event, team_1=team1, team_2=team2, winner=team1, is_complete=True)
        self.assertTrue(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))
        Competition_H2H.objects.create(event=self.h2h_event, team_1=team2, team_2=team1, winner=team2, is_complete=True)
        Competition_H2H.objects.create(event=self.h2h_event, team_1=team2, team_2=team1, winner=team2, is_complete=True)
        self.assertFalse(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))

        # Clear competitions for next tests
        Competition_H2H.objects.all().delete()

        # Test 3: Won games total
        t1_ranking.wins = 5
        t2_ranking.wins = 4
        self.assertTrue(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))
        t1_ranking.wins = 4
        t2_ranking.wins = 5
        self.assertFalse(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))

        # Reset wins for next tests
        t1_ranking.wins = 5
        t2_ranking.wins = 5

        # Test 4: Victory margin
        t1_ranking.score_for = 100
        t1_ranking.score_against = 80
        t2_ranking.score_for = 100
        t2_ranking.score_against = 90
        self.assertTrue(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))
        t1_ranking.score_against = 90
        t2_ranking.score_against = 80
        self.assertFalse(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))

        # Reset scores for next tests
        t1_ranking.score_for = 100
        t1_ranking.score_against = 90
        t2_ranking.score_for = 100
        t2_ranking.score_against = 90

        # Test 5: Strength of schedule
        t1_ranking.sos_wins = 8
        t1_ranking.sos_losses = 2
        t2_ranking.sos_wins = 7
        t2_ranking.sos_losses = 3
        self.assertTrue(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))
        t1_ranking.sos_wins = 7
        t1_ranking.sos_losses = 3
        t2_ranking.sos_wins = 8
        t2_ranking.sos_losses = 2
        self.assertFalse(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))

        # Reset SOS for next test
        t1_ranking.sos_wins = 8
        t1_ranking.sos_losses = 2
        t2_ranking.sos_wins = 8
        t2_ranking.sos_losses = 2

        # Test 6: Strength of schedule wins
        t1_ranking.sos_wins = 9
        t2_ranking.sos_wins = 8
        self.assertTrue(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))
        t1_ranking.sos_wins = 8
        t2_ranking.sos_wins = 9
        self.assertFalse(self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking))

        # Test 7: Randomness (run multiple times to check both outcomes)
        t1_ranking.sos_wins = 8
        t2_ranking.sos_wins = 8
        results = [self.h2h_event.isTeam1AboveTeam2(t1_ranking, t2_ranking) for _ in range(100)]
        self.assertTrue(any(results))
        self.assertFalse(all(results))

    @patch('random.random', return_value=0.3)
    def test_break_ties(self, mock_random):
        t_1_ranking = EventRanking_H2H.objects.create(
            event=self.h2h_event, 
            team=self.teams[0], 
            wins=1, 
            losses=0, 
            ties=0
        )
        t_2_ranking = EventRanking_H2H.objects.create(
            event=self.h2h_event, 
            team=self.teams[1], 
            wins=1, 
            losses=0, 
            ties=0
        )
        t_3_ranking = EventRanking_H2H.objects.create(
            event=self.h2h_event, 
            team=self.teams[2], 
            wins=1, 
            losses=0, 
            ties=0
        )
        rankings = [t_1_ranking, t_2_ranking, t_3_ranking]

        # Test Randomness (except we rigged it for the team1)
        result = self.h2h_event.break_ties(rankings)
        self.assertEqual(result, rankings)

        # Test SOS Wins
        t_3_ranking.sos_wins = 3
        t_1_ranking.sos_wins = 2
        t_1_ranking.sos_ties = 2
        t_2_ranking.sos_wins = 1
        t_2_ranking.sos_ties = 3

        t_1_ranking.save()
        t_2_ranking.save()
        t_3_ranking.save()
    
        result = self.h2h_event.break_ties(rankings)
        self.assertEqual(result, [t_3_ranking, t_1_ranking, t_2_ranking])

        # Test SOS Raw
        t_3_ranking.sos_wins = 4
        t_1_ranking.sos_wins = 1
        t_1_ranking.sos_ties = 3
        t_2_ranking.sos_wins = 2
        t_2_ranking.sos_ties = 0
        t_2_ranking.sos_losses = 2

        t_1_ranking.save()
        t_2_ranking.save()
        t_3_ranking.save()

        result = self.h2h_event.break_ties(rankings)
        self.assertEqual(result, [t_3_ranking, t_1_ranking, t_2_ranking])

        # Test Victory Margin
        t_1_ranking.score_for = 60
        t_1_ranking.score_against = 50
        t_2_ranking.score_for = 10
        t_2_ranking.score_against = 5
        t_3_ranking.score_for = 100
        t_3_ranking.score_against = 110

        result = self.h2h_event.break_ties(rankings)
        self.assertEqual(result, [t_1_ranking, t_2_ranking, t_3_ranking])

        # Test Won Games Total
        t_2_ranking.wins = 3
        t_3_ranking.wins = 2
        t_1_ranking.wins = 1

        result = self.h2h_event.break_ties(rankings)
        self.assertEqual(result, [t_2_ranking, t_3_ranking, t_1_ranking])

        # Test Head to Head Wins
        t_1_ranking.win_rate = 0.5
        t_2_ranking.win_rate = 0.5
        t_3_ranking.win_rate = 0.5

        Competition_H2H.objects.create(event=self.h2h_event, team_1=self.teams[0],team_2=self.teams[1], winner=self.teams[1], is_complete=True)
        Competition_H2H.objects.create(event=self.h2h_event, team_1=self.teams[1],team_2=self.teams[2], winner=self.teams[2], is_complete=True)
        Competition_H2H.objects.create(event=self.h2h_event, team_1=self.teams[2],team_2=self.teams[0], winner=self.teams[2], is_complete=True)

        t_1_ranking.save()
        t_2_ranking.save()
        t_3_ranking.save()

        results = self.h2h_event.break_ties(rankings)
        self.assertEqual(results, [t_3_ranking, t_2_ranking, t_1_ranking])

        # Test Winrate differences
        t_1_ranking.win_rate = 0.5
        t_2_ranking.win_rate = 0.6
        t_3_ranking.win_rate = 0.4
        for ranking in rankings:
            ranking.save()

        result = self.h2h_event.break_ties(rankings)
        self.assertEqual(result, [t_2_ranking, t_1_ranking, t_3_ranking])

    def test_check_for_round_robin_completion(self):
        no_completed = self.h2h_event.check_for_round_robin_completion()
        self.assertFalse(no_completed)

        all_comps = self.h2h_event.competition_h2h_set.all()
        all_comps.update(is_complete=True)

        completed = self.h2h_event.check_for_round_robin_completion()
        self.assertTrue(completed)

    def test_update_bracket(self):
        rankings = self.h2h_event.event_h2h_event_rankings.all()
  
        for i, ranking in enumerate(rankings):
            ranking.rank = i+1
            ranking.save()

        self.h2h_event._update_bracket()

        self.assertEqual(self.h2h_event.bracket_4.championship.left.team_1, rankings[0].team)
        self.assertEqual(self.h2h_event.bracket_4.championship.left.team_2, rankings[3].team)
        self.assertEqual(self.h2h_event.bracket_4.championship.right.team_1, rankings[2].team)
        self.assertEqual(self.h2h_event.bracket_4.championship.right.team_2, rankings[1].team)

    #Go back up to event ranking when youre done with ties

class Event_H2HCleanUpTests(TestCase):
    pass
    #complete this once you've finished testing for other models

class Competition_TeamTests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.team_event = Event_Team.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_competitions=2,
        )
        self.team_event.start()


    def test_start(self):
        comp = Competition_Team.objects.filter(event=self.team_event).first()
        comp.start()
        self.assertTrue(comp.is_active)
        self.assertLessEqual(comp.start_time, timezone.now())
        self.assertFalse(comp.team.is_available)

    @patch.object(EventRanking_Team, 'update_scores')
    @patch.object(Event_Team, 'update_event_rankings_team')
    def test_end(self, mock_update_event_rankings_team, mock_update_scores):
        comp = Competition_Team.objects.filter(event=self.team_event).first()
        team_score = 20
        comp.end(team_score)

        # Assert that the competition has ended correctly
        self.assertEqual(comp.team_score, team_score)
        self.assertEqual(comp.is_active, False)
        self.assertEqual(comp.is_complete, True)

        # Assert that the ranking's update_scores method was called
        mock_update_scores.assert_called_once()

        # Assert that the event's update_event_rankings_ind method was called
        mock_update_event_rankings_team.assert_called_once()


class Competition_IndTests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.ind_event = Event_IND.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_competitions=2,
        )
        self.ind_event.start()


    def test_start(self):
        comp = Competition_Ind.objects.filter(event=self.ind_event).first()
        comp.start()
        self.assertTrue(comp.is_active)
        self.assertLessEqual(comp.start_time, timezone.now())
        self.assertFalse(comp.team.is_available)

    @patch.object(EventRanking_Ind, 'update_scores')
    @patch.object(Event_IND, 'update_event_rankings_ind')
    def test_end(self, mock_update_event_rankings_ind, mock_update_scores):
        comp = Competition_Ind.objects.filter(event=self.ind_event).first()
        player_1_score, player_2_score = 10, 15
        comp.end(player_1_score, player_2_score)

        # Assert that the competition has ended correctly
        self.assertEqual(comp.player_1_score, player_1_score)
        self.assertEqual(comp.player_2_score, player_2_score)
        self.assertEqual(comp.team_score, player_1_score + player_2_score)
        self.assertEqual(comp.avg_score, (player_1_score + player_2_score) / 2)
        self.assertEqual(comp.is_active, False)
        self.assertEqual(comp.is_complete, True)

        # Assert that the ranking's update_scores method was called
        mock_update_scores.assert_called_once()

        # Assert that the event's update_event_rankings_ind method was called
        mock_update_event_rankings_ind.assert_called_once()


class Competition_H2HTests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.h2h_event = Event_H2H.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_matches=2,
        )
        self.h2h_event.start()


    def test_determine_winner(self):
        comp = Competition_H2H.objects.create(
            event=self.h2h_event,
            team_1=self.teams[0],
            team_2=self.teams[1]
        )
        team_1_score = 20
        team_2_score = 21
        winner, loser = comp.determine_winner(team_1_score, team_2_score)

        self.assertEqual(winner, self.teams[1])
        self.assertEqual(loser, self.teams[0])
        
        self.h2h_event.is_high_score_wins = False
        self.h2h_event.save()

        winner, loser = comp.determine_winner(team_1_score, team_2_score)

        self.assertEqual(winner, self.teams[0])
        self.assertEqual(loser, self.teams[1])

    def test_start(self):
        comp = Competition_H2H.objects.create(
            event=self.h2h_event,
            team_1=self.teams[0],
            team_2=self.teams[1]
        )
        comp.start()
        self.assertTrue(comp.is_active)
        self.assertLessEqual(comp.start_time, timezone.now())
        self.assertFalse(comp.team_1.is_available)
        self.assertFalse(comp.team_2.is_available)

    @patch.object(Event_H2H, 'update_event_rankings_h2h')
    def test_end(self, mock_update_event_rankings_h2h):
        comp = Competition_H2H.objects.create(
            event=self.h2h_event,
            team_1=self.teams[0],
            team_2=self.teams[1]
        )

        comp.end(21, 20)
        comp.refresh_from_db()
        mock_update_event_rankings_h2h.assert_called_once()
        team_1_ranking = EventRanking_H2H.objects.get(event=self.h2h_event, team=self.teams[0])
        team_2_ranking = EventRanking_H2H.objects.get(event=self.h2h_event, team=self.teams[1])

        self.assertEqual(comp.winner, self.teams[0])
        self.assertEqual(comp.loser, self.teams[1])
        self.assertTrue(comp.is_complete)
        self.assertFalse(comp.is_active)

        self.assertEqual(team_1_ranking.wins, 1)
        self.assertEqual(team_1_ranking.losses, 0)
        self.assertEqual(team_1_ranking.score_for, 21)
        self.assertEqual(team_1_ranking.score_against, 20)

        self.assertEqual(team_2_ranking.wins, 0)
        self.assertEqual(team_2_ranking.losses, 1)
        self.assertEqual(team_2_ranking.score_for, 20)
        self.assertEqual(team_2_ranking.score_against, 21)

        # Assert that the win rate is correctly calculated
        self.assertEqual(team_1_ranking.win_rate, 1.0)
        self.assertEqual(team_2_ranking.win_rate, 0.0)

        comp2 = Competition_H2H.objects.create(
            event=self.h2h_event,
            team_1=self.teams[0],
            team_2=self.teams[1]
        )

        comp2.end(10, 21)
        comp2.refresh_from_db()
        team_1_ranking = EventRanking_H2H.objects.get(event=self.h2h_event, team=self.teams[0])
        team_2_ranking = EventRanking_H2H.objects.get(event=self.h2h_event, team=self.teams[1])

        self.assertEqual(comp2.winner, self.teams[1])
        self.assertEqual(comp2.loser, self.teams[0])

        self.assertEqual(team_1_ranking.wins, 1)
        self.assertEqual(team_1_ranking.losses, 1)
        self.assertEqual(team_1_ranking.score_for, 31)
        self.assertEqual(team_1_ranking.score_against, 41)

        self.assertEqual(team_2_ranking.wins, 1)
        self.assertEqual(team_2_ranking.losses, 1)
        self.assertEqual(team_2_ranking.score_for, 41)
        self.assertEqual(team_2_ranking.score_against, 31)

        # Assert that the win rate is correctly calculated
        self.assertEqual(team_1_ranking.win_rate, 0.50)
        self.assertEqual(team_2_ranking.win_rate, 0.50)

class EventRanking_TeamTests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.team_event = Event_Team.objects.create(
            brolympics=self.brolympics,
            name="test event",
        )
        self.team_event.start()

    def test_update_scores(self):
        # Create and end some competitions
        for i in range(1, 5):
            comp = Competition_Team.objects.create(event=self.team_event, team=self.teams[0])
            comp.end(i*10)  

        event_ranking = EventRanking_Team.objects.get(event=self.team_event, team=self.teams[0])

        self.assertEqual(event_ranking.team_total_score, 10+20+30+40)  # 10+20+30+40 = 100
        self.assertEqual(event_ranking.team_avg_score, (10+20+30+40)/4)  # (10+20+30+40)/4 = 25

class EventRanking_IndTests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.ind_event = Event_IND.objects.create(
            brolympics=self.brolympics,
            name="test event",
        )
        self.ind_event.start()

    def test_update_scores(self):
        # Create and end some competitions
        for i in range(1, 5):
            comp = Competition_Ind.objects.create(event=self.ind_event, team=self.teams[0], display_avg_score=False)
            comp.end(i*10, i*15)  

        event_ranking = EventRanking_Ind.objects.get(event=self.ind_event, team=self.teams[0])

        self.assertEqual(event_ranking.player_1_total_score, 10+20+30+40)  # 10+20+30+40 = 100
        self.assertEqual(event_ranking.player_1_avg_score, (10+20+30+40)/4)  # (10+20+30+40)/4 = 25

        self.assertEqual(event_ranking.player_2_total_score, 15+30+45+60)  # 15+30+45+60 = 150
        self.assertEqual(event_ranking.player_2_avg_score, (15+30+45+60)/4)  # (15+30+45+60)/4 = 37.5

        self.assertEqual(event_ranking.team_total_score, (100+150))  # 100+150 = 250
        self.assertEqual(event_ranking.team_avg_score, (100+150)/4)  # 25 + 37.5 = 62.5
        
        self.ind_event.display_avg_scores = False
        self.ind_event.save()

        self.assertEqual(event_ranking.team_total_score, (100+150))  # 100+150 = 250
        self.assertEqual(event_ranking.team_avg_score, (100+150)/4)  # (100+150)/4 = 62.5



class EventRanking_H2HTests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.h2h_event = Event_H2H.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_matches=4,
        )
        self.h2h_event.start()

    def test_get_win_rate(self):
        event_ranking = self.h2h_event.event_h2h_event_rankings.first()
        self.assertEqual(event_ranking.get_win_rate(),0)

        event_ranking.wins = 3
        event_ranking.losses = 1
        event_ranking.save()

        self.assertEqual(event_ranking.get_win_rate(), .75)

        event_ranking.wins = 1
        event_ranking.losses = 1
        event_ranking.ties = 2
        event_ranking.save()

        self.assertEqual(event_ranking.get_win_rate(), 0.50)

class BracketMatchupTests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.h2h_event = Event_H2H.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_matches=4,
        )
        self.h2h_event.start()

    def test_initially_blank(self):
        all_matchups = BracketMatchup.objects.filter(bracket=self.h2h_event.bracket_4)
        for matchup in all_matchups:
            self.assertEqual(matchup.team_1, None)
            self.assertEqual(matchup.team_2, None)

    def test_update_teams(self):
        all_matchups = BracketMatchup.objects.filter(bracket=self.h2h_event.bracket_4)
        matchup_1 = all_matchups[0]

        matchup_1.update_teams(self.teams[0], self.teams[1])
        self.assertEqual(matchup_1.team_1, self.teams[0])
        self.assertEqual(matchup_1.team_2, self.teams[1])

    def test_start(self):
        all_matchups = BracketMatchup.objects.filter(bracket=self.h2h_event.bracket_4, winner_node__isnull=False)
        matchup_1 = all_matchups[0]
        matchup_1.update_teams(self.teams[0], self.teams[1])

        self.assertRaises(ValueError, matchup_1.start)        
        self.assertFalse(matchup_1.is_active)
        self.assertIsNone(matchup_1.start_time)
        self.assertTrue(matchup_1.team_1.is_available)
        self.assertTrue(matchup_1.team_2.is_available)

        matchup_1.bracket.is_active = True
        matchup_1.bracket.save()

        matchup_1.start()
        self.assertTrue(matchup_1.is_active)
        self.assertLessEqual(matchup_1.start_time, timezone.now())
        self.assertFalse(matchup_1.team_1.is_available)
        self.assertFalse(matchup_1.team_2.is_available)

    def test_end(self):
        all_matchups = BracketMatchup.objects.filter(bracket=self.h2h_event.bracket_4, winner_node__isnull=False)
        matchup_1 = all_matchups[0]
        matchup_1.update_teams(self.teams[0], self.teams[1])

        with self.assertRaises(Exception):
            matchup_1.end(10, 10)

        matchup_1.end(21, 20)
    
        self.assertIsNotNone(matchup_1.winner_node.team_1)
        self.assertIsNotNone(matchup_1.loser_node.team_1)
        self.assertIsNotNone(matchup_1.winner_node.team_1_seed)
        self.assertIsNotNone(matchup_1.loser_node.team_1_seed)

        # Test that if the championship and loser_bracket_finals are complete, finalize is called on the bracket
        matchup_1.bracket.loser_bracket_finals.is_complete = True
        matchup_1.bracket.loser_bracket_finals.winner=self.teams[1]
        matchup_1.bracket.loser_bracket_finals.loser=self.teams[3]
        matchup_1.bracket.loser_bracket_finals.save()

        finals_matchup = matchup_1.bracket.championship
        finals_matchup.update_teams(self.teams[0], self.teams[2])
        finals_matchup.end(21, 20)

        # Test that the bracket is finalized
        matchup_1.refresh_from_db()
        self.assertTrue(matchup_1.bracket.is_complete)

class Bracket_4Tests(TestCase):
    def setUp(self):    
        self.user = User.objects.create_user(
            uid="1",
            phone='1234567890', 
            email='jon_doe@test.com',
            password='Passw0rd@123',
            first_name='John',
            last_name='Doe',
        )
        self.league = League.objects.create(
            name='Test League', 
            league_owner=self.user
        )
    
        self.brolympics = Brolympics.objects.create(
            league=self.league, 
            name='Test Brolympics',
        )
        self.teams = [Team.objects.create(brolympics=self.brolympics, name=f'Team {i+1}', player_1=self.user) for i in range(8)]
        self.h2h_event = Event_H2H.objects.create(
            brolympics=self.brolympics,
            name="test event",
            n_matches=4,
        )
        

    def test_finalize(self):
        self.h2h_event.start()
        self.h2h_event.bracket_4.finalize()
        self.assertFalse(self.h2h_event.bracket_4.is_complete)

        self.h2h_event.bracket_4.championship.winner = self.teams[0]
        self.h2h_event.bracket_4.championship.loser = self.teams[1]
        self.h2h_event.bracket_4.loser_bracket_finals.winner = self.teams[2]
        self.h2h_event.bracket_4.loser_bracket_finals.loser = self.teams[3]
        
        self.h2h_event.bracket_4.championship.save()
        self.h2h_event.bracket_4.loser_bracket_finals.save()

        self.h2h_event.bracket_4.finalize()
        self.h2h_event.bracket_4.refresh_from_db()

        self.assertTrue(self.h2h_event.bracket_4.is_complete)
        self.assertFalse(self.h2h_event.bracket_4.is_active)

    def test_create_matchups(self):
        bracket = Bracket_4.objects.create(event=self.h2h_event)
        bracket.create_matchups()

        self.assertIsNotNone(bracket.championship)
        self.assertIsNotNone(bracket.loser_bracket_finals)

        championship = bracket.championship
        loser_bracket_finals = bracket.loser_bracket_finals
        one_four = championship.left
        two_three = championship.right

        self.assertEqual(one_four.team_1_seed, 1)
        self.assertEqual(one_four.team_2_seed, 4)
        self.assertEqual(one_four.winner_node, championship)
        self.assertEqual(one_four.loser_node, loser_bracket_finals)
        
        self.assertEqual(two_three.team_1_seed, 3)
        self.assertEqual(two_three.team_2_seed, 2)
        self.assertEqual(two_three.winner_node, championship)
        self.assertEqual(two_three.loser_node, loser_bracket_finals)

    def test_update_teams(self):
        playoff_teams = [
            EventRanking_H2H.objects.create(event=self.h2h_event, team=self.teams[i])
            for i in range(4)
        ]

        bracket = Bracket_4.objects.create(event=self.h2h_event)
        bracket.create_matchups()
        bracket.update_teams(playoff_teams)

        bracket.championship.left.team_1 = self.teams[0]
        bracket.championship.left.team_2 = self.teams[3]
        bracket.championship.right.team_1 = self.teams[1]
        bracket.championship.right.team_2 = self.teams[2]
    




        

        