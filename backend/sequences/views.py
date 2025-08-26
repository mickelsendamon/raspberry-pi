
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from .serializers import SequenceSerializer
from .models import Sequence


# Create your views here.
class SequenceCreateAPIView(CreateAPIView):
    queryset = Sequence.objects.all()
    serializer_class = SequenceSerializer


class SequenceDetailAPIView(RetrieveAPIView):
    lookup_field = 'sequence'
    queryset = Sequence.objects.all()
    serializer_class = SequenceSerializer
