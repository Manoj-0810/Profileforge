"""Unit tests for LinkedIn entity reference resolution and degree parsing."""

from __future__ import annotations

import json
from pathlib import Path

from app.providers.linkedin.parser import LinkedInParser
from app.providers.linkedin.resolver import LinkedInResolver

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "raw_upstream"


def test_resolver_resolves_complete_graph():
    """Verify resolver constructs full profile metadata, image URL, and timeline entries."""
    fixture_path = FIXTURES_DIR / "voyager_complete.json"
    with open(fixture_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    parsed = LinkedInParser.parse(raw_data)
    resolved = LinkedInResolver.resolve(parsed)

    assert resolved.full_name == "Sarah Jenkins"
    assert "Staff Software Engineer" in (resolved.headline or "")
    assert "San Francisco" in (resolved.location or "")
    assert (
        resolved.profile_image_url
        == "https://media.licdn.com/dms/image/v2/sarah-jenkins-800.jpg"
    )
    assert resolved.followers_count == 4850

    # Experience
    assert len(resolved.experience) == 2
    assert resolved.experience[0].title == "Staff Software Engineer"
    assert resolved.experience[0].company == "Stripe"
    assert resolved.experience[0].start_date == "2021-04"
    assert resolved.experience[0].end_date is None

    # Education
    assert len(resolved.education) == 2
    assert resolved.education[0].school == "Stanford University"
    assert resolved.education[0].degree == "Master of Science"
    assert resolved.education[0].field_of_study == "Computer Science"

    # Skills & Languages
    assert "Distributed Systems" in resolved.skills
    assert "Python" in resolved.skills
    assert len(resolved.languages) == 2
    assert resolved.languages[0].name == "English"
    assert len(resolved.certifications) == 1
    assert resolved.certifications[0].issuing_organization == "Amazon Web Services"


def test_degree_pattern_regex_parsing():
    """Verify parse_degree correctly extracts standard degrees and fields of study."""
    deg, field = LinkedInResolver.parse_degree("B.S. in Computer Science")
    assert deg == "B.S."
    assert field == "Computer Science"

    deg2, field2 = LinkedInResolver.parse_degree(
        "Master of Science - Electrical Engineering"
    )
    assert deg2 == "Master of Science"
    assert field2 == "Electrical Engineering"

    deg3, field3 = LinkedInResolver.parse_degree("Ph.D. in Artificial Intelligence")
    assert deg3 == "Ph.D."
    assert field3 == "Artificial Intelligence"

    deg4, field4 = LinkedInResolver.parse_degree("MBA")
    assert deg4 == "MBA"
    assert field4 is None

    deg5, field5 = LinkedInResolver.parse_degree("Self Taught Programming")
    assert deg5 is None
    assert field5 == "Self Taught Programming"
