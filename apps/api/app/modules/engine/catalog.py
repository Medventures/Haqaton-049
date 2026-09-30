"""Загрузка справочников data/*.json в память с валидацией по JSON Schema.

Раздел 14 SPEC.md: "Справочники из data/ в БД не копируются: API загружает
их в память при старте."
"""
import json
from functools import lru_cache

from jsonschema import Draft7Validator

from app.paths import DATA_DIR, SCHEMAS_DIR

_FILES = {
    "questions": ("questions.json", "questions.schema.json"),
    "services": ("services.json", "services.schema.json"),
    "document_types": ("document_types.json", "document_types.schema.json"),
    "providers": ("providers.json", "providers.schema.json"),
    "sources": ("sources.json", "sources.schema.json"),
}


def _load_and_validate(data_file, schema_file):
    with open(DATA_DIR / data_file, encoding="utf-8") as f:
        data = json.load(f)
    with open(SCHEMAS_DIR / schema_file, encoding="utf-8") as f:
        schema = json.load(f)
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        messages = "; ".join(e.message for e in errors[:5])
        raise ValueError(f"{data_file} не проходит {schema_file}: {messages}")
    return data


class Catalog:
    """Справочники в памяти, ключ — идентификатор записи."""

    def __init__(self):
        questions = _load_and_validate(*_FILES["questions"])
        services = _load_and_validate(*_FILES["services"])
        document_types = _load_and_validate(*_FILES["document_types"])
        providers = _load_and_validate(*_FILES["providers"])
        sources = _load_and_validate(*_FILES["sources"])

        self.questions = {q["id"]: q for q in questions}
        self.services = {s["service_id"]: s for s in services}
        self.document_types = {d["doc_type"]: d for d in document_types}
        self.providers = {p["provider_id"]: p for p in providers}
        self.sources = {s["source_id"]: s for s in sources}

        self.questions_list = questions
        self.services_list = services


@lru_cache(maxsize=1)
def get_catalog() -> Catalog:
    return Catalog()
