"""Tests for generated Pydantic models."""

import pytest
from pydantic import ValidationError

from rsm_schema.generated import Contributor, RSMMetadata


def test_only_project_slug_is_required() -> None:
    """A minimal document should validate and fill declared defaults."""
    metadata = RSMMetadata.model_validate({"project_slug": "demo"})

    assert metadata.project_slug == "demo"
    assert metadata.keywords.entries == []
    assert metadata.topics.entries == []
    assert metadata.contributors.entries == []
    assert metadata.project_name is None


def test_topics_are_project_level_edam_terms() -> None:
    """Research topics belong to the project rather than individual functions."""
    metadata = RSMMetadata.model_validate(
        {
            "project_slug": "demo",
            "topics": {
                "entries": [
                    {
                        "term": "Data analysis",
                        "uri": "https://edamontology.org/topic_3474",
                    }
                ]
            },
            "software_functions": {"entries": [{"operations": [{"term": "Data analysis"}]}]},
        }
    )

    assert metadata.topics.entries[0].term == "Data analysis"
    assert not hasattr(metadata.software_functions.entries[0], "topics")


def test_contributor_carries_roles_and_affiliations() -> None:
    """One entry per person, with every role and affiliation on that entry."""
    metadata = RSMMetadata.model_validate(
        {
            "project_slug": "demo",
            "development_status": "wip",
            "contributors": {
                "entries": [
                    {
                        "name": "Ada Lovelace",
                        "email": "ada@example.org",
                        "orcid": "https://orcid.org/0000-0002-1825-0097",
                        "roles": ["Original author", "Maintainer"],
                        "affiliations": [
                            {"name": "Leiden University Medical Center"},
                            {"name": "Leiden University"},
                        ],
                    }
                ]
            },
        }
    )

    contributor = metadata.contributors.entries[0]
    assert isinstance(contributor, Contributor)
    # Authoring and maintaining the software is one person, listed once.
    assert [role.value for role in contributor.roles] == ["Original author", "Maintainer"]
    assert contributor.affiliations is not None
    assert [org.name for org in contributor.affiliations] == [
        "Leiden University Medical Center",
        "Leiden University",
    ]
    assert metadata.development_status == "wip"


def test_contributor_must_declare_a_role() -> None:
    """`roles` is what the separate author/maintainer lists used to encode."""
    with pytest.raises(ValidationError):
        RSMMetadata.model_validate(
            {"project_slug": "demo", "contributors": {"entries": [{"name": "Ada"}]}}
        )

    with pytest.raises(ValidationError):
        RSMMetadata.model_validate(
            {
                "project_slug": "demo",
                "contributors": {"entries": [{"name": "Ada", "roles": []}]},
            }
        )


def test_unknown_properties_are_rejected() -> None:
    """The schema sets ``additionalProperties: false``, so extras must fail."""
    with pytest.raises(ValidationError):
        RSMMetadata.model_validate({"project_slug": "demo", "not_a_field": 1})


def test_enum_values_are_constrained() -> None:
    """Enumerated fields should reject values outside the schema's enum."""
    with pytest.raises(ValidationError):
        RSMMetadata.model_validate({"project_slug": "demo", "development_status": "flourishing"})


def test_required_property_is_enforced() -> None:
    """``project_slug`` is the one required root property."""
    with pytest.raises(ValidationError):
        RSMMetadata.model_validate({"project_name": "Demo"})


def test_access_code_review_and_funder_details() -> None:
    """New public fields should be available through generated models."""
    metadata = RSMMetadata.model_validate(
        {
            "project_slug": "demo",
            "access": {
                "type": "free-with-restrictions",
                "details": "Free for academic use; see https://example.org/access.",
            },
            "code_review_policy": "Two approvals are required before merge.",
            "funding": {
                "entries": [
                    {
                        "funder": "Example Foundation",
                        "funder_identifier": "https://ror.org/012345678",
                        "funder_identifier_type": "ror",
                        "funder_url": "https://example.org/foundation",
                        "award_number": "ABC-123",
                    }
                ]
            },
        }
    )

    assert metadata.access.type == "free-with-restrictions"
    assert metadata.code_review_policy == "Two approvals are required before merge."
    assert metadata.funding.entries[0].funder_identifier_type == "ror"
