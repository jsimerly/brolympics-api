from django.urls import path
from .views import SyncUserView, UserView, UserImageView

urlpatterns = [
    path('sync-user/', SyncUserView.as_view(), name='sync_user'),
    path('user/', UserView.as_view(), name='user_api'),
    path('user/image/', UserImageView.as_view(), name='user_image_api')
]