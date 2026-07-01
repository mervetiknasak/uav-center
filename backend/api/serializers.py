from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Max

from .models import (
    CoverPage,
    Document,
    PanelResponsible,
    Project,
    ProjectPanel,
    TechnicalDocument,
    TechnicalDocumentNotification,
    TechnicalDocumentStatusHistory,
)
from .services.document_extractor import SUPPORTED_EXTENSIONS


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_active", "is_staff"]
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(trim_whitespace=True)
    password = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=attrs.get("username"),
            password=attrs.get("password"),
        )

        if user is None:
            matching_user = User.objects.filter(username__iexact=attrs.get("username")).first()
            if matching_user and matching_user.check_password(attrs.get("password")) and not matching_user.is_active:
                raise serializers.ValidationError("Bu hesap aktif değil. Admin onayı bekliyor veya devre dışı bırakılmış.")

            raise serializers.ValidationError("Kullanıcı adı veya şifre hatalı.")

        if not user.is_active:
            raise serializers.ValidationError("Bu kullanıcı pasif durumda.")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(trim_whitespace=True, min_length=3, max_length=150)
    email = serializers.EmailField(trim_whitespace=True, max_length=254)
    password = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})
    password_confirm = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})

    def validate_username(self, username):
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("Bu kullanıcı adı zaten kullanılıyor.")

        return username

    def validate_email(self, email):
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Bu e-posta adresi zaten kullanılıyor.")

        return email

    def validate_password(self, password):
        validate_password(password)
        return password

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": ["Şifreler aynı olmalı."]})

        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            is_active=False,
        )


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_active", "is_staff", "date_joined", "last_login"]
        read_only_fields = fields


class AdminUserStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

    def update(self, instance, validated_data):
        instance.is_active = validated_data["is_active"]
        instance.save(update_fields=["is_active"])
        return instance


class DocumentListSerializer(serializers.ModelSerializer):
    text_length = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "original_name",
            "content_type",
            "size",
            "prompt",
            "status",
            "ai_result",
            "error_message",
            "created_at",
            "processed_at",
            "text_length",
        ]
        read_only_fields = fields

    def get_text_length(self, document):
        return len(document.extracted_text or "")


class DocumentDetailSerializer(DocumentListSerializer):
    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + ["extracted_text"]


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    prompt = serializers.CharField(trim_whitespace=True, allow_blank=False, max_length=8000)

    def validate_file(self, uploaded_file):
        suffix = ""
        if "." in uploaded_file.name:
            suffix = "." + uploaded_file.name.rsplit(".", 1)[-1].lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise serializers.ValidationError(f"Desteklenmeyen dosya tipi. Desteklenenler: {supported}")

        return uploaded_file


class PanelResponsibleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PanelResponsible
        fields = ["id", "panel", "name", "title", "email", "phone", "username", "order"]
        read_only_fields = ["panel"]

    def create(self, validated_data):
        panel = validated_data["panel"]
        last_order = panel.responsibles.aggregate(max_order=Max("order"))["max_order"]
        validated_data["order"] = (last_order if last_order is not None else -1) + 1
        return super().create(validated_data)


class ProjectPanelSerializer(serializers.ModelSerializer):
    responsibles = PanelResponsibleSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectPanel
        fields = ["id", "project", "name", "description", "order", "responsibles"]
        read_only_fields = ["project"]


class ProjectSerializer(serializers.ModelSerializer):
    panels = ProjectPanelSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "code",
            "description",
            "is_active",
            "order",
            "created_at",
            "updated_at",
            "panels",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TechnicalDocumentPanelSerializer(serializers.ModelSerializer):
    responsible_count = serializers.IntegerField(source="responsibles.count", read_only=True)

    class Meta:
        model = ProjectPanel
        fields = ["id", "name", "responsible_count"]


class TechnicalDocumentStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.username", read_only=True)
    from_status_display = serializers.CharField(source="get_from_status_display", read_only=True)
    to_status_display = serializers.CharField(source="get_to_status_display", read_only=True)

    class Meta:
        model = TechnicalDocumentStatusHistory
        fields = [
            "id",
            "from_status",
            "from_status_display",
            "to_status",
            "to_status_display",
            "note",
            "changed_by_name",
            "created_at",
        ]


class TechnicalDocumentNotificationSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.CharField(source="sent_by.username", read_only=True)

    class Meta:
        model = TechnicalDocumentNotification
        fields = [
            "id",
            "subject",
            "message",
            "recipients",
            "recipient_count",
            "status",
            "error_message",
            "sent_by_name",
            "created_at",
        ]


class CoverPageSerializer(serializers.ModelSerializer):
    number = serializers.CharField(max_length=80, trim_whitespace=True)
    issue = serializers.CharField(max_length=40, trim_whitespace=True)

    class Meta:
        model = CoverPage
        fields = ["id", "number", "issue"]
        read_only_fields = ["id"]


