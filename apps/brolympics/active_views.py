from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from datetime import datetime
from apps.brolympics.models import *
from apps.brolympics.serializers import *
from apps.brolympics.active_serializers import *
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q


## Home Page Start
class StartBrolympics(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, uuid):
        brolympics = get_object_or_404(Brolympics, uuid=uuid)

        if self.request.user != brolympics.league.league_owner:
            raise PermissionDenied('You do not have permission to start this Brolympcs.')
        
        return brolympics

        
    def put(self, request):
        uuid = request.data.get('uuid')
        brolympics = self.get_object(uuid)

        if brolympics.teams.all().count() <= 1:
            return Response({'detail':'You cannot start this brolympics until it has at least 2 teams.'}, status=status.HTTP_412_PRECONDITION_FAILED)
        
        all_events = brolympics.get_all_events()
        total_events = len(all_events['h2h']) + len(all_events['ind']) + len(all_events['team']) 

        if total_events <= 0:
            return Response({'detail':'You cannot start this brolympics until it has at least 1 event.'}, status=status.HTTP_412_PRECONDITION_FAILED)
        
        brolympics.start()
        return Response(status=status.HTTP_200_OK)
    
class StartEvents(APIView):
    permission_classes = [IsAuthenticated]

    def confirm(self, event):
        if self.request.user != event.brolympics.league.league_owner:
            raise PermissionDenied('You do not have permission to start this event.')
        
        if event.is_active:
            raise ValueError('This event is already active.')
        
    def put(self, request):
        event_uuid = request.data.get('uuid')
        event_type = request.data.get('type')

        if event_type == 'h2h':
            event = get_object_or_404(Event_H2H, uuid=event_uuid)
            self.confirm(event)

            event.start()
            return Response(status=status.HTTP_200_OK)

        elif event_type == 'ind':
            event = get_object_or_404(Event_IND, uuid=event_uuid)
            self.confirm(event)

            event.start()
            return Response(status=status.HTTP_200_OK)

        elif event_type == 'team':
            event = get_object_or_404(Event_Team, uuid=event_uuid)
            self.confirm(event)

            event.start()
            return Response(status=status.HTTP_200_OK)
    
        return Response(status=status.HTTP_400_BAD_REQUEST)

