from .models import AsyncJob


def jobs_for_user(user):
    return AsyncJob.objects.filter(owner=user).select_related("document")
