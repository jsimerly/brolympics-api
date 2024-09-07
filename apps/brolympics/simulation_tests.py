from django.test import TestCase
from apps.brolympics.models import *
import random


def create_scores(comp):
    max_score = comp.event.max_score
    min_score = comp.event.min_score
    score_type = comp.event.score_type

    if score_type == 'I':
        winning_score = max_score
        losing_score = random.randint(min_score, max_score-1)
    elif score_type == 'B':
        winning_score=1
        losing_score=0
    else:
        winning_score=round(random.uniform(min_score, max_score), 3)
        losing_score=round(random.uniform(min_score, max_score), 3)
    
    return winning_score, losing_score

def simulate_competition_h2h(comp: Competition_H2H_Base):
    comp.start()
    winning_score, losing_score = create_scores(comp)
    comp.end(winning_score, losing_score)

    print(f'{comp.team_1.name} {winning_score} v {comp.team_2.name} {losing_score}')
    

def simulate_competition_ind(comp: Competition_Ind):
    comp.start()
    player_1_score, player_2_score = create_scores(comp)
    comp.end(player_1_score, player_2_score)

    display_score = comp.avg_score if comp.display_avg_score else comp.team_score

    print(f'{comp.team.name}: {display_score}')

def simulate_competition_team(comp: Competition_Team):
    comp.start()
    _, score = create_scores(comp)
    comp.end(score)

    print(f'{comp.team.name}: {comp.team_score}')

def simulate_event_h2h(event: Event_H2H):
    print(f'\n --- {event.name} Started ---')
    event.start()
    counter = 0
    while not event.is_round_robin_complete:
        available_comps = event._find_available_standard_comps()
        
        comp = available_comps.first()
        simulate_competition_h2h(comp)

        counter += 1
        if counter > 100:
            break
        event.refresh_from_db()

    print('-- Round Robin Completed -- \n')
    rr_final_rankings = event.event_h2h_event_rankings.all().order_by('rank')
    max_name_length = max(len(ranking.team.name) for ranking in rr_final_rankings)

    print("Pre Bracket Standings")
    for ranking in rr_final_rankings:
        name = ranking.team.name.ljust(max_name_length)
        record = f"{ranking.wins}-{ranking.losses}"
        points = ranking.points
        sos = ranking.sos_wins
        margin = ranking.score_for - ranking.score_against
        print(f"{ranking.rank}) {name}  |  {record}  |  {points} pts |  {margin}  | {sos}")

    print('\n')
    print('--- Playoffs ---')

    simulate_competition_h2h(event.bracket_4.championship.left)
    simulate_competition_h2h(event.bracket_4.championship.right)
    event.refresh_from_db()
    simulate_competition_h2h(event.bracket_4.loser_bracket_finals)
    event.refresh_from_db()
    simulate_competition_h2h(event.bracket_4.championship)

    print('\nBracket Results')
    print(f"1) {event.bracket_4.championship.winner.name}")
    print(f"2) {event.bracket_4.championship.loser.name}")
    print(f"3) {event.bracket_4.loser_bracket_finals.winner.name}")
    print(f"4) {event.bracket_4.loser_bracket_finals.loser.name}")

    final_rankings = event.event_h2h_event_rankings.all().order_by('rank')
    print(f'\nFinal {event.name} Standings')

    for ranking in final_rankings:
        name = ranking.team.name.ljust(max_name_length)
        record = f"{ranking.wins}-{ranking.losses}"
        points = ranking.points

        print(f"{ranking.rank}) {name}  |  {record}  |  {points} pts")


    overall_rankings = event.brolympics.overall_ranking.all().order_by('rank')
    print('\n --- Updated Overall Rankings ---')
    for ranking in overall_rankings:
        name = ranking.team.name.ljust(max_name_length)
        record = f"{ranking.wins}-{ranking.losses}"
        points = ranking.total_points

        print(f"{ranking.rank}) {name}  |  {record}  |  {points} pts")
        