class UnstartedEvents(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        brolympics = get_object_or_404(Brolympics, uuid=uuid)
        all_events = brolympics.get_all_events()

        h2h = all_events['h2h'].filter(is_active=False, is_complete=False)
        ind = all_events['ind'].filter(is_active=False, is_complete=False)
        team = all_events['team'].filter(is_active=False, is_complete=False)

        h2h_serializer = EventBasicSerializer_H2h(h2h, many=True)
        ind_serializer = EventBasicSerializer_Ind(ind, many=True) 
        team_serializer = EventBasicSerializer_Team(team, many=True)

        serializers = h2h_serializer.data + ind_serializer.data + team_serializer.data

        return Response(serializers, status=status.HTTP_200_OK)
    

class GetActiveHome(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, uuid):
        brolympics = get_object_or_404(Brolympics, uuid=uuid)
        return brolympics
    
    def get_available(self, qset):
        available = [
            event.find_available_comps(self.request.user)
            for event in qset
        ]
        return available
    
    def get_active(self, qset):
        active = [
            event.find_active_comps()
            for event in qset
        ]
        return active

    def get(self, request, uuid):
        brolympics = self.get_object(uuid)  
        event_map = brolympics.get_active_events()

        # Active Events
        h2h = event_map['h2h']
        ind = event_map['ind']
        team = event_map['team']

        h2h_event_serialized = HomeEventSerializer_H2h(
            h2h, 
            many=True, 
            ).data
        ind_event_serialized = HomeEventSerializer_Ind(
            ind, 
            many=True
            ).data
        team_event_serialized = HomeEventSerializer_Team(
            team, 
            many=True
            ).data

        all_serialized = h2h_event_serialized + ind_event_serialized + team_event_serialized
        all_serialized.sort(key=lambda x: x['start_time'] if x['start_time'] is not None else datetime.max, reverse=False)

        #Available_competitions
        h2h_available = {'std':[], 'bracket':[]}
        for event in h2h:
            comps = event.find_available_comps(request.user)
            h2h_available['std'].extend(comps['std'])
            if event.is_round_robin_complete:
                h2h_available['bracket'].extend(comps['bracket'])
        
        ind_available = self.get_available(ind)
        team_available = self.get_available(team)
        
        h2h_comp_serialized = CompetitionSerializer_H2h(
            h2h_available['std'], 
            many=True,
            context={'request': request}
            ).data 
        
        h2h_bracket_serialized = BracketCompetitionSerializer_H2h(
            h2h_available['bracket'], 
            many=True,
            context={'request': request}
            ).data 

        ind_comp_serialized = [
            comp 
            for qset in ind_available
            for comp in CompetitionSerializer_Ind(qset, many=True, context={'request': request}).data 

        ]
        team_comp_serializerd = [
            comp
            for qset in team_available
            for comp in CompetitionSerializer_Team(qset, many=True, context={'request': request}).data 
        ]
        available_comps = h2h_comp_serialized + ind_comp_serialized + team_comp_serializerd
        
        #Active
        h2h_active = {'std': [], 'bracket':[]}
        for event in h2h:
            comps = event.find_active_comps()
            h2h_active['std'].extend(comps['std'])
            h2h_active['bracket'].extend(comps['bracket'])

        ind_active = self.get_active(ind)
        team_active = self.get_active(team)

        bracket_active_serialized = BracketCompetitionSerializer_H2h(
            h2h_active['bracket'], 
            many=True,
            context={'request': request}
            ).data
        h2h_active_serialized = CompetitionSerializer_H2h(
            h2h_active['std'], 
            many=True,
            context={'request': request}
            ).data

        ind_active_serialized = [
            comp
            for qset in ind_active
            for comp in CompetitionSerializer_Ind(
                    qset, 
                    many=True,
                    context={'request': request}
                ).data
        ]

        team_active_serialized = [
            comp
            for qset in team_active
            for comp in CompetitionSerializer_Team(
                    qset, 
                    many=True,
                    context={'request': request}
                ).data 
        ] 

        all_active_data = h2h_active_serialized + ind_active_serialized + team_active_serialized + bracket_active_serialized
       
        data = {
            'active_events' : all_serialized,
            'available_competitions' : available_comps + h2h_bracket_serialized,
            'active_competitions' : all_active_data
        }

        return Response(data ,status=status.HTTP_200_OK)
    
class StartCompetition(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, comp_uuid, comp_type):
        if comp_type == 'h2h':
            comp = get_object_or_404(Competition_H2H, uuid=comp_uuid)
            return comp
        if comp_type == 'bracket':
            comp = get_object_or_404(BracketMatchup, uuid=comp_uuid)
            return comp

        if comp_type == 'ind':
            comp = get_object_or_404(Competition_Ind, uuid=comp_uuid)
            return comp
        
        if comp_type == 'team':
            comp = get_object_or_404(Competition_Team, uuid=comp_uuid)
            return comp

        raise ValueError('Cannot match the competition type.')


    def confirm(self, comp):        
        if comp.is_active:
            raise ValueError('This comp is already active.')
        
    def put(self, request):
        comp_uuid = request.data.get('uuid')
        comp_type = request.data.get('type')

        comp = self.get_object(comp_uuid, comp_type)
        comp.start()
        
        return Response({'comp_uuid': comp_uuid}, status=status.HTTP_200_OK)
    
class IsInCompetition(APIView):
    permission_classes = [IsAuthenticated]

    def find_comp(self, user):
        h2h = Competition_H2H.objects.filter(
            Q(team_1__player_1=user) | Q(team_1__player_2=user) | 
            Q(team_2__player_1=user) | Q(team_2__player_2=user),
            is_active=True,
        )
        if h2h.exists():
            return h2h.first(), 'h2h'

        bracket = BracketMatchup.objects.filter(
            Q(team_1__player_1=user) | Q(team_1__player_2=user) | 
            Q(team_2__player_1=user) | Q(team_2__player_2=user),
            is_active=True,
        )
        if bracket.exists():
            return bracket.first(), 'h2h'

        ind = Competition_Ind.objects.filter(
            Q(team__player_1=user) | Q(team__player_2=user),
            is_active=True,
        )
        if ind.exists():
            return ind.first(), 'ind'

        team = Competition_Team.objects.filter(
            Q(team__player_1=user) | Q(team__player_2=user),
            is_active=True,
        )
        if team.exists():
            return team.first(), 'team'
        
        user.is_available = True
        user.save()
        raise ValueError('No Competition currently exists')



    def get(self, request):
        user = request.user
        data = {
            'is_available' : True,
            'comp_uuid' : ''
        }
        if not user.is_available:
            comp, type = self.find_comp(user)
            data = {
                'is_available' : False,
                'comp_uuid' : comp.uuid,
                'type': type
            }

        return Response(data, status=status.HTTP_200_OK)
    
class GetCompH2h(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        h2h_comp_qset = Competition_H2H.objects.filter(uuid=uuid)

        if h2h_comp_qset.exists():
            comp = h2h_comp_qset.first()
            comp_serializer = CompetitionMScoresSerializer_H2h(comp, context={'request':request})
            return Response(comp_serializer.data, status=status.HTTP_200_OK)
        
        bracket_comp_qset = BracketMatchup.objects.filter(uuid=uuid)
        if bracket_comp_qset.exists():
            comp = bracket_comp_qset.first()
            comp_serializer = CompetitionMScoresSerializer_Bracket(comp, context={'request':request})
            return Response(comp_serializer.data, status=status.HTTP_200_OK)
        
        return ResourceWarning(status=status.HTTP_404_NOT_FOUND)
     
class GetCompInd(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        comp = get_object_or_404(Competition_Ind, uuid=uuid)
        serializer = CompetitionMScoresSerializer_Ind(comp, context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class GetCompTeam(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        comp = get_object_or_404(Competition_Team, uuid=uuid)
        serializer = CompetitionMScoresSerializer_Team(comp, context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class EndCompH2h(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        comp_uuid = request.data.get('uuid')

        try:
            team_1_score = float(request.data.get('team_1_score'))
            team_2_score = float(request.data.get('team_2_score'))
        except ValueError:
            return Response({'error': 'Invalid Score'}, status=status.HTTP_400_BAD_REQUEST)

        h2h_comp_qset = Competition_H2H.objects.filter(uuid=comp_uuid)

        if h2h_comp_qset.exists():
            comp = h2h_comp_qset.first()

            if comp.is_complete:
                return Response({'message':'This competition was already completed.'}, status=status.HTTP_409_CONFLICT)
            
            comp.end(team_1_score, team_2_score)
            return Response(status=status.HTTP_200_OK)

        bracket_comp_qset = BracketMatchup.objects.filter(uuid=comp_uuid)
        if bracket_comp_qset.exists():
            comp = bracket_comp_qset.first()
            comp.end(team_1_score, team_2_score)

            return Response(status=status.HTTP_200_OK)

        
        return Response(status=status.HTTP_404_NOT_FOUND)
    
class EndCompInd(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        comp_uuid = request.data.get('uuid')

        try:
            player_1_score = float(request.data.get('player_1_score'))
            player_2_score = float(request.data.get('player_2_score'))
        except ValueError:
            return Response({'error': 'Invalid Score'}, status=status.HTTP_400_BAD_REQUEST)
        
        comp = get_object_or_404(Competition_Ind, uuid=comp_uuid)
        comp.end(player_1_score, player_2_score)

        return Response(status=status.HTTP_200_OK) 
    

class EndCompTeam(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        comp_uuid = request.data.get('uuid')

        try:
            team_score = float(request.data.get('team_score'))
        except ValueError:
            return Response({'error': 'Invalid Score'}, status=status.HTTP_400_BAD_REQUEST)
        
        comp = get_object_or_404(Competition_Team, uuid=comp_uuid)
        comp.end(team_score)

        return Response(status=status.HTTP_200_OK) 
    


class CancelCompH2h(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        comp_uuid = request.data.get('uuid')

        h2h_comp_qset = Competition_H2H.objects.filter(uuid=comp_uuid)        
        if h2h_comp_qset.exists():
            comp = h2h_comp_qset.first()
            if not comp.is_complete:
                comp.cancel()

            return Response(status=status.HTTP_200_OK)

        bracket_comp_qset = BracketMatchup.objects.filter(uuid=comp_uuid)
        if bracket_comp_qset.exists():
            comp = bracket_comp_qset.first()
            if not comp.is_complete:
                comp.cancel()

            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)

class CancelCompInd(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        comp_uuid = request.data.get('uuid')        
        comp = get_object_or_404(Competition_Ind, uuid=comp_uuid)
        if not comp.is_complete:
            comp.cancel()

        return Response(status=status.HTTP_200_OK) 

class CancelCompTeam(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        comp_uuid = request.data.get('uuid')        
        comp = get_object_or_404(Competition_Team, uuid=comp_uuid)
        if not comp.is_complete:
            comp.cancel()

        return Response(status=status.HTTP_200_OK) 
    

## Home Page End ##

## Team Page

class GetTeamInfo(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, uuid):
        team = get_object_or_404(Team, uuid=uuid)
        team_data = TeamPageSerailizer(team).data

        h2h_rankings = EventRanking_H2H.objects.filter(team=team)
        h2h_ranking_data = EventRankingSerializer_H2h(h2h_rankings, many=True).data

        ind_rankings = EventRanking_Ind.objects.filter(team=team)
        ind_ranking_data = EventRankingSerializer_Ind(ind_rankings, many=True).data

        team_rankings = EventRanking_Team.objects.filter(team=team)
        team_ranking_data = EventRankingSerializer_Team(team_rankings, many=True).data

        all_event_data = h2h_ranking_data + ind_ranking_data + team_ranking_data

        data = {
            'team' : team_data,
            'events': all_event_data 
        }

        return Response(data, status=status.HTTP_200_OK)
    

# Event Page 
class GetEventInfo(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid, type):
        if type == 'h2h':
            event = get_object_or_404(Event_H2H, uuid=uuid)

            if event.is_active or event.is_complete:
                event_rankings = EventRanking_H2H.objects.filter(event=event)
                ranking_data = EventPageSerializer_h2h(event_rankings, many=True, context={'request': request})

                comps = Competition_H2H.objects.filter(event=event)
                comp_data = CompetitionSerializer_H2h(comps, many=True, context={'request': request})

                bracket = BracketSerializer(event.bracket_4, context={'request': request})

                data = {
                    'type' : 'h2h',
                    'standings' : ranking_data.data,
                    'competitions' : comp_data.data,
                    'bracket' : bracket.data,
                    'is_complete' : event.is_complete
                }

                return Response(data, status=status.HTTP_200_OK)
            
            return Response({'message':'Event has not started yet.'}, status=status.HTTP_200_OK)
            

        if type == 'ind':
            event = get_object_or_404(Event_IND, uuid=uuid)

            if event.is_active or event.is_complete:
                event_rankings = EventRanking_Ind.objects.filter(event=event)
                ranking_data = EventPageSerializer_ind(event_rankings, many=True, context={'request': request})

                comps = Competition_Ind.objects.filter(event=event)
                comp_data = CompetitionSerializer_Ind(comps, many=True, context={'request': request})

                data = {
                    'type' : 'ind',
                    'standings' : ranking_data.data,
                    'competitions' : comp_data.data,
                    'is_complete' : event.is_complete
                }

                return Response(data, status=status.HTTP_200_OK)
            
            return Response({'message':'Event has not started yet.'}, status=status.HTTP_200_OK)

        if type == 'team':
            event = get_object_or_404(Event_Team, uuid=uuid)
            if event.is_active or event.is_complete:
                event_rankings = EventRanking_Team.objects.filter(event=event)
                ranking_data = EventPageSerializer_team(event_rankings, many=True, context={'request': request})

                comps = Competition_Team.objects.filter(event=event)
                comp_data = CompetitionSerializer_Team(comps, many=True, context={'request': request})

                data = {
                    'type' : 'team',
                    'standings' : ranking_data.data,
                    'competitions' : comp_data.data,
                    'is_complete' : event.is_complete,
                }

                return Response(data, status=status.HTTP_200_OK)
            
            return Response({'message':'Event has not started yet.'}, status=status.HTTP_200_OK)


        return Response(status=status.HTTP_400_BAD_REQUEST)
    
class GetStandingsInfo(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_podiums(self, events, ranking_model):
        event_data = []
        for event in events:
            podium_data = { 'event' : event.name}

            first = ranking_model.objects.filter(event=event, rank=1)
            second = ranking_model.objects.filter(event=event, rank=2)
            third = ranking_model.objects.filter(event=event, rank=3)
            

            teams_first = [ranking.team for ranking in first] if first.exists() else []
            podium_data['first'] = SmallTeamSerializer(teams_first, many=True, context={'request': self.request}).data

            teams_second = [ranking.team for ranking in second] if second.exists() else []
            podium_data['second'] = SmallTeamSerializer(teams_second, many=True, context={'request': self.request}).data

            teams_third = [ranking.team for ranking in third] if third.exists() else []
            podium_data['third'] = SmallTeamSerializer(teams_third, many=True, context={'request': self.request}).data
   
            event_data.append(podium_data)

        return event_data
    
    def get(self, request, uuid):
        brolympics = get_object_or_404(Brolympics, uuid=uuid)
        all_rankings = brolympics.overall_ranking.all()

        overall_rank_serializer = OverallRankingSerializer(all_rankings, many=True, context={'request':request})

        completed_events_h2h = Event_H2H.objects.filter(is_complete=True, brolympics=brolympics)
        completed_events_ind = Event_IND.objects.filter(is_complete=True, brolympics=brolympics)
        completed_events_team = Event_Team.objects.filter(is_complete=True, brolympics=brolympics)

        h2h_podiums = self.get_podiums(completed_events_h2h, EventRanking_H2H)
        ind_podiums = self.get_podiums(completed_events_ind, EventRanking_Ind)
        team_podiums = self.get_podiums(completed_events_team, EventRanking_Team)

        podiums = h2h_podiums + ind_podiums + team_podiums
            
        data = {
            'standings': overall_rank_serializer.data,
            'podiums' : podiums
        }

        return Response(data, status=status.HTTP_200_OK)


