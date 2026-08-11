from pathlib import Path

from django.conf import settings
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import (
    AnalysisControl,
    AsyncJob,
    CoverPage,
    Document,
    DocumentAnalysisRun,
    FlightPermit,
    PanelResponsible,
    Person,
    PersonGroup,
    Project,
    ProjectPanel,
    TechnicalDocument,
    TechnicalDocumentNotification,
    TechnicalDocumentStatusHistory,
)
from .services.document_extractor import IMAGE_EXTENSIONS, SUPPORTED_EXTENSIONS


User = get_user_model()

FLIGHT_PERMIT_DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png"
}
FLIGHT_PERMIT_DOCUMENT_MAX_SIZE = 15 * 1024 * 1024


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


class AsyncJobSerializer(serializers.ModelSerializer):
    job_type_display = serializers.CharField(source="get_job_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    document_name = serializers.CharField(source="document.original_name", read_only=True)

    class Meta:
        model = AsyncJob
        fields = [
            "id",
            "job_type",
            "job_type_display",
            "status",
            "status_display",
            "priority",
            "progress",
            "result",
            "error_message",
            "attempts",
            "max_attempts",
            "document",
            "document_name",
            "created_at",
            "started_at",
            "completed_at",
            "updated_at",
        ]
        read_only_fields = fields


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    prompt = serializers.CharField(
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
        max_length=8000,
    )
    use_ocr = serializers.BooleanField(default=False)
    use_ai = serializers.BooleanField(default=True)

    def validate_file(self, uploaded_file):
        suffix = ""
        if "." in uploaded_file.name:
            suffix = "." + uploaded_file.name.rsplit(".", 1)[-1].lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise serializers.ValidationError(f"Desteklenmeyen dosya tipi. Desteklenenler: {supported}")

        return uploaded_file

    def validate(self, attrs):
        if attrs["use_ai"] and not attrs["prompt"]:
            raise serializers.ValidationError({"prompt": ["AI ile işlemek için prompt zorunludur."]})

        suffix = Path(attrs["file"].name).suffix.lower()
        if suffix in IMAGE_EXTENSIONS and not attrs["use_ocr"]:
            raise serializers.ValidationError(
                {"use_ocr": ["Resim dosyalarından metin çıkarmak için OCR etkinleştirilmelidir."]}
            )
        return attrs


class AnalysisControlSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    database_id = serializers.IntegerField(source="pk", read_only=True)
    kind = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisControl
        fields = [
            "id",
            "database_id",
            "name",
            "description",
            "instructions",
            "severity",
            "is_active",
            "kind",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_id(self, control):
        return f"custom:{control.pk}"

    def get_kind(self, _control):
        return "custom"

    def validate_name(self, value):
        return value.strip()

    def validate_instructions(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Kontrol talimatı en az 10 karakter olmalıdır.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        owner = getattr(request, "user", None)
        name = attrs.get("name", getattr(self.instance, "name", ""))
        duplicate = AnalysisControl.objects.filter(owner=owner, name__iexact=name)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError({"name": ["Bu isimde bir kontrol zaten var."]})
        return attrs


class DocumentRagQuerySerializer(serializers.Serializer):
    query = serializers.CharField(trim_whitespace=True, min_length=2, max_length=8000)
    top_k = serializers.IntegerField(required=False, default=6, min_value=1, max_value=12)


class DocumentControlRunSerializer(serializers.Serializer):
    control_ids = serializers.ListField(
        child=serializers.CharField(max_length=80),
        required=False,
        default=list,
        max_length=10,
    )


class DocumentAnalysisRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnalysisRun
        fields = [
            "id",
            "document",
            "query",
            "status",
            "controls",
            "result",
            "error_message",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields


class PanelResponsibleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PanelResponsible
        fields = ["id", "panel", "name", "title", "email", "username", "order"]
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


class PersonSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Person
        fields = [
            "id", "name", "title", "email", "username",
            "groups", "created_at", "updated_at",
        ]
        read_only_fields = ["groups", "created_at", "updated_at"]


class PersonGroupSerializer(serializers.ModelSerializer):
    people = PersonSerializer(many=True, read_only=True)

    class Meta:
        model = PersonGroup
        fields = [
            "id", "name", "description", "order", "people",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class FlightPermitSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    permit_type_display = serializers.CharField(source="get_permit_type_display", read_only=True)
    validity_status = serializers.SerializerMethodField()
    validity_status_display = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    generated_document_url = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    updated_by_name = serializers.CharField(source="updated_by.username", read_only=True)
    remove_document = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = FlightPermit
        fields = [
            "id",
            "aircraft_number",
            "permit_number",
            "permit_type",
            "permit_type_display",
            "issuing_authority",
            "flight_region",
            "valid_from",
            "valid_until",
            "status",
            "status_display",
            "validity_status",
            "validity_status_display",
            "notes",
            "document",
            "document_name",
            "document_content_type",
            "document_size",
            "document_url",
            "generated_document_url",
            "remove_document",
            "created_by_name",
            "updated_by_name",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"document": {"write_only": True, "required": False}}
        read_only_fields = [
            "document_name",
            "document_content_type",
            "document_size",
            "created_at",
            "updated_at",
        ]

    def validate_aircraft_number(self, value):
        return value.strip().upper()

    def validate_permit_number(self, value):
        return value.strip().upper()

    def validate_document(self, uploaded_file):
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix not in FLIGHT_PERMIT_DOCUMENT_EXTENSIONS:
            allowed = ", ".join(sorted(FLIGHT_PERMIT_DOCUMENT_EXTENSIONS))
            raise serializers.ValidationError(f"Desteklenmeyen doküman tipi. Desteklenenler: {allowed}")
        if uploaded_file.size > FLIGHT_PERMIT_DOCUMENT_MAX_SIZE:
            raise serializers.ValidationError("Doküman boyutu 15 MB'dan büyük olamaz.")
        return uploaded_file

    def validate(self, attrs):
        valid_from = attrs.get("valid_from", getattr(self.instance, "valid_from", None))
        valid_until = attrs.get("valid_until", getattr(self.instance, "valid_until", None))
        if valid_from and valid_until and valid_until < valid_from:
            raise serializers.ValidationError(
                {"valid_until": ["Geçerlilik bitiş tarihi başlangıç tarihinden önce olamaz."]}
            )
        return attrs

    def get_validity_status(self, permit):
        today = timezone.localdate()
        if permit.status in {FlightPermit.STATUS_SUSPENDED, FlightPermit.STATUS_REVOKED}:
            return permit.status
        if permit.status == FlightPermit.STATUS_DRAFT:
            return "draft"
        if permit.valid_from > today:
            return "upcoming"
        if permit.valid_until < today:
            return "expired"
        if (permit.valid_until - today).days <= 30:
            return "expiring"
        return "active"

    def get_validity_status_display(self, permit):
        return {
            "draft": "Taslak",
            "upcoming": "Yaklaşan",
            "active": "Geçerli",
            "expiring": "Süresi Yaklaşıyor",
            "expired": "Süresi Doldu",
            "suspended": "Askıya Alındı",
            "revoked": "İptal Edildi",
        }[self.get_validity_status(permit)]

    def get_document_url(self, permit):
        if not permit.document:
            return ""
        return f"/api/flight-permits/{permit.pk}/document/"

    def get_generated_document_url(self, permit):
        return f"/api/flight-permits/{permit.pk}/generated-document/"

    @staticmethod
    def document_metadata(uploaded_file):
        return {
            "document_name": uploaded_file.name,
            "document_content_type": uploaded_file.content_type or "application/octet-stream",
            "document_size": uploaded_file.size,
        }

    def create(self, validated_data):
        validated_data.pop("remove_document", None)
        upload = validated_data.get("document")
        if upload:
            validated_data.update(self.document_metadata(upload))
        user = self.context["request"].user
        return FlightPermit.objects.create(
            **validated_data,
            created_by=user,
            updated_by=user,
        )

    def update(self, instance, validated_data):
        remove_document = validated_data.pop("remove_document", False)
        upload = validated_data.get("document")
        old_document_name = instance.document.name if instance.document else ""
        old_storage = instance.document.storage if instance.document else None

        if upload:
            validated_data.update(self.document_metadata(upload))
        elif remove_document:
            validated_data.update(
                {
                    "document": None,
                    "document_name": "",
                    "document_content_type": "",
                    "document_size": 0,
                }
            )

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.updated_by = self.context["request"].user
        instance.save()

        if old_document_name and (upload or remove_document) and old_storage:
            old_storage.delete(old_document_name)
        return instance


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


class OllamaChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant", "tool"])
    content = serializers.CharField(max_length=120_000, allow_blank=True, trim_whitespace=False)
    thinking = serializers.CharField(
        max_length=120_000, required=False, allow_blank=True, trim_whitespace=False
    )
    images = serializers.ListField(
        child=serializers.CharField(trim_whitespace=False),
        required=False,
        max_length=3,
    )
    tool_calls = serializers.JSONField(required=False)
    tool_name = serializers.CharField(max_length=120, required=False)

    def validate_images(self, images):
        total_size = sum(len(image) for image in images)
        if total_size > 28_000_000:
            raise serializers.ValidationError("Görsel verisi 20 MB sınırını aşıyor.")
        for image in images:
            if image.startswith("data:") and "," not in image:
                raise serializers.ValidationError("Geçersiz data URL görseli.")
        return [image.split(",", 1)[-1] if image.startswith("data:") else image for image in images]


class OllamaChatRequestSerializer(serializers.Serializer):
    model = serializers.CharField(max_length=160, required=False)
    messages = OllamaChatMessageSerializer(many=True, allow_empty=False, max_length=60)
    system_prompt = serializers.CharField(
        max_length=20_000, required=False, allow_blank=True, trim_whitespace=False
    )
    think = serializers.BooleanField(default=True)
    response_format = serializers.ChoiceField(
        choices=["text", "json"], default="text", required=False
    )
    tools = serializers.JSONField(required=False, default=list)
    temperature = serializers.FloatField(min_value=0, max_value=2, default=1.0)
    top_p = serializers.FloatField(min_value=0, max_value=1, default=0.95)
    top_k = serializers.IntegerField(min_value=0, max_value=200, default=64)
    num_ctx = serializers.IntegerField(min_value=512, max_value=131_072, default=8192)
    num_predict = serializers.IntegerField(min_value=-1, max_value=32_768, default=2048)
    seed = serializers.IntegerField(required=False, allow_null=True)
    keep_alive = serializers.RegexField(
        regex=r"^(?:0|\d+[smh])$", default="5m", required=False
    )

    def validate_tools(self, tools):
        if not isinstance(tools, list):
            raise serializers.ValidationError("Araç şeması bir JSON listesi olmalıdır.")
        if len(tools) > 20:
            raise serializers.ValidationError("En fazla 20 araç tanımlanabilir.")
        return tools

    def to_ollama_payload(self):
        data = self.validated_data
        messages = list(data["messages"])
        system_prompt = data.get("system_prompt", "").strip()
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        options = {
            "temperature": data["temperature"],
            "top_p": data["top_p"],
            "top_k": data["top_k"],
            "num_ctx": data["num_ctx"],
            "num_predict": data["num_predict"],
        }
        if data.get("seed") is not None:
            options["seed"] = data["seed"]

        payload = {
            "model": data.get("model") or settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": True,
            "think": data["think"],
            "keep_alive": data["keep_alive"],
            "options": options,
        }
        if data.get("response_format") == "json":
            payload["format"] = "json"
        if data.get("tools"):
            payload["tools"] = data["tools"]
        return payload
