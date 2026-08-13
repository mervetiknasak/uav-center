from .models import FormProcessRecord


def form_process_records_with_actors():
    return FormProcessRecord.objects.select_related("created_by", "updated_by")
