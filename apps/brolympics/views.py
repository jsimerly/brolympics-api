from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from apps.brolympics.models import *
from apps.brolympics.serializers import *
from apps.brolympics.active_serializers import EventCompSerailizer_h2h, EventCompSerailizer_ind, EventCompSerailizer_Team, BracketSerializer
import base64
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from PIL import Image
from io import BytesIO


User = get_user_model()

def convert_to_img_file(base_64_img, quality=85):
    if base_64_img is None:
        return None
    
    format, imgstr = base_64_img.split(';base64,')
    ext = format.split('/')[-1]
    decoded_img = base64.b64decode(imgstr)

    # Compress the image
    img = Image.open(BytesIO(decoded_img))

    # Depending on the extension apply compression
    buffer = BytesIO()

    if ext.lower() in ['jpeg', 'jpg']:
        img.save(buffer, format="JPEG", quality=quality)  # You can adjust the quality parameter
    elif ext.lower() == 'png':
        img.save(buffer, format="PNG", compress_level=5)  # compress_level range is 0-9
    else:
        # If not jpg or png, save with original decoded content
        return ContentFile(decoded_img, name='temp.' + ext)

    img_compressed = buffer.getvalue()
    
    return ContentFile(img_compressed, name='temp.' + ext)



# Create your views here.
class CreateAllLeagueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        league_data = request.data.get('league')
        league_img_b64 = league_data.get('img')
        league_data['img'] = convert_to_img_file(league_img_b64)

        brolympics_data = request.data.get('brolympics')
        brolympics_img_b64 = brolympics_data.get('img')
        brolympics_data['img'] = convert_to_img_file(brolympics_img_b64)

        h2h_event_data = request.data.get('h2h_events')
        ind_event_data = request.data.get('ind_events')
        team_event_data = request.data.get('team_events')

        league_serializer = LeagueCreateSerializer(data=league_data, context={'request': request})
        brolympics_serializer = BrolympicsCreateSerializer(data=brolympics_data)

        if league_serializer.is_valid():
            league = league_serializer.save()
        else:
            return Response(league_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        brolympics_data['league'] = league.id
        if brolympics_serializer.is_valid():
            brolympics = brolympics_serializer.save()
        else:
            return Response(brolympics_serializer.errors, status=400)

        for event_data_list in [h2h_event_data, ind_event_data, team_event_data]:
            for event_data in event_data_list:
                event_data['brolympics'] = brolympics.id


        h2h_serializer = EventH2HCreateAllSerializer(data=h2h_event_data, many=True)
        ind_serializer = EventIndCreateAllSerializer(data=ind_event_data, many=True) 
        team_serializer = EventTeamCreateAllSerializer(data=team_event_data, many=True) 

        if h2h_serializer.is_valid():
            h2h_serializer.save()
        else:
            return Response(h2h_serializer.errors, status=400)

        if ind_serializer.is_valid():
            ind_serializer.save()
        else:
            return Response(ind_serializer.errors, status=400)

        if team_serializer.is_valid():
            team_serializer.save()
        else:
            return Response(team_serializer.errors, status=400)
        

        all_league_serializer = AllLeaguesSerializer(league, context={'request' : request})

        data = all_league_serializer.data
        data['bro_uuid'] = brolympics.uuid

        return Response(data, status=status.HTTP_201_CREATED )
    
class CreateBrolympics(APIView):
    serializer_class = BrolympicsCreateSerializer

    def post(self, request):
        league_uuid = request.data.get('league_uuid')
        league = get_object_or_404(League, uuid=league_uuid)

        if request.user != league.league_owner:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        brolympics_data = request.data.get('brolympics')
        brolympics_img_b64 = brolympics_data.get('img')
        brolympics_data['img'] = convert_to_img_file(brolympics_img_b64)

        h2h_event_data = request.data.get('h2h_events')
        ind_event_data = request.data.get('ind_events')
        team_event_data = request.data.get('team_events')

        brolympics_serializer = self.serializer_class(data=brolympics_data)
        brolympics_data['league'] = league.id

        if brolympics_serializer.is_valid():
            brolympics = brolympics_serializer.save()
        else:
            print(brolympics_serializer.errors)
            return Response(brolympics_serializer.errors, status=400)

        for event_data_list in [h2h_event_data, ind_event_data, team_event_data]:
            for event_data in event_data_list:
                event_data['brolympics'] = brolympics.id


        h2h_serializer = EventH2HCreateAllSerializer(data=h2h_event_data, many=True)
        ind_serializer = EventIndCreateAllSerializer(data=ind_event_data, many=True) 
        team_serializer = EventTeamCreateAllSerializer(data=team_event_data, many=True) 

        if h2h_serializer.is_valid():
            h2h_serializer.save()
        else:
            print(h2h_serializer.errors)
            return Response(h2h_serializer.errors, status=400)

        if ind_serializer.is_valid():
            print(ind_serializer.errors)
            ind_serializer.save()
        else:
            return Response(ind_serializer.errors, status=400)

        if team_serializer.is_valid():
            print(team_serializer.errors)
            team_serializer.save()
        else:
            return Response(team_serializer.errors, status=400)
        
        data = {'uuid': brolympics.uuid}
        
        return Response(data, status=status.HTTP_201_CREATED)

        
    
class CreateSingleTeam(APIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            join_team = request.data.get('user_join')
            team = serializer.save()
            if join_team:
                team.add_player(request.user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CreateSingleEvent(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('event_name')
        type = request.data.get('type')
        bro_uuid = request.data.get('uuid')
        brolympics = Brolympics.objects.get(uuid=bro_uuid)

        event_data = {}

        if type == 'h2h':
            event = Event_H2H.objects.create(brolympics=brolympics, name=name)
            event_data = EventBasicSerializer_H2h(event).data

        elif type == 'ind':
            event = Event_IND.objects.create(brolympics=brolympics, name=name)
            event_data = EventBasicSerializer_Ind(event).data

        elif type == 'team':
            event = Event_Team.objects.create(brolympics=brolympics, name=name)
            event_data = EventBasicSerializer_Team(event).data
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(event_data, status=status.HTTP_200_OK)


# Get Info
class GetAllLeagues(APIView):
    serializer_class = AllLeaguesSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        leagues_as_owner = user.league_set.all()
        leagues_as_player = user.leagues.all()

        leagues = (leagues_as_player | leagues_as_owner).distinct() 
        serializer = self.serializer_class(leagues, many=True, context={'request': request})
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class GetLeagueInfo(APIView):
    serializer_class = LeagueInfoSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        league = get_object_or_404(League, uuid=uuid)
        serializer = self.serializer_class(league, context={'request' : request})


        return Response(serializer.data, status=status.HTTP_200_OK)
    

    
class GetBrolympicsHome(APIView):
    serializer_class = BrolympicsSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        brolympics = get_object_or_404(Brolympics, uuid=uuid)
        serializer = self.serializer_class(brolympics, context={'request':request})

        ## Need a new serializer to get active events
        #this will need to be a check, then we feed it to a different serializer to get the information we need. [pre, active, post]
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class GetUpcoming(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        brolympics = Brolympics.objects.filter(
            Q(players__in=[user]) | Q(league__league_owner=user)
        )
        upcoming_bro = brolympics.filter(is_active=False, is_complete=False)
        current_bro = Brolympics.objects.filter(is_active=True, is_complete=False)

        upcoming_comp_h2h = Competition_H2H.objects.filter(
            Q(team_1__player_1=user) | Q(team_1__player_2=user) | 
            Q(team_2__player_1=user) | Q(team_2__player_2=user),
            is_complete=False,
            start_time=None
        )
        upcoming_bracket_matchup = BracketMatchup.objects.filter(
            Q(team_1__player_1=user) | Q(team_1__player_2=user) | 
            Q(team_2__player_1=user) | Q(team_2__player_2=user),
            is_complete=False,
            start_time=None
        )
        upcoming_comp_ind = Competition_Ind.objects.filter(
            Q(team__player_1=user) | Q(team__player_2=user),
            is_complete=False,
            start_time=None
        )
        upcoming_comp_team = Competition_Team.objects.filter(
            Q(team__player_1=user) | Q(team__player_2=user),
            is_complete=False,
            start_time=None
        )

        upcoming_bro_serializer = BrolympicsSerializer(upcoming_bro, context={'request':request}, many=True)
        current_bro_serializer = BrolympicsSerializer(current_bro, context={'request':request}, many=True)

        h2h_serializer = CompetitionSerializer_H2h(upcoming_comp_h2h, many=True)
        bracket_serializer = BracketCompetitionSerializer_H2h(upcoming_bracket_matchup, many=True)
        ind_serializer = CompetitionSerializer_Ind(upcoming_comp_ind, many=True)
        team_serializer = CompetitionSerializer_Team(upcoming_comp_team, many=True)


        data = {
            'current_brolympics' :  current_bro_serializer.data,
            'upcoming_brolympics' : upcoming_bro_serializer.data,
            'upcoming_competitions' : h2h_serializer.data + bracket_serializer.data + ind_serializer.data + team_serializer.data
        }
        

        return Response(data, status=status.HTTP_200_OK)
    
class GetLeagueTeams(APIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        pass

class GetAllCompData(APIView):
    def get(self, request, uuid):

        brolympics = get_object_or_404(Brolympics, uuid=uuid)
        if request.user != brolympics.league.league_owner:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        all_events = brolympics.get_all_events()

        h2h_events = all_events['h2h']
        ind_events = all_events['ind']
        team_events = all_events['team']

        h2h_event_data = EventCompSerailizer_h2h(h2h_events, many=True).data
        ind_event_data = EventCompSerailizer_ind(ind_events, many=True).data
        team_event_data = EventCompSerailizer_Team(team_events, many=True).data

        data = {
            'h2h' : h2h_event_data,
            'ind' : ind_event_data,
            'team' : team_event_data,
        }

        return Response(data, status=status.HTTP_200_OK)
    
class GetBracketData(APIView):
    def get(self, request, uuid):
        brolympics = get_object_or_404(Brolympics, uuid=uuid)
        if request.user != brolympics.league.league_owner:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        h2h_events = Event_H2H.objects.filter(
            Q(is_active=True) | Q(is_complete=True),
            brolympics=brolympics
        )
        
        brackets = Bracket_4.objects.filter(event__in=h2h_events)
        bracket_data = BracketSerializer(brackets, many=True).data

        return Response(bracket_data, status=status.HTTP_200_OK)



## Updates ##
class UpdateBrolympics(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        uuid = request.data.get('uuid')
        brolympics = get_object_or_404(Brolympics, uuid=uuid)

        if request.user != brolympics.league.league_owner:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        img_b64 = request.data.get('img')

        if img_b64.startswith('data:image/') and ';base64,' in img_b64:
            data['img'] = convert_to_img_file(img_b64)
        else:
            del data['img']
            
        serializer = BrolympicsCreateSerializer(brolympics, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
        
class UpdateLeague(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        uuid = request.data.get('uuid')
        league = get_object_or_404(League, uuid=uuid)

        if request.user != league.league_owner:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        serializer = LeagueInfoSerializer(league, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.
            HTTP_400_BAD_REQUEST) 
    
    def delete(self, request):
        uuid = request.query_params.get('uuid')
        league = get_object_or_404(League, uuid=uuid)
        print(uuid)

        if request.user != league.league_owner:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            league_info = LeagueInfoSerializer(league).data
            league.delete()

            return Response({
                "message": "League successfully deleted",
                "deleted_league": league_info
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"An error occurred while deleting the league: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UpdateLeagueImage(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        uuid = request.data.get('uuid')
        league = get_object_or_404(League, uuid=uuid)

        if request.user != league.league_owner:
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        if 'image' not in request.FILES:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        image = request.FILES['image']
        league.img = image
        try:
            league.save()
            return Response(LeagueInfoSerializer(league).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UpdateEvent(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        event_uuid = request.data.get('uuid')
        event_type = request.data.get('type')

        for key, value in request.data.items():
            if value == '':
                request.data[key] = None

        if 'rules' in request.data and request.data['rules'] is not None:
            request.data['rules'] = request.data['rules'].strip()

        if event_type == 'h2h':
            event = get_object_or_404(Event_H2H, uuid=event_uuid)
            serializer = EventBasicSerializer_H2h(event, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif event_type == 'ind':
            event = get_object_or_404(Event_IND, uuid=event_uuid)
            serializer = EventBasicSerializer_Ind(event, data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif event_type == 'team':
            event = get_object_or_404(Event_Team, uuid=event_uuid)
            serializer = EventBasicSerializer_Team(event, data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_400_BAD_REQUEST)
    
class UpdateCompInd(APIView):
    def put(self, request):
        comp_uuid = request.data.get('uuid')
        comp = get_object_or_404(Competition_Ind, uuid=comp_uuid)

        if request.user != comp.event.brolympics.league.league_owner:
            return Response(status=status.HTTP_403_FORBIDDEN)
        

        player_1_score = request.data.get('player_1_score')
        player_2_score = request.data.get('player_2_score')

        if player_1_score == '' or player_1_score is None:
            return Response({'error':'Must enter a score for player 1.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if player_2_score == '' or player_2_score is None:
            return Response({'error':'Must enter a score for player 2.'}, status=status.HTTP_400_BAD_REQUEST)
        
        comp.admin_end(player_1_score, player_2_score)
        return Response(status=status.HTTP_200_OK)
        

class UpdateCompH2h(APIView):
    def put(self, request):
        comp_uuid = request.data.get('uuid')
        comp = get_object_or_404(Competition_H2H, uuid=comp_uuid)

        if request.user != comp.event.brolympics.league.league_owner:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        team_1_score = request.data.get('team_1_score')
        team_2_score = request.data.get('team_2_score')

        if team_1_score == '' or team_1_score is None:
            return Response({'error':'Must enter a score for team 1.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if team_2_score == '' or team_2_score is None:
            return Response({'error':'Must enter a score for team 2.'}, status=status.HTTP_400_BAD_REQUEST)
        
        comp.admin_end(team_1_score, team_2_score)
       
        return Response(status=status.HTTP_200_OK)


class UpdateCompTeam(APIView):
    def put(self, request):
        comp_uuid = request.data.get('uuid')
        comp = get_object_or_404(Competition_Team, uuid=comp_uuid)

        if request.user != comp.event.brolympics.league.league_owner:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        team_score = request.data.get('team_score')

        if team_score == '' or team_score is None:
            return Response({'error':'Must enter a score for player 1.'}, status=status.HTTP_400_BAD_REQUEST)
    
        comp.admin_end(team_score)
        return Response(status=status.HTTP_200_OK)
    

class UpdateBracketComp(APIView):
    def put(self, request):
        comp_uuid = request.data.get('uuid')
        comp = get_object_or_404(BracketMatchup, uuid=comp_uuid)

        if request.user != comp.event.brolympics.league.league_owner:
            return Response(status=status.HTTP_403_FORBIDDEN)

        team_1_score = request.data.get('team_1_score')
        team_2_score = request.data.get('team_2_score')

        if team_1_score == '' or team_1_score is None:
            return Response({'error':'Must enter a score for team 1.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if team_2_score == '' or team_2_score is None:
            return Response({'error':'Must enter a score for team 2.'}, status=status.HTTP_400_BAD_REQUEST)
        
        comp.end(team_1_score, team_2_score)
        
        return Response(status=status.HTTP_200_OK)

class UpdateTeamImage(APIView):
    def put(self, request):
        if 'image' not in request.FILES:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        image = request.FILES['image']
        team_uuid = request.data.get('uuid')
  
        team = get_object_or_404(Team, uuid=team_uuid)

        if request.user != team.player_1 and request.user != team.player_2 and request.user != team.brolympics.league.league_owner:
            raise PermissionDenied("You do not have permission to remove this player from this team.")

        team.img = image
        team.save()

        return Response(status=status.HTTP_200_OK)


## Delete ##

class DeleteBrolymics(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, uuid):
        brolympics = get_object_or_404(Brolympics, uuid=uuid)

        if self.request.user != brolympics.league.league_owner:
            print("DENIED")
            raise PermissionDenied("You do not have permission to delete this brolympics.")
        
        return brolympics

    def delete(self, request, uuid):
        print('here')
        brolympics = self.get_object(uuid)
        brolympics.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class DeleteTeam(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, uuid):
        team = get_object_or_404(Team, uuid=uuid)

        if self.request.user != team.player_1 and \
            self.request.user != team.player_2 and \
            self.request.user != team.brolympics.league.league_owner:
            raise PermissionDenied("You do not have permission to delete this league.")
        return team

    def delete(self, request, uuid):
        team = self.get_object(uuid)
        team.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class RemovePlayerFromTeam(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, player_uuid, team_uuid):
        player = get_object_or_404(User, uuid=player_uuid)
        team = get_object_or_404(Team, uuid=team_uuid)

        if self.request.user != team.player_1 and self.request.user != team.player_2 and self.request.user !=  team.brolympics.league.league_owner:
            raise PermissionDenied("You do not have permission to remove this player from this team.")
        return player, team     

    def delete(self, request, player_uuid, team_uuid):
        player, team = self.get_object(player_uuid, team_uuid)
        team.remove_player(player)

        return Response(status=status.HTTP_204_NO_CONTENT)
    

class DeleteIndEvent(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, uuid):
        event = get_object_or_404(Event_IND, uuid=uuid)

        if self.request.user != event.brolympics.league.league_owner:
            raise PermissionDenied("You do not have permission to delete events from this Brolympics.")
        
        return event
    
    def delete(self, request, uuid):
        event = self.get_object(uuid)
        event.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
class DeleteH2hEvent(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, uuid):
        event = get_object_or_404(Event_H2H, uuid=uuid)

        if self.request.user != event.brolympics.league.league_owner:
            raise PermissionDenied("You do not have permission to delete events from this Brolympics.")
        
        return event
    
    def delete(self, request, uuid):
        event = self.get_object(uuid)
        event.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
class DeleteTeamEvent(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, uuid):
        event = get_object_or_404(Event_Team, uuid=uuid)

        if self.request.user != event.brolympics.league.league_owner:
            raise PermissionDenied("You do not have permission to delete events from this Brolympics.")
        
        return event
    
    def delete(self, request, uuid):
        event = self.get_object(uuid)
        event.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

## Invites ##
class GetLeagueInvite(APIView):
    serializer_class = AllLeaguesSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, uuid):
        league = get_object_or_404(League, uuid=uuid)
        
        return league

    def get(self, request, uuid):
        league = self.get_object(uuid)
        serializer = self.serializer_class(league, context={'request' : request})

        return Response(serializer.data, status=status.HTTP_200_OK)
        

    
class JoinLeague(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid):
        league = get_object_or_404(League, uuid=uuid)
        user = request.user
        league.players.add(user)

        data = {
            'league_uuid':league.uuid, 
            'welcome_message' : f'Your request to join was successful. Welcome to {league.name}'
        }

        return Response(data,status=status.HTTP_200_OK)
        
class GetBrolympicsInvite(APIView):
    serializer_class = BrolympicsSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        broylmpics = get_object_or_404(Brolympics, uuid=uuid)
        serializer = self.serializer_class(broylmpics, context={'request':request})

        return Response(serializer.data, status=status.HTTP_200_OK)
            
class JoinBrolympics(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, uuid):
        brolympics = get_object_or_404(Brolympics, uuid=uuid)
        league = brolympics.league
        user = request.user

        brolympics.players.add(user)
        league.players.add(user)

        data = {
            'bro_uuid':brolympics.uuid, 
            'welcome_message' : f'Your request to join was successful. Welcome to {brolympics.name}'
        }

        return Response(data, status=status.HTTP_200_OK)
        

class GetTeamInvite(APIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        team = get_object_or_404(Team, uuid=uuid)
        serializer = self.serializer_class(team, context={'request':request})
        
        return Response(serializer.data, status=status.HTTP_200_OK)   
             
class JoinTeam(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid):
        team = get_object_or_404(Team, uuid=uuid)
        user = request.user
        team.brolympics.players.add(user)
        team.brolympics.league.players.add(user)
        try:
            team.add_player(user)
        except ValueError as e:
            Response({'detail':str(e)},status=status.HTTP_409_CONFLICT)

        data = {
            'bro_uuid':team.brolympics.uuid, 
            'welcome_message' : f'Your request to join was successful. Welcome to {team.name}'
        }

        return Response(data,status=status.HTTP_200_OK)
        