#════════════════════| INSTALLATION |══════════════════════════════
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from venv_manager import install_deps
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
packages = ["presidio-analyzer", "presidio-anonymizer"]
install_deps(packages)

#═════════════════════| IMPORTS |═════════════════════════════════
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import uuid

#════════════════| INITIALIZE PRESIDIO |══════════════════════════
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()
print("✅ Presidio Initialized Successfully")


sample_text = """
Hello Ahmed,
My email is ahmed@gmail.com
My phone number is +91 9876543210
My credit card is 4222 1111 1111 1111
Please contact me tomorrow.
Thank you
"""

# ============================================================
# BEAUTIFUL UI HELPER
# ============================================================

def print_section(title):

    print("\n")
    print("═" * 80)
    print(f"🔹 {title}")
    print("═" * 80)

# ============================================================
# STEP 1 : ORIGINAL INPUT
# ============================================================

print_section("ORIGINAL INPUT TEXT")

print(sample_text)

# ============================================================
# STEP 2 : DETECT PII ENTITIES
# ============================================================

results = analyzer.analyze(
    text=sample_text,
    language="en"
)

# ============================================================
# STEP 3 : REMOVE OVERLAPPING ENTITIES
# ============================================================

"""
Presidio may detect multiple overlapping entities.

Example:
- PHONE_NUMBER
- DATE_TIME
- UK_NHS

for the SAME text region.

We keep:
✅ Highest confidence entities only
"""

# Sort by:
# 1. Highest confidence
# 2. Longest entity

results = sorted(
    results,
    key=lambda x: (
        x.score,
        x.end - x.start
    ),
    reverse=True
)

filtered_results = []

occupied_spans = []

for entity in results:

    overlap = False

    for start, end in occupied_spans:

        if not (
            entity.end <= start
            or
            entity.start >= end
        ):
            overlap = True
            break

    if not overlap:

        filtered_results.append(entity)

        occupied_spans.append(
            (entity.start, entity.end)
        )

# Sort back by text order

filtered_results = sorted(
    filtered_results,
    key=lambda x: x.start
)

# ============================================================
# STEP 4 : DISPLAY DETECTED ENTITIES
# ============================================================

print_section("DETECTED PII ENTITIES")

for idx, entity in enumerate(filtered_results, start=1):

    detected_text = sample_text[
        entity.start:entity.end
    ]

    print(f"""
[{idx}]
Entity Type : {entity.entity_type}
Detected    : {detected_text}
Confidence  : {round(entity.score, 2)}
""")

# ============================================================
# STEP 5 : MASK PII
# ============================================================

"""
We replace sensitive data with:
<PII_xxxxxxxx>

Example:
Ahmed@gmail.com
↓
<PII_a12bc34d>
"""

masked_text = sample_text

pii_mapping = {}

# Reverse replacement prevents index shifting

for entity in reversed(filtered_results):

    original_value = sample_text[
        entity.start:entity.end
    ]

    # Generate unique placeholder

    placeholder = (
        f"<PII_{uuid.uuid4().hex[:8]}>"
    )

    # Store mapping

    pii_mapping[placeholder] = {
        "original": original_value,
        "entity_type": entity.entity_type
    }

    # Replace in text

    masked_text = (
        masked_text[:entity.start]
        + placeholder
        + masked_text[entity.end:]
    )

# ============================================================
# STEP 6 : SHOW MASKED OUTPUT
# ============================================================

print_section("MASKED OUTPUT")

print(masked_text)

# ============================================================
# STEP 7 : SHOW SECURE PII MAPPING
# ============================================================

print_section("PII PLACEHOLDER MAPPING")

for placeholder, info in pii_mapping.items():

    print(f"""
{placeholder}

    Entity Type : {info['entity_type']}
    Original    : {info['original']}
""")

# ============================================================
# STEP 8 : UNMASK / RESTORE ORIGINAL VALUES
# ============================================================

restored_text = masked_text

for placeholder, info in pii_mapping.items():

    restored_text = restored_text.replace(
        placeholder,
        info["original"]
    )

# ============================================================
# STEP 9 : SHOW RESTORED OUTPUT
# ============================================================

print_section("RESTORED / UNMASKED OUTPUT")

print(restored_text)

# ============================================================
# STEP 10 : VALIDATION CHECK
# ============================================================

print_section("VALIDATION CHECK")

if restored_text == sample_text:

    print("✅ SUCCESS")
    print("Original text restored perfectly")

else:

    print("❌ FAILED")
    print("Restoration mismatch detected")

# ============================================================
# REAL-WORLD GENAI SECURITY FLOW
# ============================================================

print_section("REAL-WORLD GENAI SECURITY FLOW")

flow = """
USER INPUT
      ↓
PII DETECTION
      ↓
REMOVE OVERLAPPING ENTITIES
      ↓
MASK SENSITIVE DATA
      ↓
SEND SAFE TEXT TO LLM
      ↓
LLM GENERATES RESPONSE
      ↓
RESTORE ORIGINAL PII
      ↓
FINAL SAFE RESPONSE
"""

print(flow)

# ============================================================
# WHY THIS MATTERS IN GENAI
# ============================================================

print_section("WHY PII PROTECTION IS IMPORTANT")

importance = [
    "Protect User Privacy",
    "Prevent Data Leakage",
    "Secure RAG Pipelines",
    "Protect Enterprise Data",
    "GDPR Compliance",
    "HIPAA Compliance",
    "Financial Data Protection",
    "Safe AI Agents",
    "Secure Customer Support AI",
    "Enterprise AI Governance"
]

for idx, item in enumerate(importance, start=1):

    print(f"{idx}. {item}")

# ============================================================
# PII TYPES SUPPORTED BY PRESIDIO
# ============================================================

print_section("SUPPORTED PII TYPES")

supported_entities = [
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "PERSON",
    "LOCATION",
    "DATE_TIME",
    "IP_ADDRESS",
    "URL",
    "US_SSN",
    "IBAN_CODE",
    "PASSPORT",
    "DRIVER_LICENSE",
    "MEDICAL_LICENSE",
    "CRYPTO"
]

for idx, entity in enumerate(supported_entities, start=1):

    print(f"{idx}. {entity}")

# ============================================================
# PRODUCTION BEST PRACTICES
# ============================================================

print_section("PRODUCTION BEST PRACTICES")

best_practices = [
    "Use UUID-based placeholders",
    "Encrypt PII mappings",
    "Store mappings temporarily",
    "Use secure databases",
    "Add audit logging",
    "Enable access control",
    "Expire mappings automatically",
    "Mask data before vector storage",
    "Never send raw PII to LLMs",
    "Use enterprise guardrails"
]

for idx, item in enumerate(best_practices, start=1):

    print(f"{idx}. {item}")

# ============================================================
# FINAL SUCCESS MESSAGE
# ============================================================

print_section("PIPELINE COMPLETED SUCCESSFULLY")

print("✅ PII Detection Completed")
print("✅ Overlap Resolution Completed")
print("✅ Secure Masking Completed")
print("✅ UUID Mapping Generated")
print("✅ PII Restoration Completed")
print("✅ Enterprise Workflow Demonstrated")

# ============================================================
# END
# ============================================================