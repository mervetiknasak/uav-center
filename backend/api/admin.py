"""Django admin configuration for application-owned data.

Reference and business records are editable from the admin site.  Records owned
by background processing or audit flows remain view-only so an administrator
cannot silently bypass their lifecycle invariants.
"""

from django import forms
from django.contrib import admin
from django.db import transaction
from django.db.models import Count

from .documents.models import (
    AnalysisControl,
    Document,
    DocumentAnalysisRun,
    DocumentChunk,
)
from .edk.models import EDKApplication
from .form_processes.models import FormProcessRecord
from .jobs.models import AsyncJob
from .organization.models import (
    PanelResponsible,
    Person,
    PersonGroup,
    Project,
    ProjectPanel,
)
from .technical_documents.models import (
    CoverPage,
    TechnicalDocument,
    TechnicalDocumentNotification,
    TechnicalDocumentStatusHistory,
)

admin.site.site_header = "UAV Center Yönetimi"
admin.site.site_title = "UAV Center Admin"
admin.site.index_title = "Veri ve sistem yönetimi"


class ReadOnlyAdmin(admin.ModelAdmin):
    """Expose operational records without allowing lifecycle bypasses."""

    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ProjectPanelInline(admin.TabularInline):
    model = ProjectPanel
    fields = ("name", "description", "order")
    extra = 0
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "order", "updated_at")
    list_editable = ("is_active", "order")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "description")
    ordering = ("order", "name")
    readonly_fields = ("created_at", "updated_at")
    inlines = (ProjectPanelInline,)


class PanelResponsibleInline(admin.TabularInline):
    model = PanelResponsible
    fields = ("name", "title", "email", "username", "order")
    extra = 0
    show_change_link = True


@admin.register(ProjectPanel)
class ProjectPanelAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "responsible_count", "order")
    list_filter = ("project",)
    search_fields = ("name", "description", "project__name", "project__code")
    autocomplete_fields = ("project",)
    ordering = ("project__code", "order", "name")
    inlines = (PanelResponsibleInline,)

    @admin.display(description="Sorumlu sayısı", ordering="responsible_count")
    def responsible_count(self, obj):
        return obj.responsible_count

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("project")
            .annotate(responsible_count=Count("responsibles"))
        )


@admin.register(PanelResponsible)
class PanelResponsibleAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "panel", "email", "username", "order")
    list_filter = ("panel__project", "panel")
    search_fields = (
        "name",
        "title",
        "email",
        "username",
        "panel__name",
        "panel__project__code",
    )
    autocomplete_fields = ("panel",)
    ordering = ("panel__project__code", "panel__order", "order", "name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("panel", "panel__project")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "email", "username", "updated_at")
    search_fields = ("name", "title", "email", "username")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)


