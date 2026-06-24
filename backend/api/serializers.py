from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import Document
from .services.document_extractor import SUPPORTED_EXTENSIONS


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]
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
            raise serializers.ValidationError("Kullanıcı adı veya şifre hatalı.")

        if not user.is_active:
            raise serializers.ValidationError("Bu kullanıcı pasif durumda.")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(trim_whitespace=True, min_length=3, max_length=150)
    password = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})

    def validate_username(self, username):
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("Bu kullanıcı adı zaten kullanılıyor.")

        return username

    def validate_password(self, password):
        validate_password(password)
        return password

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
        )


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
