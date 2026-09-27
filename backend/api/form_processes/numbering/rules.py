"""Catalog-based target validation, context resolution and persistent field locks."""

import json

from rest_framework.exceptions import ValidationError

from ..catalog import FormTemplateValidationError, get_form_template


def field_catalog(template_code):
    try:
        template = get_form_template(template_code)
    except FormTemplateValidationError as exc:
        raise ValidationError(exc.errors) from exc
    fields = {"record_number": ("text", 128), "title": ("text", 300)}
    fields.update(
        {f"data.{field.key}": (field.field_type, field.max_length) for field in template.fields}
    )
    return fields


def field_value(form, path):
    return (
        form.get("data", {}).get(path[5:], "") if path.startswith("data.") else form.get(path, "")
    )


def set_field(form, path, value):
    if path.startswith("data."):
        form.setdefault("data", {})[path[5:]] = value
    else:
        form[path] = value


def validate_mapping(template_code, target, sources, format_contract):
    fields = field_catalog(template_code)
    if target not in fields or target == "title" or fields[target][0] not in {"text", "textarea"}:
        raise ValidationError(
            {"target_field": "Numara hedefi kayıt numarası veya bir metin alanı olmalıdır."}
        )
    context = format_contract.get("required_context", [])
    if not isinstance(sources, dict) or set(sources) != {item["key"] for item in context}:
        raise ValidationError(
            {"context_sources": "Formatın tüm context alanları için kaynak seçin."}
        )
    for item in context:
        source = sources[item["key"]]
        if not isinstance(source, dict):
            raise ValidationError({"context_sources": "Geçersiz context kaynağı."})
        kind = source.get("source")
        if kind == "field":
            path = source.get("field")
            if (
                not isinstance(path, str)
                or path not in fields
                or fields[path][0] in {"table", "multi_select"}
                or path == target
            ):
                raise ValidationError(
                    {"context_sources": "Geçersiz veya kendine bağlı kaynak alanı."}
                )
        elif kind == "fixed":
            validate_context_value(source.get("value"), item)
        elif kind == "default":
            if item["required"]:
                raise ValidationError(
                    {"context_sources": "Zorunlu context için varsayılan kullanılamaz."}
                )
        elif kind != "manual":
            raise ValidationError({"context_sources": "Geçersiz kaynak türü."})


def validate_context_value(value, contract):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError({"manual_context": {contract["key"]: "Context değeri zorunludur."}})
    if len(value) > contract["max_length"]:
        raise ValidationError(
            {
                "manual_context": {
                    contract["key"]: f"En fazla {contract['max_length']} karakter girilebilir."
                }
            }
        )
    return value


def resolve_context(mapping, form, manual):
    context, locked = {}, {}
    sources = mapping.context_sources
    manual_keys = {key for key, source in sources.items() if source["source"] == "manual"}
    if not isinstance(manual, dict) or set(manual) - manual_keys:
        raise ValidationError({"manual_context": "Bilinmeyen context girdisi."})
    for contract in mapping.format_snapshot.get("required_context", []):
        key = contract["key"]
        source = sources[key]
        kind = source["source"]
        if kind == "default":
            continue
        if kind == "field":
            value = field_value(form, source["field"])
            locked[source["field"]] = value
        elif kind == "fixed":
            value = source["value"]
        else:
            value = manual.get(key)
        context[key] = validate_context_value(value, contract)
    if len(json.dumps(context, ensure_ascii=False).encode()) > 8192:
        raise ValidationError({"manual_context": "Context verisi 8 KiB sınırını aşıyor."})
    return context, locked


def validate_no_cycles(mappings):
    graph = {
        mapping.target_field: [
            source["field"]
            for source in mapping.context_sources.values()
            if source["source"] == "field"
        ]
        for mapping in mappings
        if mapping.enabled
    }
    visited, visiting = set(), set()

    def visit(node):
        if node in visiting:
            raise ValidationError(
                {"context_sources": "Alan eşleştirmeleri döngüsel bağımlılık içeriyor."}
            )
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def locked_values(record):
    values = {}
    for allocation in record.number_allocations.all():
        if allocation.status == "completed":
            values.update(allocation.locked_values)
    return values


def enforce_locks(record, attrs):
    current = {"record_number": record.record_number, "title": record.title, "data": record.data}
    candidate = {**current, **attrs}
    errors = {}
    for path, value in locked_values(record).items():
        if field_value(candidate, path) != value:
            errors[path] = "Bu alan numara üretiminde kullanıldığı için değiştirilemez."
    if errors:
        raise ValidationError(errors)
