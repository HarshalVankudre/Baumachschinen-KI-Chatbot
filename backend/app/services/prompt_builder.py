"""
Dynamic Prompt Builder Service

Builds adaptive, context-aware prompts using Jinja2 templates.
Replaces 6000+ character static prompts with dynamic 1200-character prompts.

This service:
- Reduces token usage by 80% (6000 → ~1200 chars)
- Adapts prompts based on query intent and complexity
- Supports 7 intent-specific roles
- Provides data-aware instructions
- Adjusts style based on query complexity
- Maintains German formal "Sie" form throughout

Intent-Specific Roles:
1. search - Technical documentation lookup
2. recommendation - Machine selection advisor
3. comparison - Objective specification comparison
4. relationship - Component and part analysis
5. specification - Precise technical data retrieval
6. conversation - Friendly, natural dialogue
7. hierarchy - Category and model navigation

Template System:
- BASE_ROLE: Core expert identity
- INTENT_ROLES: Intent-specific instructions
- DATA_INSTRUCTIONS_TEMPLATE: Context availability handling
- STYLE_TEMPLATE: Complexity and answer type formatting

Token Savings: 6000+ chars → ~1200 chars (80% reduction)
"""

from jinja2 import Template
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Build dynamic, context-aware prompts (replaces 6000-char hardcoded prompts)

    Uses Jinja2 templates for flexibility and maintainability.

    **Key Features:**
    - 80% token reduction (6000+ chars → ~1200 chars)
    - Adaptive prompts based on query intent, complexity, and data availability
    - Support for 7 intent types: search, recommendation, comparison, relationship,
      specification, conversation, hierarchy
    - Dynamic style adjustments (simple/moderate/complex)
    - Data-aware instructions (with/without retrieved data)
    - German language throughout

    **Example Usage:**

    ```python
    from app.services.prompt_builder import get_prompt_builder

    builder = get_prompt_builder()

    # Build system prompt
    system_prompt = builder.build_system_prompt(
        intent='recommendation',
        has_data=True,
        doc_count=5,
        machine_count=10,
        kg_results=15,
        query_complexity='complex',
        answer_type='recommendation',
        should_cite=True
    )

    # Build user message
    user_message = builder.build_user_message(
        query='Welche Baumaschinen eignen sich für Straßenbau?',
        context='Retrieved data: [machines, docs, kg_results]',
        examples=[{'question': '...', 'answer': '...'}]
    )
    ```
    """

    # Base role (always included)
    BASE_ROLE = "Sie sind ein hochspezialisierter Experte für Baumaschinen und technische Dokumentation."

    # Intent-specific roles
    INTENT_ROLES = {
        "search": """Sie durchsuchen technische Dokumentation und liefern präzise Informationen aus Handbüchern und Anleitungen.""",

        "recommendation": """Sie sind ein Berater, der die perfekte Baumaschine für spezifische Aufgaben empfiehlt.
Analysieren Sie:
- Die Aufgabenanforderungen (Gelände, Umfang, Bedingungen)
- Verfügbare Maschinenkapazitäten
- Effizienz und Eignung

Geben Sie Top 3 Empfehlungen mit klarer Begründung.""",

        "comparison": """Sie vergleichen Baumaschinen objektiv anhand von:
- Technischen Spezifikationen
- Leistungsdaten
- Einsatzgebieten
- Vor- und Nachteilen

Präsentieren Sie Ergebnisse strukturiert (idealerweise als Tabelle).""",

        "relationship": """Sie analysieren Beziehungen zwischen Maschinen:
- Gemeinsame Komponenten (Motor, Hydraulik)
- Teil-Kompatibilität
- Hersteller-Familien

Erklären Sie die Zusammenhänge klar.""",

        "specification": """Sie liefern präzise technische Spezifikationen:
- Direkt aus Datenbank abrufen
- Exakte Werte mit Einheiten
- Klar und natürlich formulieren""",

        "conversation": """Sie führen freundliche, natürliche Gespräche auf Deutsch.
Seien Sie hilfsbereit, zugänglich und professionell.""",

        "hierarchy": """Sie analysieren hierarchische Beziehungen zwischen Maschinen:
- Kategorien und Unterkategorien
- Maschinentypen und Modelle
- Hersteller und ihre Produktlinien

Erklären Sie die Struktur verständlich."""
    }

    # Data availability instructions
    DATA_INSTRUCTIONS_TEMPLATE = Template("""
{% if has_data %}
=== VERFÜGBARE DATEN ===
{% if doc_count > 0 %}
📄 Dokumentation: {{ doc_count }} relevante Abschnitte gefunden
{% endif %}
{% if machine_count > 0 %}
🏗️ Maschinen: {{ machine_count }} passende Maschinen gefunden{% if total_machines > machine_count %} (aus insgesamt {{ total_machines }} Maschinen in der Datenbank){% endif %}
{% endif %}
{% if kg_results %}
🔗 Wissensgraph: {{ kg_results }} strukturierte Ergebnisse
{% endif %}

**WICHTIG:**
- Nutzen Sie AUSSCHLIESSLICH die bereitgestellten Daten
- Erfinden Sie KEINE Informationen
- Bei fehlenden Details: Sagen Sie klar "Diese Information liegt mir nicht vor"
- Geben Sie natürliche Antworten OHNE Quellenangaben (außer der Benutzer fragt explizit danach)
{% if total_machines > 0 and machine_count < total_machines %}
- WICHTIG FÜR ZÄHL-FRAGEN: Die Datenbank enthält insgesamt {{ total_machines }} Maschinen. Wenn nach der Gesamtzahl gefragt wird, verwenden Sie diese Zahl.
{% endif %}

