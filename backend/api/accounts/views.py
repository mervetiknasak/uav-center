from django.contrib.auth import get_user_model, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..common.permissions import IsActiveAdminUser
from .serializers import (
    AdminUserSerializer,
    AdminUserStatusSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class CurrentUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated or not request.user.is_active:
            if request.user.is_authenticated:
                logout(request)
            return Response({"authenticated": False, "user": None})

        return Response(
            {
                "authenticated": True,
                "user": UserSerializer(request.user).data,
            }
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        login(request, serializer.validated_data["user"])
        return Response(
            {
                "authenticated": True,
                "user": UserSerializer(request.user).data,
            }
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "authenticated": False,
                "user": UserSerializer(user).data,
                "message": "Üyelik isteğiniz alındı. Admin onayından sonra giriş yapabilirsiniz.",
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsActiveAdminUser]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        return User.objects.order_by("is_active", "-date_joined")


class AdminUserStatusView(APIView):
    permission_classes = [IsActiveAdminUser]

    def patch(self, request, user_id):
        user = generics.get_object_or_404(User, pk=user_id)
        serializer = AdminUserStatusSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminUserSerializer(user).data)
