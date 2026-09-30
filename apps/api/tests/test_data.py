"""Stage 0 data checks (docs/SPEC.md, section 3, "Этап 0").

Validates data/*.json against data/schemas/*.schema.json and checks the
cross-references described in the spec's stage-0 acceptance checks.
"""
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
SCHEMAS_DIR = DATA_DIR / "schemas"


def _load(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _load_schema(name):
    with open(SCHEMAS_DIR / name, encoding="utf-8") as f:
        return json.load(f)


QUESTIONS = _load("questions.json")
SERVICES = _load("services.json")
DOCUMENT_TYPES = _load("document_types.json")
PROVIDERS = _load("providers.json")
SOURCES = _load("sources.json")

QUESTIONS_BY_ID = {q["id"]: q for q in QUESTIONS}
SERVICE_IDS = {s["service_id"] for s in SERVICES}
DOC_TYPES = {d["doc_type"] for d in DOCUMENT_TYPES}
PROVIDER_IDS = {p["provider_id"] for p in PROVIDERS}
SOURCE_IDS = {s["source_id"] for s in SOURCES}

# Раздел 10.1: допустимые пути профиля, которые может заполнять вопрос.
# unknown_fields в список не входит: это поле вычисляется движком, а не
# отвечается напрямую вопросом.
VALID_PROFILE_FIELDS = {
    "child.age",
    "child.doctor_conclusion",
    "child.day_place",
    "family.region",
    "pmpk.status",
    "pmpk.recommendations",
    "pmpk.valid_until",
    "education.change_planned",
    "education.home_learning_need",
    "disability.status",
    "disability.review_date",
    "social.benefits",
    "support.current",
    "docs.present",
    "docs.birth_abroad",
    "red_flags",
    "concerns",
    "priority_focus",
}


# ---------------------------------------------------------------------------
# Схемы
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "data_file,schema_file",
    [
        ("questions.json", "questions.schema.json"),
        ("services.json", "services.schema.json"),
        ("document_types.json", "document_types.schema.json"),
        ("providers.json", "providers.schema.json"),
        ("sources.json", "sources.schema.json"),
    ],
)
def test_file_matches_schema(data_file, schema_file):
    data = _load(data_file)
    schema = _load_schema(schema_file)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    assert not errors, "\n".join(
        f"{data_file}: {'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors
    )


# ---------------------------------------------------------------------------
# show_if: ссылки на вопросы и коды вариантов
# ---------------------------------------------------------------------------

def _iter_leaf_conditions(node):
    if isinstance(node, str):
        return
    if "any" in node or "all" in node:
        for child in node.get("any", node.get("all", [])):
            yield from _iter_leaf_conditions(child)
        return
    yield node


def _referenced_codes(value):
    if isinstance(value, list):
        return value
    return [value]


@pytest.mark.parametrize("question", QUESTIONS, ids=lambda q: q["id"])
def test_show_if_references_are_valid(question):
    for leaf in _iter_leaf_conditions(question["show_if"]):
        ref_id = leaf["q"]
        assert ref_id in QUESTIONS_BY_ID, (
            f"{question['id']}.show_if ссылается на несуществующий вопрос {ref_id}"
        )
        if leaf["op"] in ("gte", "lt"):
            continue
        ref_question = QUESTIONS_BY_ID[ref_id]
        option_codes = {o["code"] for o in ref_question["options"]}
        for code in _referenced_codes(leaf["value"]):
            assert code in option_codes, (
                f"{question['id']}.show_if ссылается на несуществующий код "
                f"'{code}' у вопроса {ref_id}"
            )


# ---------------------------------------------------------------------------
# profile_field
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", QUESTIONS, ids=lambda q: q["id"])
def test_profile_field_is_known(question):
    assert question["profile_field"] in VALID_PROFILE_FIELDS, (
        f"{question['id']}.profile_field = '{question['profile_field']}' "
        "не описан в схеме профиля (раздел 10.1)"
    )


# ---------------------------------------------------------------------------
# Ссылки услуг на service_id / doc_type / provider_id / source_id
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("service", SERVICES, ids=lambda s: s["service_id"])
def test_service_predecessors_exist(service):
    for pred in service["predecessors_any"]:
        assert pred in SERVICE_IDS, (
            f"{service['service_id']}.predecessors_any ссылается на "
            f"несуществующую услугу {pred}"
        )


@pytest.mark.parametrize("service", SERVICES, ids=lambda s: s["service_id"])
def test_service_documents_exist(service):
    for kind, doc_types in service["documents"].items():
        for doc_type in doc_types:
            assert doc_type in DOC_TYPES, (
                f"{service['service_id']}.documents.{kind} ссылается на "
                f"несуществующий doc_type {doc_type}"
            )


@pytest.mark.parametrize("service", SERVICES, ids=lambda s: s["service_id"])
def test_service_providers_exist(service):
    for provider_id in service["provider_ids"]:
        assert provider_id in PROVIDER_IDS, (
            f"{service['service_id']}.provider_ids ссылается на "
            f"несуществующего поставщика {provider_id}"
        )


@pytest.mark.parametrize("service", SERVICES, ids=lambda s: s["service_id"])
def test_service_sources_exist(service):
    for source_id in service["source_ids"]:
        assert source_id in SOURCE_IDS, (
            f"{service['service_id']}.source_ids ссылается на "
            f"несуществующий источник {source_id}"
        )


@pytest.mark.parametrize("service", SERVICES, ids=lambda s: s["service_id"])
def test_service_has_source_or_unverified_sla(service):
    assert service["source_ids"] or service["sla_verified"] is False, (
        f"{service['service_id']}: нужен либо source_ids, либо sla_verified: false"
    )


# ---------------------------------------------------------------------------
# Обязательные вопросы
# ---------------------------------------------------------------------------

def test_exactly_six_mandatory_questions():
    mandatory = [q["id"] for q in QUESTIONS if q["mandatory"] is True]
    assert len(mandatory) == 6, f"Ожидалось 6 обязательных вопросов, получено: {mandatory}"
    assert set(mandatory) == {"Q01", "Q02", "Q03", "Q04", "Q14", "Q16"}