{% else %}
=== KEINE RELEVANTEN DATEN GEFUNDEN ===
Es wurden keine passenden Informationen in den Datenbanken gefunden.

Antworten Sie:
"Dazu habe ich leider keine spezifischen Informationen in unserer Datenbank. {{ suggestion }}"

{% if can_use_general_knowledge %}
Falls angemessen, bieten Sie an mit allgemeinem Wissen zu antworten.
{% endif %}
{% endif %}
""")

    # Style instructions based on complexity
    STYLE_TEMPLATE = Template("""
=== ANTWORT-STIL ===
{% if complexity == 'simple' %}
- Antworten Sie kurz und direkt (2-4 Sätze)
- Kommen Sie schnell zum Punkt
- Keine unnötige Struktur
{% elif complexity == 'moderate' %}
- Ausgewogene Antwort (1-2 Absätze)
- Klare Struktur wenn hilfreich
- Wichtigste Punkte zuerst
{% elif complexity == 'complex' %}
- Detaillierte, strukturierte Antwort
- Nutzen Sie Überschriften und Listen
- Alle relevanten Details einbeziehen
- Logischer Aufbau
{% endif %}

{% if answer_type == 'factoid' %}
Direkte Antwort auf die Frage, präzise.
{% elif answer_type == 'explanation' %}
Erklären Sie das Konzept verständlich mit Beispielen.
{% elif answer_type == 'list' %}
Nutzen Sie Bullet Points (•) oder Nummerierung.
{% elif answer_type == 'comparison' %}
Erstellen Sie eine vergleichende Übersicht (Tabelle wenn möglich).
{% elif answer_type == 'recommendation' %}
Listen Sie Empfehlungen mit Begründung:
1. Empfehlung: [Maschine] - Begründung: [Warum]
{% endif %}

**SPRACHE:**
- Formelles Sie (nicht du)
- Professionell aber zugänglich
- Klare, verständliche Formulierungen
- Keine Roboter-Sprache
""")

    def build_system_prompt(
        self,
        intent: str,
        has_data: bool = True,
        doc_count: int = 0,
        machine_count: int = 0,
        kg_results: int = 0,
        total_machines: int = 0,
        query_complexity: str = "moderate",
        answer_type: str = "explanation",
        should_cite: bool = False,
        can_use_general_knowledge: bool = False
    ) -> str:
        """
        Build dynamic system prompt based on context

        Args:
            intent: Query intent (search, recommendation, comparison, etc.)
            has_data: Whether relevant data was found
            doc_count: Number of document chunks retrieved
            machine_count: Number of machines found (top-k results shown)
            kg_results: Number of knowledge graph results
            total_machines: Total number of machines in the entire database
            query_complexity: simple, moderate, complex
            answer_type: factoid, explanation, list, comparison, recommendation
            should_cite: Whether to include source citations
            can_use_general_knowledge: Allow general knowledge if no data found

        Returns:
            Complete system prompt (much shorter than 6000 chars!)
        """

        parts = []

        # 1. Base role
        parts.append(self.BASE_ROLE)

        # 2. Intent-specific role
        if intent in self.INTENT_ROLES:
            parts.append(self.INTENT_ROLES[intent])

        # 3. Data availability instructions
        suggestion = "Möchten Sie, dass ich allgemein antworte?" if can_use_general_knowledge else "Bitte formulieren Sie die Frage anders oder fragen Sie nach etwas Spezifischerem."

        data_instructions = self.DATA_INSTRUCTIONS_TEMPLATE.render(
            has_data=has_data,
            doc_count=doc_count,
            machine_count=machine_count,
            total_machines=total_machines,
            kg_results=kg_results,
            should_cite=should_cite,
            suggestion=suggestion,
            can_use_general_knowledge=can_use_general_knowledge
        )
        parts.append(data_instructions)

        # 4. Style instructions
        style_instructions = self.STYLE_TEMPLATE.render(
            complexity=query_complexity,
            answer_type=answer_type
        )
        parts.append(style_instructions)

        # Combine all parts
        full_prompt = "\n\n".join(parts)

        # Log token savings
        logger.info(f"Dynamic prompt built: ~{len(full_prompt)} chars (vs 6000+ static)")

        return full_prompt

    def build_user_message(
        self,
        query: str,
        context: str = "",
        examples: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Build user message with context and optional examples

        Args:
            query: User's original query
            context: Retrieved context (documents, machinery data, KG results)
            examples: Few-shot examples (optional)

        Returns:
            Formatted user message
        """

        parts = []

        # Add few-shot examples if provided
        if examples and len(examples) > 0:
            parts.append("=== BEISPIELE ===")
            for i, example in enumerate(examples, 1):
                parts.append(f"\nBeispiel {i}:")
                parts.append(f"Frage: {example['question']}")
                parts.append(f"Antwort: {example['answer']}")
            parts.append("")

        # Add retrieved context if available
        if context:
            parts.append("=== KONTEXT ===")
            parts.append(context)
            parts.append("")

        # Add user's query
        parts.append("=== BENUTZERANFRAGE ===")
        parts.append(query)

        return "\n".join(parts)


# Factory function (thread-safe)
from functools import lru_cache


@lru_cache()
def get_prompt_builder():
    """
    Get PromptBuilder instance

    Returns:
        Singleton PromptBuilder instance (thread-safe)
    """
    return PromptBuilder()
