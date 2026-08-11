from django.urls import path

from .views import (
    GroupPersonListCreateView,
    PanelResponsibleDetailView,
    PanelResponsibleListCreateView,
    PersonDetailView,
    PersonGroupDetailView,
    PersonGroupListCreateView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectPanelDetailView,
    ProjectPanelListCreateView,
)

urlpatterns = [
    path("projects/", ProjectListCreateView.as_view(), name="project-list"),
    path("projects/<int:project_id>/", ProjectDetailView.as_view(), name="project-detail"),
    path(
        "projects/<int:project_id>/panels/",
        ProjectPanelListCreateView.as_view(),
        name="project-panel-list",
    ),
    path("panels/<int:panel_id>/", ProjectPanelDetailView.as_view(), name="project-panel-detail"),
    path(
        "panels/<int:panel_id>/responsibles/",
        PanelResponsibleListCreateView.as_view(),
        name="panel-responsible-list",
    ),
    path(
        "responsibles/<int:responsible_id>/",
        PanelResponsibleDetailView.as_view(),
        name="panel-responsible-detail",
    ),
    path("person-groups/", PersonGroupListCreateView.as_view(), name="person-group-list"),
    path(
        "person-groups/<int:group_id>/", PersonGroupDetailView.as_view(), name="person-group-detail"
    ),
    path(
        "person-groups/<int:group_id>/people/",
        GroupPersonListCreateView.as_view(),
        name="group-person-list",
    ),
    path("people/<int:person_id>/", PersonDetailView.as_view(), name="person-detail"),
]
