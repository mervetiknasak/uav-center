from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.permissions import IsActiveAuthenticated
from .models import AsyncJob
from .selectors import jobs_for_user
from .serializers import AsyncJobSerializer


class AsyncJobListView(generics.ListAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = AsyncJobSerializer

    def get_queryset(self):
        queryset = jobs_for_user(self.request.user)
        status_value = self.request.query_params.get("status", "").strip()
        if status_value in dict(AsyncJob.STATUS_CHOICES):
            queryset = queryset.filter(status=status_value)
        try:
            limit = min(max(int(self.request.query_params.get("limit", 100)), 1), 200)
        except (TypeError, ValueError):
            limit = 100
        return queryset[:limit]


class AsyncJobDetailView(generics.RetrieveAPIView):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = AsyncJobSerializer
    lookup_url_kwarg = "job_id"

    def get_queryset(self):
        return jobs_for_user(self.request.user)


class AsyncJobCancelView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, job_id):
        job = generics.get_object_or_404(AsyncJob, pk=job_id, owner=request.user)
        if job.status != AsyncJob.STATUS_QUEUED:
            return Response(
                {"detail": "Yalnızca sırada bekleyen joblar iptal edilebilir."},
                status=status.HTTP_409_CONFLICT,
            )
        now = timezone.now()
        updated = AsyncJob.objects.filter(
            pk=job.pk,
            owner=request.user,
            status=AsyncJob.STATUS_QUEUED,
        ).update(
            status=AsyncJob.STATUS_CANCELLED,
            completed_at=now,
            locked_at=None,
            locked_by="",
        )
        if not updated:
            return Response(
                {"detail": "Job worker tarafından alınmış; artık iptal edilemez."},
                status=status.HTTP_409_CONFLICT,
            )
        job.refresh_from_db()
        return Response(AsyncJobSerializer(job).data)
