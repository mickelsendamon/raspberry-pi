from django.urls import path
from .views import SequenceCreateAPIView, SequenceDetailAPIView

urlpatterns = [
    path('sequences/new/', SequenceCreateAPIView.as_view(), name='sequence_create_api'),
    path('sequences/<str:sequence>/', SequenceDetailAPIView.as_view(), name='sequence_retrieve_api')
]
