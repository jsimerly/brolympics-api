from django.urls import path
from apps.brolympics.views import *
from apps.brolympics.active_views import *

urlpatterns = [
    #Create
    path('create-all-league/', CreateAllLeagueView.as_view(), name='create_all_league'),
    path('create-brolympics/', CreateBrolympics.as_view(), name='create_brolympics'),
    path('create-single-team/', CreateSingleTeam.as_view(), name='create_single_team'),
    path('create-event/', CreateSingleEvent.as_view(), name='create_single_event'),

    #Get
    path('all-leagues/', GetAllLeagues.as_view(), name='get_all_leagues'),
    path('league-info/<uuid:uuid>', GetLeagueInfo.as_view(), name='get_league_info'),
    path('get-brolympics-home/<uuid:uuid>', GetBrolympicsHome.as_view(), name='get_brolympics_home'),
    path('upcoming/', GetUpcoming.as_view(), name='get_upcoming'),
    path('league-teams/<uuid:uuid>', GetLeagueTeams.as_view(), name='league_teams'),
    path('all-comp-data/<uuid:uuid>', GetAllCompData.as_view(), name='get_comp_data'),
    path('bracket-data/<uuid:uuid>', GetBracketData.as_view(), name='bracket_data'),
    
    #Update
    path('update-brolympics/', UpdateBrolympics.as_view(), name='update_event'),
    path('update-league/', UpdateLeague.as_view()),
    path('update-league/image/', UpdateLeagueImage.as_view(),),
    path('update-event/', UpdateEvent.as_view(), name='update_event'),
    path('update-comp-h2h/', UpdateCompH2h.as_view(), name='update_comp_h2h'),
    path('update-comp-ind/', UpdateCompInd.as_view(), name='update_comp_ind'),
    path('update-comp-team/', UpdateCompTeam.as_view(), name='updated_comp_team'),
    path('update-bracket-comp/', UpdateBracketComp.as_view(), name='update_bracket_comp'),
    path('update-team-image/', UpdateTeamImage.as_view(), name='update_team_img'),


    #Delete
    path('delete-brolympics/<uuid:uuid>', DeleteBrolymics.as_view(), name='delete_brolympics'),
    path('delete-team/<uuid:uuid>', DeleteTeam.as_view(), name='delete_team'),
    path('remove-player-team/<str:player_uid>/<uuid:team_uuid>', RemovePlayerFromTeam.as_view(), name='remove_player_from_team'),
    path('delete-event-ind/<uuid:uuid>', DeleteIndEvent.as_view(), name='delete_event_ind'),
    path('delete-event-team/<uuid:uuid>', DeleteTeamEvent.as_view(), name='delete_event_team'),
    path('delete-event-h2h/<uuid:uuid>', DeleteH2hEvent.as_view(), name='delete_event_h2h'),

    #invites
    path('league-invite/<uuid:uuid>', GetLeagueInvite.as_view(), name='league_invite'),
    path('join-league/<uuid:uuid>', JoinLeague.as_view(), name='join_league'),
    path('brolympics-invite/<uuid:uuid>', GetBrolympicsInvite.as_view(), name='brolympics_invite'),
    path('join-brolympics/<uuid:uuid>', JoinBrolympics.as_view(), name='join_brolympics'),
    path('team-invite/<uuid:uuid>', GetTeamInvite.as_view(), name='team_invite'),
    path('join-team/<uuid:uuid>', JoinTeam.as_view(), name='join_team'),

    #Active Brolympics
    # Home Page
    path('start-brolympics/', StartBrolympics.as_view(), name='start_brolympics'),
    path('events-unstarted/<uuid:uuid>', UnstartedEvents.as_view(), name='unstarted-events'),
    path('start-event/', StartEvents.as_view(), name='start_event'),
    path('get-active-home/<uuid:uuid>', GetActiveHome.as_view(), name='get_active_home'),
    path('start-competition/', StartCompetition.as_view(), name='start_competition'),
    path('is-in-competition/', IsInCompetition.as_view(), name='is_in_competition'),
    path('get-comp-h2h/<uuid:uuid>', GetCompH2h.as_view(), name='get_comp_h2h'),
    path('get-comp-ind/<uuid:uuid>', GetCompInd.as_view(), name='get_comp_ind'),
    path('get-comp-team/<uuid:uuid>', GetCompTeam.as_view(), name='get_comp_team'),
    path('end-competition-h2h/', EndCompH2h.as_view(), name='end_comp_h2h'),
    path('end-competition-ind/', EndCompInd.as_view(), name='end_comp_ind'),
    path('end-competition-team/', EndCompTeam.as_view(), name='end_comp_team'),
    path('cancel-competition-h2h/', CancelCompH2h.as_view(), name='end_comp_h2h'),
    path('cancel-competition-ind/', CancelCompInd.as_view(), name='end_comp_ind'),
    path('cancel-competition-team/', CancelCompTeam.as_view(), name='end_comp_team'),

        # Teams
    path('get-team-info/<uuid:uuid>', GetTeamInfo.as_view(), name='get_team_info' ),

        #Events
    path('get-event-info/<uuid:uuid>/<str:type>', GetEventInfo.as_view(), name='get_event_info'),

        #Standings
    path('get-standings-info/<uuid:uuid>', GetStandingsInfo.as_view(), name='get_standings_info'),
]
