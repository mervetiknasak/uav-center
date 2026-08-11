from rest_framework import generics

from .models import PanelResponsible, PersonGroup, Project, ProjectPanel
from .permissions import IsOrganizationReaderOrAdmin
from .selectors import (
    groups_with_people,
    panels_with_responsibles,
    people_with_groups,
    projects_with_structure,
)
from .serializers import (
    PanelResponsibleSerializer,
    PersonGroupSerializer,
    PersonSerializer,
    ProjectPanelSerializer,
    ProjectSerializer,
)


class ProjectListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return projects_with_structure()


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = ProjectSerializer
    queryset = projects_with_structure()
    lookup_url_kwarg = "project_id"


class ProjectPanelListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = ProjectPanelSerializer

    def get_queryset(self):
        return panels_with_responsibles().filter(project_id=self.kwargs["project_id"])

    def perform_create(self, serializer):
        project = generics.get_object_or_404(Project, pk=self.kwargs["project_id"])
        serializer.save(project=project)


class ProjectPanelDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = ProjectPanelSerializer
    queryset = panels_with_responsibles()
    lookup_url_kwarg = "panel_id"


class PanelResponsibleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PanelResponsibleSerializer

    def get_queryset(self):
        return PanelResponsible.objects.filter(panel_id=self.kwargs["panel_id"])

    def perform_create(self, serializer):
        panel = generics.get_object_or_404(ProjectPanel, pk=self.kwargs["panel_id"])
        serializer.save(panel=panel)


class PanelResponsibleDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PanelResponsibleSerializer
    queryset = PanelResponsible.objects.all()
    lookup_url_kwarg = "responsible_id"


class PersonGroupListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PersonGroupSerializer

    def get_queryset(self):
        return groups_with_people()


class PersonGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PersonGroupSerializer
    queryset = groups_with_people()
    lookup_url_kwarg = "group_id"


class GroupPersonListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PersonSerializer

    def get_queryset(self):
        return people_with_groups().filter(groups__id=self.kwargs["group_id"])

    def perform_create(self, serializer):
        group = generics.get_object_or_404(PersonGroup, pk=self.kwargs["group_id"])
        person = serializer.save()
        group.people.add(person)


class PersonDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOrganizationReaderOrAdmin]
    serializer_class = PersonSerializer
    queryset = people_with_groups()
    lookup_url_kwarg = "person_id"