def simulate_event_ind(event: Event_IND):
    event.start()
    counter = 0
    
    print(f'\n --- {event.name} Started ---')
    for team in event.brolympics.teams.all():
        while event.get_team_next_comp_ind(team) is not None:
            comp = event.get_team_next_comp_ind(team)
            simulate_competition_ind(comp)

            counter += 1
            if counter > 100:
                break   

    final_rankings = event.event_ind_event_rankings.all().order_by('rank')
    print(f'\nFinal {event.name} Standings')
    max_name_length = max(len(ranking.team.name) for ranking in final_rankings)
    for ranking in final_rankings:
        name = ranking.team.name.ljust(max_name_length)
        if event.display_avg_scores:
            score = f"{ranking.team_avg_score}"
        else:
            score = f"{ranking.team_total_score}"
        points = ranking.points

        print(f"{ranking.rank}) {name}  |  {score}  |  {points} pts")


    overall_rankings = event.brolympics.overall_ranking.all().order_by('rank')
    print('\n --- Updated Overall Rankings ---')
    for ranking in overall_rankings:
        name = ranking.team.name.ljust(max_name_length)
        record = f"{ranking.wins}-{ranking.losses}"
        points = ranking.total_points

        print(f"{ranking.rank}) {name}  |  {record}  |  {points} pts")

def simulate_event_team(event: Event_Team):
    event.start()
    counter = 0
    for team in event.brolympics.teams.all():
        while event.get_team_next_comp_team(team) is not None:
            comp = event.get_team_next_comp_team(team)
            simulate_competition_team(comp)

            counter += 1
            if counter > 100:
                break

    final_rankings = event.event_team_event_rankings.all().order_by('rank')
    print(f'\nFinal {event.name} Standings')
    max_name_length = max(len(ranking.team.name) for ranking in final_rankings)
    for ranking in final_rankings:
        name = ranking.team.name.ljust(max_name_length)
        score = ranking.team_total_score
        points = ranking.points

        print(f"{ranking.rank}) {name}  |  {score}  |  {points} pts")


    overall_rankings = event.brolympics.overall_ranking.all().order_by('rank')
    print('\n --- Updated Overall Rankings ---')
    for ranking in overall_rankings:
        name = ranking.team.name.ljust(max_name_length)
        record = f"{ranking.wins}-{ranking.losses}"
        points = ranking.total_points

        print(f"{ranking.rank}) {name}  |  {record}  |  {points} pts")


def simulate_event(event):
    if isinstance(event, Event_H2H):
        simulate_event_h2h(event)
    if isinstance(event, Event_IND):
        simulate_event_ind(event)
    if isinstance(event, Event_Team):
        simulate_event_team(event)


