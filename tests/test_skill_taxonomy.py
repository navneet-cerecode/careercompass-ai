from services.skills.taxonomy import canonical_skill_key


def test_curated_aliases_cover_cross_industry_abbreviations():
    pairs = (
        ("MS Excel", "Microsoft Excel"),
        ("CRM", "Customer Relationship Management (CRM)"),
        ("CRM", "Customer Relationship Management"),
        ("SOPs", "Standard Operating Procedures"),
        ("EHR", "Electronic Health Records"),
        ("JS", "JavaScript"),
    )

    for left, right in pairs:
        assert canonical_skill_key(left) == canonical_skill_key(right)


def test_ambiguous_related_terms_remain_distinct():
    pairs = (
        ("Customer service", "Customer support"),
        ("Inventory management", "Inventory control"),
        ("Recruiting", "Talent acquisition"),
    )

    for left, right in pairs:
        assert canonical_skill_key(left) != canonical_skill_key(right)
