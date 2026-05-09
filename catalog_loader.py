import json
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CATALOG_FILE = DATA_DIR / "shl_catalog.json"

FALLBACK_CATALOG = [
    {
        "name": "Java 8 (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/java-8-new/",
        "test_type": "K",
        "description": "Measures Java 8 programming knowledge, object-oriented programming, collections and core language skills.",
        "duration": "",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "keywords": ["java", "developer", "backend", "programming", "coding"]
    },
    {
        "name": "JavaScript (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/javascript-new/",
        "test_type": "K",
        "description": "Measures JavaScript programming knowledge for web development roles.",
        "duration": "",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "keywords": ["javascript", "frontend", "developer", "web"]
    },
    {
        "name": "Python (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/python-new/",
        "test_type": "K",
        "description": "Measures Python programming and problem-solving knowledge.",
        "duration": "",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "keywords": ["python", "developer", "data", "automation", "programming"]
    },
    {
        "name": "SQL (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/sql-new/",
        "test_type": "K",
        "description": "Measures SQL querying, joins, filtering and database concepts.",
        "duration": "",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "keywords": ["sql", "database", "data analyst", "data engineer"]
    },
    {
        "name": "Verify G+ Ability Test",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-g-ability-test/",
        "test_type": "A",
        "description": "General cognitive ability assessment covering reasoning skills useful across professional roles.",
        "duration": "",
        "remote_testing": "Yes",
        "adaptive_irt": "Yes",
        "keywords": ["cognitive", "reasoning", "ability", "general ability", "graduate"]
    },
    {
        "name": "OPQ32r",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/opq32r/",
        "test_type": "P",
        "description": "Occupational personality questionnaire used to understand workplace preferences and behavioural style.",
        "duration": "",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "keywords": ["personality", "behaviour", "stakeholder", "team", "leadership"]
    },
    {
        "name": "Motivation Questionnaire MQM5",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/motivation-questionnaire-mqm5/",
        "test_type": "P",
        "description": "Assesses motivational drivers and work preferences.",
        "duration": "",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "keywords": ["motivation", "personality", "culture", "fit"]
    }
]


def load_catalog() -> List[Dict[str, Any]]:
    if CATALOG_FILE.exists():
        with CATALOG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list) and data:
            return data
    return FALLBACK_CATALOG
