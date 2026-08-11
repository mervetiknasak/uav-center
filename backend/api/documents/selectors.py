from .models import Document


def visible_documents(user):
    """Documents visible to an actor; unowned legacy rows are staff-only."""

    queryset = Document.objects.select_related("owner")
    if user.is_staff:
        return queryset
    return queryset.filter(owner=user)
