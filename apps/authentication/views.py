import asyncio

from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from apps.authentication.firebase import FirebaseAuthentication
from rest_framework import status
import logging
from firebase_admin import auth, storage
from api.settings.base import FIREBASE_STORAGE_BUCKET

from .serializers import UserSerializer

User = get_user_model()
logger = logging.getLogger(__name__)

class SyncUserView(APIView):
    authentication_classes = [FirebaseAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_anonymous:
            logger.warning("Anonymous user tried to access SyncUserView")
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            "status": status.HTTP_200_OK,
            "message": "User synced successfully",
            "user_id": user.uid,
        })


class UserView(APIView):
    authentication_classes = [FirebaseAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class UserImageView(APIView):
    authentication_classes = [FirebaseAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        if 'image' not in request.FILES:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        image = request.FILES['image']
        
        try:
            logger.info(f"Attempting to upload image: {image.name}, size: {image.size} bytes")
            
            # Update the user's image field
            request.user.img = image
            request.user.save()
            
            # Get the URL of the uploaded image
            image_url = request.user.img.url
            
            logger.info(f"Image uploaded successfully for user {request.user.uid}")
            return Response({'message': 'Image uploaded successfully', 'image_url': image_url}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error in image upload process: {str(e)}")
            return Response({'error': f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            logger.exception(f"Error in GET request: {str(e)}")
            return Response({'error': f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

