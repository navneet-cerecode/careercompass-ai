"""Small, curated equivalence map for high-confidence skill aliases."""


_ALIAS_GROUPS = {
    "Artificial Intelligence (AI)": ("ai", "artificial intelligence"),
    "Basic Life Support (BLS)": ("bls", "basic life support"),
    "Cardiopulmonary Resuscitation (CPR)": ("cpr", "cardiopulmonary resuscitation"),
    "Customer Relationship Management (CRM)": (
        "crm",
        "customer relationship management",
    ),
    "Electronic Health Records (EHR)": ("ehr", "electronic health records"),
    "Electronic Medical Records (EMR)": ("emr", "electronic medical records"),
    "Enterprise Resource Planning (ERP)": ("erp", "enterprise resource planning"),
    "Human Resources (HR)": ("hr", "human resources"),
    "JavaScript": ("javascript", "js"),
    "Machine Learning (ML)": ("ml", "machine learning"),
    "Microsoft Excel": ("excel", "microsoft excel", "ms excel"),
    "Microsoft PowerPoint": ("powerpoint", "microsoft powerpoint", "ms powerpoint"),
    "Microsoft Word": ("microsoft word", "ms word"),
    "Natural Language Processing (NLP)": ("nlp", "natural language processing"),
    "Point of Sale (POS)": ("pos", "point of sale", "point-of-sale"),
    "Quality Assurance (QA)": ("qa", "quality assurance"),
    "Search Engine Optimization (SEO)": ("seo", "search engine optimization"),
    "Standard Operating Procedures (SOP)": (
        "sop",
        "sops",
        "standard operating procedure",
        "standard operating procedures",
    ),
    "Structured Query Language (SQL)": ("sql", "structured query language"),
    "User Experience (UX)": ("ux", "user experience"),
    "User Interface (UI)": ("ui", "user interface"),
}


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().split())


_ALIASES = {
    _normalize(alias): _normalize(display_name)
    for display_name, aliases in _ALIAS_GROUPS.items()
    for alias in (*aliases, display_name)
}


def canonical_skill_key(value: str) -> str:
    normalized = _normalize(value)
    return _ALIASES.get(normalized, normalized)
