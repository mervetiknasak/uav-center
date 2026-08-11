from .models import Person, PersonGroup, Project, ProjectPanel


def projects_with_structure():
    return Project.objects.prefetch_related("panels__responsibles")


def panels_with_responsibles():
    return ProjectPanel.objects.prefetch_related("responsibles")


def groups_with_people():
    return PersonGroup.objects.prefetch_related("people__groups")


def people_with_groups():
    return Person.objects.prefetch_related("groups")