class Simulation(TestCase):
    def setUp(self) -> None:
        return super().setUp()
    
    def test_run(self):
        player_list = [
            'Jacob Simerly',
            'Javi Canales',
            'Tanner Stis',
            'Max Zimmerman',
            'Alex Piroozi',
            'Timmy Becker',
            'Jonathan Gianakos',
            'Bryce Harter',
            'Alex Walker',
            'Davis Hagen',
            'Salvador Matus',
            'Anthony Golden',
            'Brady Johnson',
            'Jake Conrad',
            'Marcus Thompson',
            'Marcus Cousin',
            'Julian Simmerman',
            'David Tsetse',
            'Tanner Dye',
            'Cory Collins'
        ]

        event_list_h2h = [

            {
                'name' : 'Beer Die',
                'is_high_score_wins' : True,
                'max_score' : 15,
                'min_score' : 0,
                'n_matches' : 4,
                'n_active_limit' : 1,
            },
            {
                'name' : 'Cornhole',
                'is_high_score_wins' : True,
                'max_score' : 21,
                'min_score' : 0,
                'n_matches' : 4,
                'n_active_limit' : 2,
            },
            {
                'name' : 'Beer Pong',
                'is_high_score_wins' : False,
                'max_score' : 10,
                'min_score' : 0,
                'n_matches' : 4,
                'n_active_limit' : 1,
            },

            #Day 2

            {
                'name' : 'Pickleball',
                'max_score' : 11,
                'min_score' : 0,
                'n_matches' : 4,
                'n_active_limit' : 2,
            },

        ]

        event_list_ind = [
            {
                'name' : 'Foot Golf',
                'is_high_score_wins' : False,
                'max_score' : 120,
                'min_score' : 9,
            },
            #Day 2
            {
                'name' : 'Home Run Derby',
                'max_score' : 25,
                'min_score' : 0,
                'n_competitions' : 1,
                'n_active_limit' : 1,
            },
            {
                'name' : 'Go-Karting',
                'is_high_score_wins' : False,
                'max_score' : 50,
                'min_score' : 20,
                'n_competitions' : 1,
                'score_type' : '3'
            },
            {
                'name' : 'Mini-Golf',
                'is_high_score_wins' : False,
                'max_score' : 180,
                'min_score' : 18,
                'n_competitions' : 1,
            },
            {
                'name' : 'Bowling', 
                'max_score' : 300,
                'min_score' : 0,
                'n_competitions' : 1,
            }
        ]
    

        event_list_team = [
            {
                'name' : 'Trivia',
                'max_score' : 60,
                'min_score' : 0,
                'n_competitions' : 1,
            },
        ]

        #users register
        user_list = []
        for i, player in enumerate(player_list):
            formatted_i = str(i + 1).zfill(2)  # Convert i to string and pad with leading zeros
            phone_number = f'131728983{formatted_i}'
            first_name = player.split(' ')[0]
            last_name = player.split(' ')[1]
            email = f'{first_name}.{last_name}@test.com'

            user = User.objects.create(
                uid=str(i),
                phone=phone_number,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user_list.append(user)
        
        jacob = User.objects.get(last_name='Simerly')
        javi = User.objects.get(last_name='Canales')
        tanner_s = User.objects.get(last_name='Simerly')
        max = User.objects.get(last_name='Canales')
        alex_p = User.objects.get(last_name='Simerly')
        tim = User.objects.get(last_name='Canales')
        gio = User.objects.get(last_name='Simerly')
        bryce = User.objects.get(last_name='Canales')
        alex_w = User.objects.get(last_name='Simerly')
        davis_h = User.objects.get(last_name='Canales')
        sal = User.objects.get(last_name='Simerly')
        ag = User.objects.get(last_name='Canales')
        brady = User.objects.get(last_name='Simerly')
        conrad = User.objects.get(last_name='Canales')
        marcus = User.objects.get(last_name='Simerly')
        marcus_c = User.objects.get(last_name='Canales')
        julian = User.objects.get(last_name='Simerly')
        teste = User.objects.get(last_name='Canales')
        tanner_d = User.objects.get(last_name='Simerly')
        cory = User.objects.get(last_name='Canales')

        print('\n')
        print('Users Registered')
        league = League.objects.create(league_owner=jacob)
        print("League has been formed")
        brolympics = Brolympics.objects.create(
            league=league,
            name='Summer 2023'
        )
        print('Brolympics created')

        el_sal = Team.objects.create(
            brolympics=brolympics, name='El Salvador', player_1=jacob
        )
        germany = Team.objects.create(
            brolympics=brolympics, name='Germany', player_1=max
        )
        poland = Team.objects.create(
            brolympics=brolympics, name='Poland', player_1=alex_p
        )
        greece = Team.objects.create(
            brolympics=brolympics, name='Greece', player_1=gio
        )
        france = Team.objects.create(
            brolympics=brolympics, name='France', player_1=alex_w
        )
        mexico = Team.objects.create(
            brolympics=brolympics, name='Mexico', player_1=sal
        )
        north_k = Team.objects.create(
            brolympics=brolympics, name='North Korea', player_1=brady
        )
        usa = Team.objects.create(
            brolympics=brolympics, name='USA', player_1=marcus
        )
        italy = Team.objects.create(
            brolympics=brolympics, name='Italy', player_1=julian
        )
        # norway = Team.objects.create(
        #     brolympics=brolympics, name='Norway', player_1=tanner_d
        # )

        print('All Teams Created')

        el_sal.add_player(javi)
        germany.add_player(tanner_s)
        poland.add_player(tim)
        greece.add_player(bryce)
        france.add_player(davis_h)
        mexico.add_player(ag)
        north_k.add_player(conrad)
        usa.add_player(marcus_c)
        italy.add_player(teste)
        # norway.add_player(cory)

        print('All Players added to Team')
        print('\n')

        for event in event_list_h2h:
            brolympics.add_event_h2h(**event)
            name = event['name']
            print(f'{name} - Added')

        for event in event_list_ind:
            brolympics.add_event_ind(**event)
            name = event['name']
            print(f'{name} - Added')

        for event in event_list_team:
            brolympics.add_event_team(**event)
            name = event['name']
            print(f'{name} - Added')

        print('\n Set Up Completed, Ready for Brolympics! \n')

        brolympics.start()

        event_h2h = brolympics.event_h2h_set.all()
        event_ind = brolympics.event_ind_set.all()
        event_team = brolympics.event_team_set.all()


        for event in event_h2h:
            print(f'\n-------------------- {event.name} -----------------')
            simulate_event(event)
        for event in event_ind:
            print(f'\n-------------------- {event.name} -----------------')
            simulate_event(event)
        for event in event_team:
            print(f'\n-------------------- {event.name} -----------------')
            simulate_event(event)

    







    
            
        

