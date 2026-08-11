from django.db.models import Max
from rest_framework import serializers

from .models import PanelResponsible, Person, PersonGroup, Project, ProjectPanel


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
            "id",
            "name",
            "title",
            "email",
            "username",
            "groups",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["groups", "created_at", "updated_at"]


class PersonGroupSerializer(serializers.ModelSerializer):
    people = PersonSerializer(many=True, read_only=True)

    class Meta:
        model = PersonGroup
        fields = [
            "id",
            "name",
            "description",
            "order",
            "people",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
