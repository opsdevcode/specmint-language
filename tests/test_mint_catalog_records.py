from __future__ import annotations

import json

from opsdevcode_specmint.mint.catalog import (
    CAPABILITIES,
    CATALOG_RECORDS_SCHEMA,
    ENSURE_MARKER_TYPE,
    INTEGRATIONS,
    TARGET_KINDS,
    capability_for,
    catalog_integration,
    github_catalog_integrations,
    load_catalog_records,
    search_catalog_integrations,
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


def test_catalog_records_include_packaged_reference() -> None:
    document = load_catalog_records()
    assert "integrations" in document
    found = catalog_integration(ENSURE_MARKER_TYPE, "0.1.0")
    assert found is not None
    assert found.origin == "packaged"
    assert found.execution_support == "fake"
    assert "execute" not in found.phases
    matches = search_catalog_integrations(query="sandbox", target_kind_filter="local.sandbox")
    assert found in matches
    github = catalog_integration("repo.github.plan", "0.1.0")
    assert github is not None
    assert github.origin == "github"
    assert github.execution_support == "fake"
    assert "execute" not in github.phases
    assert github.github is not None
    assert github.github.artifact_digest == (
        "sha256:3c864b4f5e7298a0a2f52d0680cb5c3eb8ea57a8195e7d9ba628fe3b7b6e60da"
    )
    assert github.github.manifest_digest == (
        "sha256:1b805a915d950c614c99089942252abbe6d846658afa741b28824330feba41f9"
    )
    github_matches = search_catalog_integrations(query="github", target_kind_filter="repo.github")
    assert github in github_matches
    assert {item.identity for item in INTEGRATIONS} == {
        ENSURE_MARKER_TYPE,
        "repo.github.plan",
    }


def test_github_catalog_coordinates_bind_recorded_release_digests() -> None:
    packaged = catalog_integration(ENSURE_MARKER_TYPE, "0.1.0", origin="packaged")
    github_local = catalog_integration(ENSURE_MARKER_TYPE, "0.1.0", origin="github")
    assert packaged is not None
    assert packaged.github is None
    assert github_local is not None
    assert github_local.github is not None
    assert github_local.github.artifact_digest == (
        "sha256:591e1b3ebdd7e4f9373996e0cdeafa62d8fea39d2640ded8270ff2e59c68094d"
    )
    assert github_local.github.manifest_digest == (
        "sha256:cde4adf9e5f4c9e0b127cd11e6e977d25857d4a72602702ffe8a57223b05100e"
    )
    assert github_local.github.tag == "v0.2.0-alpha.1"
    assert github_local.github.repository == "opsdevcode/mint-integration-local"
    assert "pypi.org" not in github_local.github.url
    assert github_local.github.tag != "latest"
    recorded = github_catalog_integrations()
    assert {item.identity for item in recorded} == {ENSURE_MARKER_TYPE, "repo.github.plan"}
    for item in recorded:
        assert item.origin == "github"
        assert item.github is not None
        assert item.github.artifact_digest.startswith("sha256:")
        assert "pypi.org" not in item.summary.lower() or "not PyPI" in item.summary


def first_capability_ids() -> set[str]:
    document = load_catalog_records()
    return {str(item["id"]) for item in document["capabilities"]}
