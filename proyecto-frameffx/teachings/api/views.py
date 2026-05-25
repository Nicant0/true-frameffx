from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from .serializers import TeachingSerializer
from teachings.models import Teaching
from .pagination import paginador_teaching1


class TeachingViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = TeachingSerializer
    pagination_class = paginador_teaching1

    def get_queryset(self):
        return Teaching.objects.all()


class TeachingAuthenticatedListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TeachingSerializer
    pagination_class = paginador_teaching1

    def get_queryset(self):
        return Teaching.objects.all()


class TeachingCRUDView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = TeachingSerializer
    queryset = Teaching.objects.all()