class TechnicalDocumentSerializer(serializers.ModelSerializer):
    panels = serializers.PrimaryKeyRelatedField(
        queryset=ProjectPanel.objects.select_related("project"),
        many=True,
        required=False,
        write_only=True,
    )
    panel_details = TechnicalDocumentPanelSerializer(source="panels", many=True, read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_code = serializers.CharField(source="project.code", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    classification_display = serializers.CharField(source="get_classification_display", read_only=True)
    notification_recipients = serializers.SerializerMethodField()
    status_history = TechnicalDocumentStatusHistorySerializer(many=True, read_only=True)
    notifications = TechnicalDocumentNotificationSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    updated_by_name = serializers.CharField(source="updated_by.username", read_only=True)
    cover_page = CoverPageSerializer(required=False, allow_null=True)

    class Meta:
        model = TechnicalDocument
        fields = [
            "id",
            "project",
            "project_name",
            "project_code",
            "cover_page",
            "panels",
            "panel_details",
            "code",
            "title",
            "description",
            "category",
            "document_type",
            "revision",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "classification",
            "classification_display",
            "owner_name",
            "publication_date",
            "due_date",
            "review_date",
            "source_url",
            "notes",
            "notification_recipients",
            "last_notification_at",
            "last_notification_recipient_count",
            "status_history",
            "notifications",
            "created_by_name",
            "updated_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "last_notification_at",
            "last_notification_recipient_count",
            "created_at",
            "updated_at",
        ]

    def get_notification_recipients(self, document):
        recipients = {}
        for panel in document.panels.all():
            for responsible in panel.responsibles.all():
                if responsible.email:
                    recipients[responsible.email.lower()] = {
                        "name": responsible.name,
                        "email": responsible.email,
                        "panel": panel.name,
                    }
        return list(recipients.values())

    def validate_code(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        project = attrs.get("project", getattr(self.instance, "project", None))
        panels = attrs.get("panels")
        status_value = attrs.get("status", getattr(self.instance, "status", TechnicalDocument.STATUS_DRAFT))
        publication_date = attrs.get(
            "publication_date",
            getattr(self.instance, "publication_date", None),
        )
        cover_page = attrs.get("cover_page", serializers.empty)

        if panels is not None and project:
            invalid_panels = [panel.name for panel in panels if panel.project_id != project.id]
            if invalid_panels:
                raise serializers.ValidationError(
                    {"panels": [f"Seçilen paneller bu projeye ait değil: {', '.join(invalid_panels)}"]}
                )
        elif (
            self.instance
            and project
            and project.id != self.instance.project_id
            and self.instance.panels.exclude(project_id=project.id).exists()
        ):
            raise serializers.ValidationError(
                {
                    "panels": [
                        "Proje değiştirilirken yeni projeye ait panel seçimi de gönderilmelidir."
                    ]
                }
            )

        if status_value == TechnicalDocument.STATUS_PUBLISHED and not publication_date:
            raise serializers.ValidationError(
                {"publication_date": ["Yayınlanan bir doküman için yayın tarihi zorunludur."]}
            )

        if cover_page is not serializers.empty and cover_page is not None:
            if not cover_page.get("number") or not cover_page.get("issue"):
                raise serializers.ValidationError(
                    {"cover_page": ["Kapak sayfası numarası ve issue birlikte girilmelidir."]}
                )

        return attrs

    @staticmethod
    def resolve_cover_page(project, cover_page_data):
        if cover_page_data is None:
            return None
        cover_page, _ = CoverPage.objects.get_or_create(
            project=project,
            number=cover_page_data["number"].strip(),
            issue=cover_page_data["issue"].strip(),
        )
        return cover_page

    @transaction.atomic
    def create(self, validated_data):
        panels = validated_data.pop("panels", [])
        cover_page_data = validated_data.pop("cover_page", None)
        user = self.context["request"].user
        document = TechnicalDocument.objects.create(
            **validated_data,
            cover_page=self.resolve_cover_page(validated_data["project"], cover_page_data),
            created_by=user,
            updated_by=user,
        )
        document.panels.set(panels)
        TechnicalDocumentStatusHistory.objects.create(
            document=document,
            to_status=document.status,
            note="Doküman kaydı oluşturuldu.",
            changed_by=user,
        )
        return document

    @transaction.atomic
    def update(self, instance, validated_data):
        panels = validated_data.pop("panels", None)
        cover_page_data = validated_data.pop("cover_page", serializers.empty)
        previous_status = instance.status
        status_note = self.context["request"].data.get("status_note", "")
        user = self.context["request"].user

        for field, value in validated_data.items():
            setattr(instance, field, value)
        if cover_page_data is not serializers.empty:
            instance.cover_page = self.resolve_cover_page(instance.project, cover_page_data)
        instance.updated_by = user
        instance.save()
        if panels is not None:
            instance.panels.set(panels)

        if previous_status != instance.status:
            TechnicalDocumentStatusHistory.objects.create(
                document=instance,
                from_status=previous_status,
                to_status=instance.status,
                note=status_note,
                changed_by=user,
            )
        return instance


class TechnicalDocumentNotificationRequestSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255, required=False, allow_blank=True)
    message = serializers.CharField(max_length=5000, required=False, allow_blank=True)
