from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

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
            if (
                matching_user
                and matching_user.check_password(attrs.get("password"))
                and not matching_user.is_active
            ):
                raise serializers.ValidationError(
                    "Bu hesap aktif değil. Admin onayı bekliyor veya devre dışı bırakılmış."
                )

            raise serializers.ValidationError("Kullanıcı adı veya şifre hatalı.")

        if not user.is_active:
            raise serializers.ValidationError("Bu kullanıcı pasif durumda.")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(trim_whitespace=True, min_length=3, max_length=150)
    email = serializers.EmailField(trim_whitespace=True, max_length=254)
    password = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})
    password_confirm = serializers.CharField(
        trim_whitespace=False, style={"input_type": "password"}
    )

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