@admin.register(PersonGroup)
class PersonGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "member_count", "order", "updated_at")
    list_editable = ("order",)
    search_fields = ("name", "description", "people__name", "people__email")
    filter_horizontal = ("people",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("order", "name")

    @admin.display(description="Üye sayısı", ordering="member_count")
    def member_count(self, obj):
        return obj.member_count

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(member_count=Count("people"))


@admin.register(CoverPage)
class CoverPageAdmin(admin.ModelAdmin):
    list_display = ("number", "issue", "project", "updated_at")
    list_filter = ("project", "issue")
    search_fields = ("number", "issue", "project__name", "project__code")
    autocomplete_fields = ("project",)
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("project")


class TechnicalDocumentAdminForm(forms.ModelForm):
    status_note = forms.CharField(
        label="Durum değişikliği notu",
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Durum değiştiğinde geçmiş kaydına eklenir.",
    )

    class Meta:
        model = TechnicalDocument
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("project")
        cover_page = cleaned_data.get("cover_page")
        panels = cleaned_data.get("panels")
        if not project:
            return cleaned_data
        if cover_page and cover_page.project_id != project.id:
            self.add_error("cover_page", "Kapak sayfası seçili projeye ait olmalıdır.")
        if panels is not None and panels.exclude(project=project).exists():
            self.add_error("panels", "Tüm paneller seçili projeye ait olmalıdır.")
        return cleaned_data


class TechnicalDocumentStatusHistoryInline(admin.TabularInline):
    model = TechnicalDocumentStatusHistory
    fields = ("from_status", "to_status", "note", "changed_by", "created_at")
    readonly_fields = fields
    extra = 0
    can_delete = False
    ordering = ("-created_at",)
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TechnicalDocument)
class TechnicalDocumentAdmin(admin.ModelAdmin):
    form = TechnicalDocumentAdminForm
    list_display = (
        "code",
        "title",
        "project",
        "status",
        "priority",
        "classification",
        "due_date",
        "updated_at",
    )
    list_filter = (
        "status",
        "priority",
        "classification",
        "project",
        "category",
        "document_type",
    )
    search_fields = (
        "code",
        "title",
        "description",
        "owner_name",
        "project__name",
        "project__code",
        "cover_page__number",
    )
    autocomplete_fields = ("project", "cover_page", "created_by", "updated_by")
    filter_horizontal = ("panels",)
    readonly_fields = (
        "created_by",
        "updated_by",
        "last_notification_at",
        "last_notification_recipient_count",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "updated_at"
    save_on_top = True
    inlines = (TechnicalDocumentStatusHistoryInline,)
    fieldsets = (
        (
            "Doküman",
            {
                "fields": (
                    "project",
                    "cover_page",
                    "panels",
                    "code",
                    "title",
                    "description",
                    "category",
                    "document_type",
                    "revision",
                )
            },
        ),
        (
            "Durum ve planlama",
            {
                "fields": (
                    "status",
                    "status_note",
                    "priority",
                    "classification",
                    "owner_name",
                    "publication_date",
                    "due_date",
                    "review_date",
                )
            },
        ),
        ("Kaynak ve notlar", {"fields": ("source_url", "notes")}),
        (
            "Bildirim özeti",
            {
                "fields": ("last_notification_at", "last_notification_recipient_count"),
                "classes": ("collapse",),
            },
        ),
        (
            "Kayıt bilgisi",
            {
                "fields": ("created_by", "updated_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("project", "cover_page", "created_by", "updated_by")
        )

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = (
                TechnicalDocument.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
            )
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

        if not change or previous_status != obj.status:
            TechnicalDocumentStatusHistory.objects.create(
                document=obj,
                from_status=previous_status or "",
                to_status=obj.status,
                note=form.cleaned_data.get("status_note", "").strip()
                or ("Doküman kaydı oluşturuldu." if not change else ""),
                changed_by=request.user,
            )


@admin.register(AnalysisControl)
class AnalysisControlAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "severity", "is_active", "updated_at")
    list_editable = ("is_active",)
    list_filter = ("severity", "is_active")
    search_fields = ("name", "description", "instructions", "owner__username")
    autocomplete_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner")


@admin.register(Document)
class DocumentAdmin(ReadOnlyAdmin):
    list_display = (
        "original_name",
        "owner",
        "status",
        "size",
        "created_at",
        "processed_at",
    )
    list_filter = ("status", "content_type", "created_at")
    search_fields = ("original_name", "owner__username", "owner__email", "error_message")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner")


@admin.register(DocumentChunk)
class DocumentChunkAdmin(ReadOnlyAdmin):
    list_display = ("document", "position", "word_count", "char_start", "char_end")
    list_filter = ("created_at",)
    search_fields = ("document__original_name", "content", "content_hash")
    autocomplete_fields = ("document",)
    ordering = ("document_id", "position")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("document")


@admin.register(DocumentAnalysisRun)
class DocumentAnalysisRunAdmin(ReadOnlyAdmin):
    list_display = ("document", "created_by", "status", "created_at", "completed_at")
    list_filter = ("status", "created_at")
    search_fields = ("document__original_name", "created_by__username", "query")
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("document", "created_by")


@admin.register(AsyncJob)
class AsyncJobAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "job_type",
        "owner",
        "status",
        "progress",
        "attempts",
        "priority",
        "created_at",
    )
    list_filter = ("job_type", "status", "created_at")
    search_fields = ("id", "owner__username", "document__original_name", "locked_by")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner", "document")


@admin.register(TechnicalDocumentStatusHistory)
class TechnicalDocumentStatusHistoryAdmin(ReadOnlyAdmin):
    list_display = ("document", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("from_status", "to_status", "created_at")
    search_fields = ("document__code", "document__title", "note", "changed_by__username")
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("document", "changed_by")


@admin.register(TechnicalDocumentNotification)
class TechnicalDocumentNotificationAdmin(ReadOnlyAdmin):
    list_display = (
        "document",
        "subject",
        "recipient_count",
        "status",
        "sent_by",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("document__code", "document__title", "subject", "idempotency_key")
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("document", "sent_by")


@admin.register(FormProcessRecord)
class FormProcessRecordAdmin(ReadOnlyAdmin):
    list_display = (
        "record_number",
        "title",
        "process_code",
        "template_code",
        "status",
        "updated_by",
        "updated_at",
    )
    list_filter = ("process_code", "template_code", "status", "updated_at")
    search_fields = ("record_number", "title", "process_code", "template_code", "notes")
    date_hierarchy = "updated_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by", "updated_by")


@admin.register(EDKApplication)
class EDKApplicationAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "meeting_title",
        "applicant",
        "project_name",
        "requested_date",
        "status",
        "reviewed_by",
        "created_at",
    )
    list_filter = ("status", "requested_date", "created_at")
    search_fields = (
        "meeting_title",
        "project_name",
        "location",
        "applicant__username",
        "applicant__email",
    )
    date_hierarchy = "requested_date"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("applicant", "reviewed_by")
