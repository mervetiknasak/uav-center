from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.permissions import IsActiveAuthenticated
from .serializers import OperationalAlertResponseSerializer
from .services import build_operational_alerts


class OperationalAlertListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        payload = build_operational_alerts(
            as_of=timezone.localdate(),
            is_staff=request.user.is_staff,
        )
        return Response(OperationalAlertResponseSerializer(payload).data)
