from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=40, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ProjectPanel(models.Model):
    project = models.ForeignKey(Project, related_name="panels", on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="unique_panel_name_per_project"
            )
        ]

    def __str__(self):
        return f"{self.project.code} / {self.name}"


class PanelResponsible(models.Model):
    panel = models.ForeignKey(ProjectPanel, related_name="responsibles", on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    title = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=160, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=160)
    title = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PersonGroup(models.Model):
    name = models.CharField(max_length=160, unique=True)
    description = models.TextField(blank=True)
    people = models.ManyToManyField(Person, related_name="groups", blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name
