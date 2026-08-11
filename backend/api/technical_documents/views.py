from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.permissions import IsActiveAdminUser
from ..organization.permissions import IsOrganizationReaderOrAdmin
from .adapters import DjangoEmailSender
from .selectors import technical_document_queryset
from .serializers import (
    NotificationIdempotencyKeySerializer,
    TechnicalDocumentNotificationRequestSerializer,
    TechnicalDocumentSerializer,
)
from .services.notifications import (
    NoNotificationRecipients,
    NotificationDeliveryError,
    NotificationInProgress,
    NotificationKeyConflict,
    NotificationOutcomeUnknown,
    send_document_notification,
)


class TechnicalDocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = TechnicalDocumentSerializer

    def get_queryset(self):
        queryset = technical_document_queryset()
        project_id = self.request.query_params.get("project")
        panel_id = self.request.query_params.get("panel")
        status_value = self.request.query_params.get("status")
        search = self.request.query_params.get("search", "").strip()

        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if panel_id:
            queryset = queryset.filter(panels__id=panel_id)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(title__icontains=search)
                | Q(category__icontains=search)
                | Q(owner_name__icontains=search)
                | Q(cover_page__number__icontains=search)
                | Q(cover_page__issue__icontains=search)
            )
        return queryset.distinct()


class TechnicalDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = TechnicalDocumentSerializer
    queryset = technical_document_queryset()
    lookup_url_kwarg = "technical_document_id"


class TechnicalDocumentNotifyView(APIView):
    permission_classes = [IsActiveAdminUser]

    def post(self, request, technical_document_id):
        document = generics.get_object_or_404(
            technical_document_queryset(),
            pk=technical_document_id,
        )
        serializer = TechnicalDocumentNotificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        idempotency_key = request.headers.get("Idempotency-Key")
        idempotency_serializer = NotificationIdempotencyKeySerializer(
            data={"idempotency_key": idempotency_key} if idempotency_key else {}
        )
        idempotency_serializer.is_valid(raise_exception=True)

        try:
            result = send_document_notification(
                document=document,
                actor=request.user,
                sender=DjangoEmailSender(),
                idempotency_key=idempotency_serializer.validated_data["idempotency_key"],
                subject=serializer.validated_data.get("subject", ""),
                message=serializer.validated_data.get("message", ""),
            )
        except NoNotificationRecipients:
            return Response(
                {"detail": "Seçili panellerde e-posta adresi bulunan sorumlu yok."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except NotificationDeliveryError as exc:
            return Response(
                {
                    "detail": "E-posta gönderilemedi. Hata denetim kaydına işlendi.",
                    "notification": {
                        "id": exc.notification.id,
                        "status": exc.notification.status,
                    },
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except NotificationInProgress:
            return Response(
                {"detail": "Aynı bildirim isteği halen işleniyor."},
                status=status.HTTP_409_CONFLICT,
            )
        except NotificationOutcomeUnknown as exc:
            return Response(
                {
                    "detail": (
                        "Bildirim teslim sonucu belirsiz. Yeni gönderimden önce "
                        "audit kaydını uzlaştırın."
                    ),
                    "notification": {
                        "id": exc.notification.id,
                        "status": exc.notification.status,
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )
        except NotificationKeyConflict:
            return Response(
                {"detail": "Idempotency-Key farklı bir bildirim isteği için kullanılmış."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {
                "message": (
                    "Aynı bildirim daha önce gönderildi; mevcut sonuç döndürüldü."
                    if result.deduplicated
                    else f"Bildirim {result.recipient_count} panel sorumlusuna gönderildi."
                ),
                "document": TechnicalDocumentSerializer(
                    technical_document_queryset().get(pk=document.pk),
                    context={"request": request},
                ).data,
            }
        )
