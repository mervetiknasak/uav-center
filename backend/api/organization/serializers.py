from django.db.models import Max
from rest_framework import serializers

from .models import PanelResponsible, Person, PersonGroup, Project, ProjectPanel
from .titles import (
    ORGANIZATION_TITLES,
    format_organization_titles,
    normalize_organization_titles,
    parse_organization_title,
)


class OrganizationMemberSerializer(serializers.ModelSerializer):
    titles = serializers.ListField(
        child=serializers.ChoiceField(
            choices=ORGANIZATION_TITLES,
            error_messages={"invalid_choice": "Geçersiz görev/ünvan seçimi: {input}."},
        ),
        required=False,
        write_only=True,
    )

    def validate_titles(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Aynı görev/ünvan birden fazla kez seçilemez.")
        return normalize_organization_titles(value)

    def validate_title(self, value):
        if not value:
            return ""
        titles = parse_organization_title(value)
        if not titles:
            choices = ", ".join(ORGANIZATION_TITLES)
            raise serializers.ValidationError(
                f"Görev/ünvan yalnızca şu seçeneklerden oluşabilir: {choices}."
            )
        return format_organization_titles(titles)

    def validate(self, attrs):
        titles = attrs.pop("titles", None)
        if titles is not None:
            attrs["title"] = format_organization_titles(titles)
        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["titles"] = parse_organization_title(instance.title)
        return representation


class PanelResponsibleSerializer(OrganizationMemberSerializer):
    class Meta:
        model = PanelResponsible
        fields = ["id", "panel", "name", "title", "titles", "email", "username", "order"]
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


class PersonSerializer(OrganizationMemberSerializer):
    groups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Person
        fields = [
            "id",
            "name",
            "title",
            "titles",
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
