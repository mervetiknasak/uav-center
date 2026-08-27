from rest_framework import serializers

from .user_display import format_user_display_name


class UserDisplayNameField(serializers.Field):
    """Read-only serializer field for consistent actor attribution."""

    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        return format_user_display_name(value)
