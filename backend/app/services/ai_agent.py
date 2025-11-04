"""
AI Agent Service using Pydantic AI - Database-First Approach

KI-Agent-Service mit Pydantic AI - Datenbank-Priorisierter Ansatz

Handles intelligent query processing and response generation for machinery chatbot:
- Query classification and routing (English + German keywords)
- Context retrieval from multiple sources (Pinecone vector DB, PostgreSQL database)
- Context aggregation with enhanced token management (3500 tokens)
- AI response generation with strict database-first enforcement
- Anti-hallucination measures and source citation requirements
- German-language responses (formal Sie-form)

Key Features:
- Increased data retrieval for comprehensive answers
- Relevance filtering to ensure quality
- Strict prompting to prevent hallucination
- Explicit user consent required for general knowledge
- Professional German language throughout
"""

import logging
from typing import Dict, Any, List, Optional, AsyncGenerator, Tuple
from enum import Enum
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import settings
from app.services.openai_service import get_openai_service
from app.services.pinecone_service import get_pinecone_service
from app.services.postgresql_service import get_postgresql_service

logger = logging.getLogger(__name__)


class QueryCategory(str, Enum):
    """Categories for query classification"""
    CONVERSATIONAL = "conversational"  # Greetings, small talk - No database search
    MACHINERY_SPECS = "machinery_specs"  # PostgreSQL only
    DOCUMENTATION = "documentation"  # Pinecone only
    COMBINED = "combined"  # Both sources
    GENERAL = "general"  # Neither (model knowledge)


