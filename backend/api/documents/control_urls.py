from django.urls import path

from .views import AnalysisControlDetailView, AnalysisControlListCreateView

urlpatterns = [
    path("", AnalysisControlListCreateView.as_view(), name="analysis-control-list"),
    path("<int:control_id>/", AnalysisControlDetailView.as_view(), name="analysis-control-detail"),
]
