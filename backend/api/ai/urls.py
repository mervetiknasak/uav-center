from django.urls import path

from .views import OllamaChatView, OllamaPullView, OllamaStatusView, OllamaUnloadView

urlpatterns = [
    path("status/", OllamaStatusView.as_view(), name="ollama-status"),
    path("pull/", OllamaPullView.as_view(), name="ollama-pull"),
    path("unload/", OllamaUnloadView.as_view(), name="ollama-unload"),
    path("chat/", OllamaChatView.as_view(), name="ollama-chat"),
]