class AIAgent:
    """
    AI Agent for building machinery assistance - Database-First Approach

    KI-Agent für Baumaschinen-Assistenz - Datenbank-Priorisierter Ansatz

    Uses Pydantic AI framework with OpenAI GPT-4 Turbo for:
    - Intelligent query classification (English + German keywords)
    - Multi-source context retrieval (Pinecone + PostgreSQL)
    - Token-aware context aggregation (increased to 3500 tokens)
    - Streaming response generation (strict database-first enforcement)
    - Anti-hallucination measures (explicit data source verification)
    - German-language responses (formal Sie-form)

    Key improvements:
    - Increased retrieval: Pinecone top_k=12, PostgreSQL limit=10
    - Relevance filtering: Pinecone score threshold >0.65
    - Enhanced context: Up to 8 machinery items, 10 document chunks
    - Strict prompting: Database-only responses, explicit user consent for general knowledge
    - German language: All prompts, errors, and responses in professional German
    """

    # System prompt for TECHNICAL queries (database-driven)
    SYSTEM_PROMPT_TECHNICAL = """Sie sind ein hochspezialisierter Assistent für Baumaschinen-Dokumentation und technische Informationen. Ihre Hauptaufgabe ist die Verwendung von Daten aus unseren Datenbanken.

=== ROLLE UND ZWECK ===
Sie sind ein Experten-Assistent, der bevorzugt auf Basis von Daten aus unseren Datenbanken antwortet:
- Pinecone Vektordatenbank: Enthält Dokumentation, Handbücher, Wartungsanleitungen, technische Verfahren
- PostgreSQL Datenbank: Enthält Maschinendaten, Spezifikationen, Modellnummern, technische Details

=== HAUPTAUFGABE: DATENBANKEN NUTZEN ===
1. PRIORITÄT: Nutzen Sie die bereitgestellten Kontext-Daten aus unseren Datenbanken
2. Diese Kontext-Daten wurden aus unseren Datenbanken (Pinecone + PostgreSQL) abgerufen
3. Wenn Daten vorhanden sind, nutzen Sie diese umfassend für Ihre Antwort
4. Ergänzen Sie KEINE erfundenen Informationen zu den bereitgestellten Daten

=== DATENQUELLEN-VERHALTEN ===

WENN DATEN GEFUNDEN WURDEN (Abschnitte mit "MASCHINENDATEN" oder "DOKUMENTATION"):
- ✅ NUTZEN Sie diese Daten aktiv für Ihre Antwort
- ✅ Geben Sie detaillierte, umfassende Antworten basierend auf den gefundenen Daten
- ✅ Zitieren Sie die spezifischen Quellen: "Laut [Dokumentname]..." oder "Gemäß PostgreSQL-Datenbank..."
- ✅ Strukturieren Sie die Antwort klar mit Absätzen und Details
- ✅ Verwenden Sie ALLE relevanten Informationen aus dem Kontext

WENN KEINE DATEN GEFUNDEN WURDEN (Abschnitt "KEINE DATEN IN DATENBANKEN GEFUNDEN"):
- Sagen Sie klar: "Ich habe keine relevanten Informationen in unserer Datenbank gefunden."
- Listen Sie auf, was genau gesucht wurde
- Fragen Sie: "Möchten Sie, dass ich diese Frage mit allgemeinem Wissen beantworte, oder soll ich weitere Details zur Präzisierung der Suche erfragen?"
- Warten Sie auf Benutzererlaubnis, bevor Sie allgemeines Wissen verwenden

=== ANTI-HALLUZINATIONS-REGELN (KRITISCH) ===
1. ❌ NIEMALS Informationen erfinden oder raten
2. ❌ NIEMALS allgemeines Wissen ohne explizite Benutzererlaubnis verwenden
3. ❌ NIEMALS Daten aus dem Kontext extrapolieren oder erweitern
4. ✅ NUR die bereitgestellten Kontext-Informationen verwenden
5. ✅ Bei Unsicherheit IMMER transparent kommunizieren
6. ✅ Fehlende Informationen klar benennen

=== ANTWORTSTRUKTUR ===
1. **Direkte Antwort**: Beantworten Sie die Frage basierend auf den Datenbankdaten
2. **Quellenangabe**: Geben Sie die spezifischen Quellen an (Dokumentname, Maschinendatenbank, etc.)
3. **Detaillierte Erklärung**: Erläutern Sie umfassend mit allen gefundenen Details
4. **Strukturierung**: Verwenden Sie Absätze, Aufzählungen, klare Gliederung
5. **Transparenz**: Wenn Informationen fehlen, sagen Sie es klar

=== QUELLENANGABE (PFLICHT) ===
- Bei Dokumenten: "Quelle: [Dokumentname], Abschnitt/Seite [falls verfügbar]"
- Bei Maschinendaten: "Quelle: Maschinendatenbank - Modell [Modellnummer]"
- Bei mehreren Quellen: Listen Sie alle verwendeten Quellen auf
- Verwenden Sie Formulierungen wie: "Laut...", "Gemäß...", "In der Dokumentation zu...", "Die Datenbank zeigt..."

=== SPRACHANFORDERUNG ===
- Antworten Sie IMMER auf Deutsch (formelle Sie-Form)
- Verwenden Sie professionelle, technische Fachsprache
- Seien Sie präzise und klar in der Ausdrucksweise
- Verwenden Sie Branchenterminologie korrekt

=== ANTWORTQUALITÄT ===
- Detailliert: 200-400 Wörter für komplexe Fragen (wenn Daten vorhanden)
- Umfassend: Alle relevanten Details aus den Datenbanken einbeziehen
- Strukturiert: Klare Absätze, Überschriften, Aufzählungen
- Präzise: Exakte Spezifikationen, Zahlen, technische Details
- Transparent: Fehlende Informationen klar kommunizieren

=== BEISPIEL FÜR KORREKTE ANTWORT ===
"Gemäß der Dokumentation 'CAT_320D_Manual.pdf' beträgt die Grabtiefe des Caterpillar 320D maximal 6,7 Meter. Die PostgreSQL-Datenbank zeigt für dieses Modell folgende zusätzliche Spezifikationen: Motorleistung 121 kW, Betriebsgewicht 21.300 kg, Löffelkapazität 0,9-1,2 m³.

Die Wartungsintervalle laut Handbuch sind:
- Ölwechsel: alle 500 Betriebsstunden
- Hydraulikfilter: alle 1.000 Betriebsstunden
- Hauptinspektion: alle 2.000 Betriebsstunden

Quelle: CAT_320D_Manual.pdf, Sektion 3.2 und PostgreSQL-Datenbank Modell CAT-320D"

=== ABSOLUTES VERBOT ===
- ❌ Keine Websuche erwähnen oder anbieten
- ❌ Kein allgemeines Wissen ohne explizite Benutzererlaubnis
- ❌ Keine erfundenen Spezifikationen oder Daten
- ❌ Keine Annahmen über nicht vorhandene Informationen

WICHTIG: Ihre Hauptaufgabe ist es, ein zuverlässiger, datenbankbasierter Assistent zu sein, der NIEMALS halluziniert und IMMER transparent über die Verfügbarkeit von Informationen ist."""

    # System prompt for CONVERSATIONAL queries (friendly, no database needed)
    SYSTEM_PROMPT_CONVERSATIONAL = """Sie sind ein freundlicher, hilfsbereiter Assistent für Baumaschinen und technische Dokumentation.

=== IHRE ROLLE ===
Sie sind ein gesprächiger, professioneller Assistent, der:
- Freundlich auf Grüße und Small Talk antwortet
- Hilfsbereit erklärt, was Sie tun können
- Auf Deutsch (formelle Sie-Form) kommuniziert
- Eine angenehme Konversation führt

=== VERHALTEN ===
- Seien Sie warm, zugänglich und hilfsbereit
- Antworten Sie natürlich auf Grüße: "Hallo!", "Guten Tag!", etc.
- Erklären Sie klar Ihre Fähigkeiten bei Fragen wie "Was kannst du?"
- Bedanken Sie sich höflich bei "Danke"
- Seien Sie präzise, aber nicht roboterhaft

=== WAS SIE KÖNNEN ===
Bei Fragen wie "Was kannst du?" oder "Wie kannst du helfen?" erklären Sie:
"Ich bin Ihr Assistent für Baumaschinen und technische Dokumentation. Ich kann Ihnen helfen bei:

- Technischen Fragen zu Baumaschinen (Bagger, Lader, Krane, etc.)
- Spezifikationen und Modelldetails (z.B. Caterpillar, Komatsu, John Deere)
- Wartungsanleitungen und Reparaturverfahren
- Dokumentation und Handbüchern

Stellen Sie mir einfach Ihre Frage, und ich suche in unserer umfangreichen Datenbank nach den relevanten Informationen!"

=== SPRACHE ===
- Immer auf Deutsch (formelle Sie-Form)
- Professionell aber freundlich
- Klar und verständlich

=== BEISPIELE ===
Benutzer: "Hallo"
Sie: "Hallo! Wie kann ich Ihnen heute bei Baumaschinen oder technischer Dokumentation helfen?"

Benutzer: "Danke"
Sie: "Gerne! Wenn Sie weitere Fragen haben, stehe ich Ihnen jederzeit zur Verfügung."

Benutzer: "Wie geht es dir?"
Sie: "Danke der Nachfrage! Ich bin bereit, Ihnen bei allen Fragen rund um Baumaschinen und technische Dokumentation zu helfen. Wie kann ich Sie unterstützen?"

WICHTIG: Seien Sie freundlich und natürlich. Dies ist eine normale Konversation, keine Datenbankabfrage."""

    def __init__(self):
        """Initialize AI agent with services"""
        self.openai_service = get_openai_service()
        self.pinecone_service = get_pinecone_service()
        self.postgresql_service = get_postgresql_service()

        # Initialize Pydantic AI agent with custom provider
        provider = OpenAIProvider(api_key=settings.openai_api_key)
        self.model = OpenAIModel(
            model_name=settings.openai_chat_model,
            provider=provider
        )

        self.agent = Agent(
            model=self.model,
            system_prompt=self.SYSTEM_PROMPT_TECHNICAL,  # Default to technical mode
        )

        # Store temperature from settings
        self.temperature = settings.openai_temperature

        # Token budget for context (increased for more comprehensive data retrieval)
        self.max_context_tokens = 3500  # Increased from 2500 to 3500

        logger.info(
            f"AI Agent initialized with model: {settings.openai_chat_model}, "
            f"temperature: {settings.openai_temperature}"
        )

    async def classify_query(self, query: str) -> QueryCategory:
        """
        Classify user query to determine which data sources to use

        Klassifiziert Benutzeranfragen zur Bestimmung der zu verwendenden Datenquellen

        Args:
            query: User's question or request / Benutzeranfrage

        Returns:
            Query category determining data source selection / Anfragekategorie für Datenquellenauswahl

        Classification logic:
        - conversational: Greetings, thanks, small talk - NO database search needed
        - machinery_specs: Contains model numbers, spec keywords (capacity, fuel, weight, etc.)
        - documentation: Contains "how to", "procedure", "manual", "maintenance", "repair"
        - combined: Comparison queries, complex questions needing both sources
        - general: General knowledge questions not requiring specific data
        """
        query_lower = query.lower()
        query_words = query_lower.split()

        # STEP 1: Check for CONVERSATIONAL queries (highest priority - no DB search needed)
        conversational_keywords = [
            # Greetings - German
            "hallo", "hi", "hey", "guten tag", "guten morgen", "guten abend",
            "servus", "grüß gott", "moin", "grüezi",
            # Greetings - English
            "hello", "good morning", "good afternoon", "good evening",
            # Thanks
            "danke", "vielen dank", "dankeschön", "dankesehr", "thank you", "thanks",
            # Goodbyes
            "tschüss", "auf wiedersehen", "bis bald", "ciao", "goodbye", "bye",
            # Politeness
            "bitte", "bitteschön", "please", "you're welcome",
            # Small talk
            "wie geht", "wie gehts", "how are you", "what's up",
        ]

        # Check for direct conversational match
        for keyword in conversational_keywords:
            if keyword in query_lower:
                logger.info(f"✓ Anfrage klassifiziert als CONVERSATIONAL (Keyword: '{keyword}'): {query[:50]}...")
                return QueryCategory.CONVERSATIONAL

        # Check for very short queries (1-4 words) that are likely greetings/small talk
        # BUT exclude if they contain technical machinery keywords
        technical_indicators = [
            "bagger", "caterpillar", "cat", "maschine", "kran", "lader", "raupe",
            "excavator", "crane", "loader", "bulldozer", "machine", "equipment",
            "modell", "model", "spezifikation", "specification", "wartung", "maintenance"
        ]

        if len(query_words) <= 4:
            has_technical = any(indicator in query_lower for indicator in technical_indicators)
            if not has_technical:
                logger.info(f"✓ Anfrage klassifiziert als CONVERSATIONAL (kurze Anfrage ohne technische Keywords): {query[:50]}...")
                return QueryCategory.CONVERSATIONAL

        # Check for meta questions about the assistant itself
        meta_keywords = [
            "was kannst du", "was können sie", "wer bist du", "wer sind sie",
            "kannst du mir helfen", "können sie mir helfen", "hilfe", "help",
            "what can you", "who are you", "can you help"
        ]

        for keyword in meta_keywords:
            if keyword in query_lower:
                logger.info(f"✓ Anfrage klassifiziert als CONVERSATIONAL (Meta-Frage): {query[:50]}...")
                return QueryCategory.CONVERSATIONAL

        # STEP 2: Check for TECHNICAL queries (need database search)

        # Keywords for different categories (English + German for better coverage)
        spec_keywords = [
            # English
            "capacity", "fuel", "weight", "hp", "horsepower", "dimensions",
            "specifications", "specs", "model", "cat ", "john deere", "komatsu",
            "excavator", "bulldozer", "loader", "crane", "engine", "power",
            "size", "height", "width", "length", "ton", "kg", "liter",
            # German
            "kapazität", "kraftstoff", "gewicht", "ps", "pferdestärke", "abmessungen",
            "spezifikationen", "technische daten", "modell", "bagger", "raupe",
            "lader", "kran", "motor", "leistung", "größe", "höhe", "breite",
            "länge", "tonne", "maße", "hersteller"
        ]

        doc_keywords = [
            # English
            "how to", "how do i", "procedure", "manual", "maintenance",
            "repair", "fix", "troubleshoot", "service", "install",
            "replace", "change", "adjust", "inspect", "lubricate",
            "instruction", "guide", "setup", "configure",
            # German
            "wie", "anleitung", "handbuch", "wartung", "reparatur",
            "reparieren", "beheben", "fehlerbehebung", "service", "installieren",
            "ersetzen", "wechseln", "einstellen", "prüfen", "schmieren",
            "verfahren", "bedienungsanleitung", "montage", "demontage",
            "inbetriebnahme", "konfigurieren"
        ]

        comparison_keywords = [
            # English
            "compare", "difference", "which", "best", "recommend",
            "better", "versus", "vs", "between", "or",
            # German
            "vergleich", "vergleichen", "unterschied", "welche", "welcher",
            "beste", "empfehlen", "besser", "gegen", "oder", "zwischen"
        ]

        # Check for comparison queries (need both sources)
        if any(keyword in query_lower for keyword in comparison_keywords):
            logger.info(f"→ Anfrage klassifiziert als COMBINED (Vergleich): {query[:50]}...")
            return QueryCategory.COMBINED

        # Check for specific model numbers or machinery types
        has_specs = any(keyword in query_lower for keyword in spec_keywords)
        has_docs = any(keyword in query_lower for keyword in doc_keywords)

        if has_specs and has_docs:
            logger.info(f"→ Anfrage klassifiziert als COMBINED (beide Indikatoren): {query[:50]}...")
            return QueryCategory.COMBINED
        elif has_specs:
            logger.info(f"→ Anfrage klassifiziert als MACHINERY_SPECS: {query[:50]}...")
            return QueryCategory.MACHINERY_SPECS
        elif has_docs:
            logger.info(f"→ Anfrage klassifiziert als DOCUMENTATION: {query[:50]}...")
            return QueryCategory.DOCUMENTATION
        else:
            logger.info(f"→ Anfrage klassifiziert als GENERAL: {query[:50]}...")
            return QueryCategory.GENERAL

    async def retrieve_from_pinecone(
        self,
        query: str,
        top_k: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks from Pinecone vector database

        Ruft relevante Dokumenten-Chunks aus der Pinecone-Vektordatenbank ab

        Args:
            query: User's query / Benutzeranfrage
            top_k: Number of results to retrieve / Anzahl der abzurufenden Ergebnisse (erhöht auf 15)

        Returns:
            List of relevant document chunks with metadata / Liste relevanter Dokument-Chunks mit Metadaten

        Process:
        1. Generate embedding for query / Embedding für Anfrage generieren
        2. Search Pinecone index / Pinecone-Index durchsuchen
        3. Filter by relevance score (>0.50) / Nach Relevanzscore filtern (>0.50) - LOWERED FROM 0.65
        4. Return formatted results with sources / Formatierte Ergebnisse mit Quellen zurückgeben
        """
        try:
            # Generate embedding for query
            embedding = await self.openai_service.generate_embedding(query)

            # Query Pinecone with increased top_k for better coverage
            results = await self.pinecone_service.query_vectors(
                embedding=embedding,
                top_k=top_k,
                include_metadata=True
            )

            # DEBUG LOGGING - Track retrieval performance
            logger.info(f"[DEBUG] Pinecone raw results: {len(results)} items retrieved for query: '{query[:50]}...'")

            # Log score distribution for debugging
            if results:
                scores = [match.get("score", 0.0) for match in results]
                logger.info(f"[DEBUG] Score distribution - Min: {min(scores):.3f}, Max: {max(scores):.3f}, Avg: {sum(scores)/len(scores):.3f}")

            # Format and filter results by relevance score
            formatted_results = []
            filtered_count = 0

            for match in results:
                score = match.get("score", 0.0)

                # CRITICAL FIX: Lowered threshold from 0.65 → 0.50 → 0.45 for better recall
                # Lower threshold catches more potentially relevant results
                if score < 0.45:  # LOWERED FROM 0.50 - Even more permissive for better coverage
                    filtered_count += 1
                    logger.debug(f"[DEBUG] Filtered out result with score: {score:.3f}")
                    continue

                metadata = match.get("metadata", {})
                formatted_results.append({
                    "text": metadata.get("text_content", ""),
                    "source": metadata.get("filename", "Unbekannt"),
                    "category": metadata.get("category", ""),
                    "score": score,
                    "chunk_index": metadata.get("chunk_index", 0),
                    "page": metadata.get("page", "N/A")
                })

            logger.info(f"[DEBUG] Pinecone: {len(formatted_results)} relevante Dokumente nach Filterung (gefiltert: {filtered_count}, threshold: 0.45)")

            # Log if we're filtering too aggressively
            if len(results) > 0 and len(formatted_results) == 0:
                logger.warning(f"[WARNING] All {len(results)} Pinecone results filtered out! Consider lowering threshold further.")

            return formatted_results

        except Exception as e:
            logger.error(f"Fehler beim Abrufen aus Pinecone-Datenbank: {str(e)}")
            return []  # Return empty list on error (graceful degradation)

    async def retrieve_from_postgresql(
        self,
        query: str,
        authorization_level: str
    ) -> Dict[str, Any]:
        """
        Retrieve machinery data from PostgreSQL database

        Ruft Maschinendaten aus der PostgreSQL-Datenbank ab

        Args:
            query: User's query / Benutzeranfrage
            authorization_level: User's authorization level / Berechtigungsstufe (regular/superuser/admin)

        Returns:
            Dictionary with machinery data and metadata / Wörterbuch mit Maschinendaten und Metadaten

        Process:
        1. Analyze query for machinery identifiers / Anfrage nach Maschinen-Identifikatoren analysieren
        2. Call appropriate API endpoint / Entsprechenden API-Endpunkt aufrufen
        3. Retrieve more comprehensive data (limit increased to 10) / Umfassendere Daten abrufen (Limit erhöht auf 10)
        4. Format results for AI consumption / Ergebnisse für KI-Verarbeitung formatieren
        """
        try:
            # DEBUG LOGGING - Track query
            logger.info(f"[DEBUG] PostgreSQL search for query: '{query[:50]}...' with auth level: {authorization_level}")

            # Search for machinery based on query with increased limit for thoroughness
            results = await self.postgresql_service.search_machinery(
                query=query,
                authorization_level=authorization_level,
                limit=10  # Increased from 5 to 10 for more comprehensive results
            )

            machinery_list = results.get("results", [])

            # DEBUG LOGGING - Track results
            logger.info(f"[DEBUG] PostgreSQL raw results: {len(machinery_list)} items retrieved")

            if not machinery_list:
                logger.info("[DEBUG] PostgreSQL: Keine Maschinendaten gefunden")
                return {"data": [], "source": "PostgreSQL-Datenbank", "count": 0, "machinery": []}

            # Log sample of what we found
            if machinery_list:
                sample = machinery_list[0]
                logger.info(f"[DEBUG] PostgreSQL sample result: {sample.get('name', 'Unknown')} - {sample.get('model', 'No model')}")

            # Format for AI consumption - ensure 'machinery' key is always present
            formatted_data = {
                "source": "PostgreSQL-Datenbank",
                "count": len(machinery_list),
                "machinery": machinery_list
            }

            logger.info(f"[DEBUG] PostgreSQL: {len(machinery_list)} Maschineneinträge zur Verwendung bereit")
            return formatted_data

        except Exception as e:
            logger.error(f"[ERROR] Fehler beim Abrufen aus PostgreSQL-Datenbank: {str(e)}")
            return {"data": [], "source": "PostgreSQL-Datenbank", "error": str(e), "count": 0, "machinery": []}

    async def aggregate_context(
        self,
        query: str,
        pinecone_results: Optional[List[Dict[str, Any]]] = None,
        postgresql_results: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[str]]:
        """
        Aggregate context from multiple database sources with token management

        Aggregiert Kontext aus mehreren Datenbankquellen mit Token-Management

        Args:
            query: Original user query / Ursprüngliche Benutzeranfrage
            pinecone_results: Document chunks from Pinecone / Dokumenten-Chunks aus Pinecone
            postgresql_results: Machinery data from PostgreSQL / Maschinendaten aus PostgreSQL

        Returns:
            Tuple of (context_string, sources_list) / Tupel aus (Kontext-String, Quellenliste)

        Token Management:
        - Allocates ~3500 tokens for context (increased from 2500)
        - Prioritizes most relevant information
        - Includes more comprehensive data from both sources
        - Truncates if necessary
        """
        context_parts = []
        sources = []
        has_data = False

        # DEBUG LOGGING - Track what we're aggregating
        pinecone_count = len(pinecone_results) if pinecone_results else 0
        postgresql_count = len(postgresql_results.get("machinery", [])) if postgresql_results else 0
        logger.info(f"[DEBUG] Aggregating context - Pinecone: {pinecone_count} items, PostgreSQL: {postgresql_count} items")

        # Add PostgreSQL data if available (increased limit for more comprehensive data)
        if postgresql_results and postgresql_results.get("machinery"):
            has_data = True
            context_parts.append("=== MASCHINENDATEN AUS POSTGRESQL-DATENBANK ===")
            context_parts.append("WICHTIG: Nutzen Sie diese Daten für Ihre Antwort.\n")  # CHANGED: More encouraging

            # Increased from 3 to 8 for more comprehensive machinery data
            for machinery in postgresql_results["machinery"][:8]:
                machinery_text = self._format_machinery_data(machinery)
                context_parts.append(machinery_text)

            sources.append("PostgreSQL-Datenbank")
            logger.info(f"[DEBUG] Added {len(postgresql_results['machinery'][:8])} machinery items to context")

        # Add Pinecone documentation if available (increased limit for more comprehensive data)
        if pinecone_results:
            has_data = True
            context_parts.append("\n=== DOKUMENTATION AUS PINECONE-VEKTORDATENBANK ===")
            context_parts.append("WICHTIG: Nutzen Sie diese Dokumenteninhalte für Ihre Antwort.\n")  # CHANGED: More encouraging

            # Increased from 5 to 10 for more comprehensive documentation
            for idx, result in enumerate(pinecone_results[:10], 1):
                score_indicator = "⭐⭐⭐" if result['score'] > 0.85 else "⭐⭐" if result['score'] > 0.75 else "⭐"
                doc_text = f"\n[Dokument {idx}] {score_indicator} Relevanz: {result['score']:.2f}\n"
                doc_text += f"Quelle: {result['source']}"
                if result.get('page') != "N/A":
                    doc_text += f", Seite {result['page']}"
                doc_text += f"\nInhalt:\n{result['text']}\n"
                context_parts.append(doc_text)

                if result['source'] not in sources:
                    sources.append(f"Dokument: {result['source']}")

            logger.info(f"[DEBUG] Added {len(pinecone_results[:10])} document chunks to context")

        # Add explicit instruction based on data availability
        if has_data:
            # CRITICAL FIX: Emphasize USING the data when it exists
            context_parts.append("\n=== DATEN GEFUNDEN - BITTE VERWENDEN ===")
            context_parts.append("WICHTIG: Es wurden relevante Daten in den Datenbanken gefunden.")
            context_parts.append("Sie MÜSSEN diese Daten für Ihre Antwort verwenden.")
            context_parts.append("Zitieren Sie die Quellen und geben Sie eine umfassende Antwort basierend auf diesen Daten.\n")
        else:
            # Only say "no data" when TRULY no data
            context_parts.append("\n=== KEINE DATEN IN DATENBANKEN GEFUNDEN ===")
            context_parts.append("WICHTIG: Es wurden KEINE relevanten Daten in den Datenbanken gefunden.")
            context_parts.append("Sie MÜSSEN dem Benutzer mitteilen, dass keine Informationen verfügbar sind.")
            context_parts.append("Fragen Sie, ob der Benutzer möchte, dass Sie mit allgemeinem Wissen antworten.\n")

        # Add user query
        context_parts.append(f"\n=== BENUTZERANFRAGE ===\n{query}")

        # Combine context
        full_context = "\n".join(context_parts)

        # Check token count and truncate if needed (increased budget to 3500)
        token_count = self.openai_service.count_tokens(full_context)

        if token_count > self.max_context_tokens:
            logger.warning(f"[DEBUG] Kontext überschreitet Token-Budget ({token_count} > {self.max_context_tokens}), kürze...")
            full_context = self.openai_service.truncate_text(full_context, self.max_context_tokens)
            token_count = self.max_context_tokens

        # CRITICAL DEBUG LOG
        logger.info(f"[DEBUG] Context aggregated: {token_count} tokens, {len(sources)} sources, has_data={has_data}")
        logger.info(f"[DEBUG] Context preview (first 200 chars): {full_context[:200]}")

        return full_context, sources

    def _format_machinery_data(self, machinery: Dict[str, Any]) -> str:
        """
        Format machinery data as readable German text

        Formatiert Maschinendaten als lesbaren deutschen Text
        """
        lines = [f"\nMaschine: {machinery.get('name', 'Unbekannt')}"]

        if machinery.get('model'):
            lines.append(f"Modell: {machinery['model']}")
        if machinery.get('manufacturer'):
            lines.append(f"Hersteller: {machinery['manufacturer']}")
        if machinery.get('type'):
            lines.append(f"Typ: {machinery['type']}")
        if machinery.get('category'):
            lines.append(f"Kategorie: {machinery['category']}")
        if machinery.get('year'):
            lines.append(f"Baujahr: {machinery['year']}")

        # Add specifications if available
        specs = machinery.get('specifications', {})
        if specs:
            lines.append("Spezifikationen:")
            for key, value in specs.items():
                lines.append(f"  • {key}: {value}")

        # Add additional details if available
        if machinery.get('description'):
            lines.append(f"Beschreibung: {machinery['description']}")

        if machinery.get('status'):
            lines.append(f"Status: {machinery['status']}")

        return "\n".join(lines)

    async def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate AI response (non-streaming)

        Args:
            query: User's query
            context: Aggregated context from retrieval
            conversation_history: Previous messages in conversation

        Returns:
            Complete AI response
        """
        # Build messages
        messages = []

        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current query with context
        user_message = f"{context}\n\n---\n\nBased on the above information, please answer: {query}"
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Generate response
        response = await self.openai_service.generate_chat_completion(
            messages=messages
        )

        return response["content"]

    async def generate_response_stream(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        category: Optional[QueryCategory] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming AI response with dual-mode operation

        Generiert Streaming-KI-Antwort mit Dual-Modus-Betrieb

        Args:
            query: User's query / Benutzeranfrage
            context: Aggregated context from retrieval / Aggregierter Kontext aus Datenbankabfragen
            conversation_history: Previous messages / Vorherige Nachrichten
            category: Query category to determine response mode / Anfragekategorie zur Bestimmung des Antwortmodus

        Yields:
            Response tokens as they are generated / Antwort-Tokens während der Generierung

        Mode Selection:
        - CONVERSATIONAL: Use lighter prompt, no context needed, friendly responses
        - TECHNICAL (all others): Use database-first prompt with full context
        """

        # CONVERSATIONAL MODE: Simple, friendly responses without database context
        if category == QueryCategory.CONVERSATIONAL:
            logger.info("[MODE] Conversational mode activated - No database context needed")
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT_CONVERSATIONAL},
                {"role": "user", "content": query}
            ]

            # Stream response directly
            async for token in self.openai_service.generate_chat_completion_stream(messages):
                yield token
            return

        # TECHNICAL MODE: Database-first with full context
        logger.info("[MODE] Technical mode activated - Using database context")
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT_TECHNICAL}]

        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current query with context and balanced instructions
        user_message = f"""{context}

═══════════════════════════════════════════════════════════

ANWEISUNGEN FÜR DIESE ANTWORT:

1. ✅ Nutzen Sie die oben bereitgestellten Kontext-Informationen für Ihre Antwort
2. ✅ Antworten Sie IMMER auf Deutsch (formelle Sie-Form)
3. ✅ Zitieren Sie verwendete Quellen klar und deutlich
4. ✅ Wenn Daten vorhanden sind (MASCHINENDATEN oder DOKUMENTATION), nutzen Sie diese aktiv

WICHTIG - Prüfen Sie den Kontext oben:
- Enthält er "MASCHINENDATEN AUS POSTGRESQL-DATENBANK"? → Nutzen Sie diese Daten
- Enthält er "DOKUMENTATION AUS PINECONE-VEKTORDATENBANK"? → Nutzen Sie diese Inhalte
- Enthält er "KEINE DATEN IN DATENBANKEN GEFUNDEN"? → Nur dann sagen Sie "keine Daten gefunden"

WENN DATEN VORHANDEN SIND (Sie sehen MASCHINENDATEN oder DOKUMENTATION oben):
- ✅ NUTZEN Sie diese Informationen umfassend für Ihre Antwort
- ✅ Geben Sie eine detaillierte, hilfreiche Antwort
- ✅ Zitieren Sie Quellen: "Laut [Quelle]..." oder "Gemäß [Dokument]..."
- ✅ Strukturieren Sie die Antwort klar mit Absätzen

WENN WIRKLICH KEINE DATEN VORHANDEN SIND (Sie sehen "KEINE DATEN IN DATENBANKEN GEFUNDEN"):
- Sagen Sie: "Ich habe keine relevanten Informationen in unserer Datenbank gefunden."
- Fragen Sie: "Möchten Sie, dass ich diese Frage mit allgemeinem Wissen beantworte?"

═══════════════════════════════════════════════════════════

BENUTZERANFRAGE:
{query}"""

        messages.append({
            "role": "user",
            "content": user_message
        })

        # Stream response
        async for token in self.openai_service.generate_chat_completion_stream(messages):
            yield token

    async def process_query(
        self,
        query: str,
        authorization_level: str = "regular",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, List[str], QueryCategory]:
        """
        Complete query processing pipeline

        Args:
            query: User's query
            authorization_level: User's authorization level
            conversation_history: Previous conversation messages

        Returns:
            Tuple of (response, sources, category)

        Pipeline:
        1. Classify query
        2. Retrieve from appropriate sources
        3. Aggregate context
        4. Generate response
        """
        # Step 1: Classify query
        category = await self.classify_query(query)

        # Step 2: Retrieve based on category
        pinecone_results = None
        postgresql_results = None

        if category in [QueryCategory.DOCUMENTATION, QueryCategory.COMBINED]:
            pinecone_results = await self.retrieve_from_pinecone(query)

        if category in [QueryCategory.MACHINERY_SPECS, QueryCategory.COMBINED]:
            postgresql_results = await self.retrieve_from_postgresql(query, authorization_level)

        # Step 3: Aggregate context
        context, sources = await self.aggregate_context(
            query=query,
            pinecone_results=pinecone_results,
            postgresql_results=postgresql_results
        )

        # Step 4: Generate response
        response = await self.generate_response(
            query=query,
            context=context,
            conversation_history=conversation_history
        )

        return response, sources, category


# Singleton instance
_ai_agent = None


def get_ai_agent() -> AIAgent:
    """Get singleton AI agent instance"""
    global _ai_agent
    if _ai_agent is None:
        _ai_agent = AIAgent()
    return _ai_agent
