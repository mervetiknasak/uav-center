from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Max

from .models import Document, PanelResponsible, Project, ProjectPanel
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
        fields = ["id", "panel", "name", "title", "email", "phone", "order"]
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
