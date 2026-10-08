from __future__ import annotations

import json

from opsdevcode_specmint.mint.catalog import (
    CAPABILITIES,
    CATALOG_RECORDS_SCHEMA,
    ENSURE_MARKER_TYPE,
    TARGET_KINDS,
    capability_for,
    load_catalog_records,
    sorted_catalog_ids,
    target_kind,
)
from opsdevcode_specmint.mint.project import closed_catalog_document


def test_catalog_records_are_local_data() -> None:
    first = load_catalog_records()
    second = load_catalog_records()
    assert first == second
    assert first["schema"] == CATALOG_RECORDS_SCHEMA
    assert first["version"] == "v0"
    dumped = json.dumps(first)
    assert "/Users/" not in dumped
    assert "ghp_" not in dumped


def test_loaded_records_match_runtime_catalog() -> None:
    assert capability_for(ENSURE_MARKER_TYPE, "v1alpha1") is not None
    assert target_kind("local.sandbox") is not None
    assert target_kind("repo.github") is not None
    aws = target_kind("aws.account")
    assert aws is not None
    assert aws.fields == (("account", "string"), ("region", "string"))
    ids = sorted_catalog_ids()
    assert ids == tuple(sorted(ids))
    assert ENSURE_MARKER_TYPE + "@v1alpha1" in ids
    closed = closed_catalog_document()
    assert closed["ids"] == list(ids)
    assert len(CAPABILITIES) == len(first_capability_ids())
    assert {item.kind for item in TARGET_KINDS} == {
        "aws.account",
        "gcp.project",
        "k8s.workload",
        "local.dev",
        "local.sandbox",
        "repo.github",
        "sandbox",
    }


def first_capability_ids() -> set[str]:
    document = load_catalog_records()
    return {str(item["id"]) for item in document["capabilities"]}
