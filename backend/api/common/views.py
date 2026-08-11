from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def health_check(_request):
    return Response(
        {
            "status": "ok",
            "service": "uav-center-backend",
            "timestamp": timezone.now().isoformat(),
        }
    )
