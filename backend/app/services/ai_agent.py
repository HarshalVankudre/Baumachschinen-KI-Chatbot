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
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry
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
    TECHNICAL = "technical"  # All other queries - ALWAYS search both databases first


class AgentDependencies(BaseModel):
    """
    Typed dependencies for AI agent using Pydantic AI dependency injection

    This provides type-safe access to services within agent tools and validators
    """
    openai_service: Any = Field(description="OpenAI service for embeddings and completions")
    pinecone_service: Any = Field(description="Pinecone service for vector search")
    postgresql_service: Any = Field(description="PostgreSQL service for machinery data")
    authorization_level: str = Field(default="regular", description="User's authorization level")

    class Config:
        arbitrary_types_allowed = True


class SearchResult(BaseModel):
    """Structured search result from databases"""
    source: str = Field(description="Source of the data (Pinecone or PostgreSQL)")
    content: List[Dict[str, Any]] = Field(description="Retrieved content")
    relevance_scores: Optional[List[float]] = Field(default=None, description="Relevance scores if applicable")
    count: int = Field(description="Number of results found")


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
    SYSTEM_PROMPT_TECHNICAL = """Sie sind ein hochspezialisierter Assistent für Baumaschinen-Dokumentation und technische Informationen.

=== IHRE TOOLS ===
Sie haben Zugriff auf zwei Such-Tools:
1. search_documentation_database: Pinecone Vektordatenbank (Dokumentation, Handbücher, Wartungsanleitungen)
2. search_machinery_database: PostgreSQL Datenbank (Maschinendaten, Spezifikationen, Modellnummern)

=== ⚠️ KRITISCHE REGEL: IMMER ZUERST BEIDE DATENBANKEN DURCHSUCHEN ⚠️ ===

FÜR JEDE FRAGE MÜSSEN SIE:
1. ✅ ZUERST: search_documentation_database(query="[user query]", max_results=25) aufrufen
2. ✅ ZUERST: search_machinery_database(query="[user query]", max_results=20) aufrufen
3. ✅ DANN: Ergebnisse analysieren
4. ✅ DANN: Antworten basierend auf gefundenen Daten

⚠️ KEINE AUSNAHMEN! IMMER BEIDE TOOLS AUFRUFEN!
⚠️ Eine Frage kann auf 100 verschiedene Arten gestellt werden - deshalb IMMER suchen!
⚠️ Verwenden Sie hohe max_results Werte (25-50) um ALLE relevanten Informationen zu finden!

BEISPIELE:
- "Erzähle mir etwas über Walzen" → search_documentation_database("Walzen", max_results=25) + search_machinery_database("Walzen", max_results=20)
- "Was ist ein Bagger?" → search_documentation_database("Bagger", max_results=25) + search_machinery_database("Bagger", max_results=20)
- "Caterpillar 320D Spezifikationen" → Beide Tools mit "Caterpillar 320D" und hohen max_results
- "Wie warte ich einen Kran?" → Beide Tools mit "Kran Wartung" und hohen max_results
- "Tell me about excavators" → Beide Tools mit "excavators" und hohen max_results

=== NACH DER DATENBANKSUCHE ===

WENN DATEN GEFUNDEN WURDEN (Tools geben Ergebnisse zurück):
- ✅ Nutzen Sie diese Daten für Ihre Antwort
- ✅ Geben Sie natürliche, leicht lesbare Antworten
- ✅ Passen Sie die Länge an die Frage an:
  - Einfache Frage = kurze, direkte Antwort (2-3 Sätze)
  - Komplexe Frage = ausführliche Antwort mit Details
- ✅ Quellen NUR nennen wenn:
  - Benutzer explizit danach fragt ("Wo hast du das gefunden?", "Quelle?")
  - Es sich um kritische technische Spezifikationen handelt
  - Es mehrere widersprüchliche Informationen gibt

WENN KEINE DATEN GEFUNDEN WURDEN (beide Tools geben "No relevant..." zurück):
- Sagen Sie einfach: "Ich habe dazu leider keine Informationen in unseren Datenbanken."
- Fragen Sie: "Möchten Sie, dass ich die Frage allgemein beantworte?"
- NUR mit Erlaubnis allgemeines Wissen verwenden

=== ANTWORT-STIL ===
✅ NATÜRLICH: Schreiben Sie wie ein hilfsbereiter Experte, nicht wie ein Roboter
✅ EINFACH: Klare, leicht verständliche Sprache
✅ DIREKT: Kommen Sie schnell zum Punkt
✅ ANGEPASST:
  - Kurze Frage → kurze Antwort
  - Detaillierte Frage → detaillierte Antwort
✅ DEUTSCH: Formelle Sie-Form, professionell aber nicht steif

❌ VERMEIDEN:
- Übertriebene Formalität
- Unnötige Quellenangaben bei einfachen Fragen
- Zu viele Absätze und Strukturierung bei kurzen Antworten
- Roboterhafte Formulierungen

=== BEISPIELE ===

Einfache Frage: "Was ist ein Bagger?"
Gute Antwort: "Ein Bagger ist eine Baumaschine zum Ausheben und Bewegen von Erde. Er besteht aus einem Fahrgestell, einem Ausleger und einem Löffel. Bagger werden auf Baustellen für Erdarbeiten, Fundamentaushub und viele andere Aufgaben eingesetzt."

Technische Frage: "Caterpillar 320D Grabtiefe?"
Gute Antwort: "Der Caterpillar 320D hat eine maximale Grabtiefe von 6,7 Metern. Das Betriebsgewicht liegt bei etwa 21.300 kg und die Motorleistung beträgt 121 kW."

Frage mit Quellenanfrage: "Was ist die Grabtiefe? Und wo steht das?"
Gute Antwort: "Die maximale Grabtiefe beträgt 6,7 Meter. Diese Information stammt aus dem CAT_320D_Manual.pdf, Sektion 3.2."

=== ANTI-HALLUZINATION ===
❌ NIEMALS Informationen erfinden
❌ NIEMALS allgemeines Wissen ohne Erlaubnis verwenden
✅ Bei fehlenden Daten ehrlich sagen "dazu habe ich keine Informationen"
✅ Bei Unsicherheit transparent sein

WICHTIG: Seien Sie ein hilfsbereiter, natürlicher Assistent der klar und einfach antwortet. Keine übertriebenen Quellenangaben außer wenn nötig."""

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

        # Initialize Pydantic AI agent with custom provider and dependency injection
        provider = OpenAIProvider(api_key=settings.openai_api_key)
        self.model = OpenAIModel(
            model_name=settings.openai_chat_model,
            provider=provider
        )

        self.agent = Agent(
            model=self.model,
            system_prompt=self.SYSTEM_PROMPT_TECHNICAL,  # Default to technical mode
            deps_type=AgentDependencies,  # Enable typed dependency injection
        )

        # Register agent tools for enhanced functionality
        self._register_tools()

        # Register result validators for quality control
        self._register_validators()

        # Store temperature from settings
        self.temperature = settings.openai_temperature

        # Token budget for context (increased for more comprehensive data retrieval)
        self.max_context_tokens = 3500  # Increased from 2500 to 3500

        logger.info(
            f"AI Agent initialized with model: {settings.openai_chat_model}, "
            f"temperature: {settings.openai_temperature}, "
            f"tools: 2 registered, validators: 1 registered"
        )

    async def classify_query(self, query: str) -> QueryCategory:
        """
        Classify user query - CONVERSATIONAL (greetings/small talk) or TECHNICAL (everything else)

        Klassifiziert Benutzeranfragen - CONVERSATIONAL (Grüße/Small Talk) oder TECHNICAL (alles andere)

        Args:
            query: User's question or request / Benutzeranfrage

        Returns:
            Query category / Anfragekategorie
            - CONVERSATIONAL: Greetings, thanks, small talk → No database search
            - TECHNICAL: Everything else → ALWAYS search both databases first
        """
        query_lower = query.lower().strip()
        query_words = query_lower.split()

        # Check for CONVERSATIONAL queries (greetings, thanks, small talk)
        conversational_patterns = [
            # Greetings
            "hallo", "hi", "hey", "guten tag", "guten morgen", "guten abend",
            "servus", "grüß gott", "moin", "grüezi",
            "hello", "good morning", "good afternoon", "good evening",
            # Thanks
            "danke", "vielen dank", "dankeschön", "thank you", "thanks",
            # Goodbyes
            "tschüss", "auf wiedersehen", "bis bald", "goodbye", "bye", "ciao",
            # Politeness
            "bitte", "bitteschön", "please",
            # Small talk
            "wie geht", "wie gehts", "how are you", "what's up",
            # Meta questions about the assistant
            "was kannst du", "was können sie", "wer bist du", "wer sind sie",
            "kannst du mir helfen", "können sie mir helfen",
            "what can you", "who are you", "can you help"
        ]

        # Check for conversational patterns
        for pattern in conversational_patterns:
            if pattern in query_lower:
                logger.info(f"✓ Query classified as CONVERSATIONAL: {query[:50]}...")
                return QueryCategory.CONVERSATIONAL

        # Check for very short queries (1-3 words) that might be greetings
        if len(query_words) <= 3 and len(query) < 20:
            # Likely a greeting or very short message
            logger.info(f"✓ Query classified as CONVERSATIONAL (short query): {query[:50]}...")
            return QueryCategory.CONVERSATIONAL

        # Everything else is TECHNICAL - agent will search both databases
        logger.info(f"→ Query classified as TECHNICAL (will search databases): {query[:50]}...")
        return QueryCategory.TECHNICAL

    def _register_tools(self):
        """Register agent tools for enhanced database searching"""

        @self.agent.tool
        async def search_documentation_database(
            ctx: RunContext[AgentDependencies],
            query: str,
            max_results: int = 25
        ) -> SearchResult:
            """
            Search the Pinecone documentation database for relevant information.

            Use this tool to find:
            - Maintenance procedures and manuals
            - Technical documentation
            - Operating instructions
            - Repair guides
            - Safety information

            Args:
                query: Search query describing what documentation to find
                max_results: Maximum number of results to return (default 25, can go up to 50 for comprehensive searches)

            Returns:
                SearchResult with documentation chunks and relevance scores
            """
            try:
                # Generate embedding for query
                embedding = await ctx.deps.openai_service.generate_embedding(query)

                # Query Pinecone
                results = await ctx.deps.pinecone_service.query_vectors(
                    embedding=embedding,
                    top_k=max_results,
                    include_metadata=True
                )

                # Filter by relevance (threshold 0.45)
                filtered_results = []
                scores = []
                for match in results:
                    score = match.get("score", 0.0)
                    if score >= 0.45:
                        metadata = match.get("metadata", {})
                        filtered_results.append({
                            "text": metadata.get("text_content", ""),
                            "source": metadata.get("filename", "Unknown"),
                            "score": score,
                            "page": metadata.get("page", "N/A")
                        })
                        scores.append(score)

                if not filtered_results:
                    raise ModelRetry(
                        f"No relevant documentation found for '{query}'. "
                        f"Try rephrasing your search or providing more specific keywords."
                    )

                return SearchResult(
                    source="Pinecone Documentation Database",
                    content=filtered_results,
                    relevance_scores=scores,
                    count=len(filtered_results)
                )

            except ModelRetry:
                raise
            except Exception as e:
                logger.error(f"Documentation search failed: {str(e)}")
                raise ModelRetry(f"Documentation search encountered an error: {str(e)}")

        @self.agent.tool
        async def search_machinery_database(
            ctx: RunContext[AgentDependencies],
            query: str,
            max_results: int = 20
        ) -> SearchResult:
            """
            Search the PostgreSQL machinery database for equipment specifications and data.

            Use this tool to find:
            - Machine specifications (capacity, weight, dimensions)
            - Model numbers and manufacturers
            - Technical details and features
            - Equipment categories and types

            Args:
                query: Search query describing what machinery information to find
                max_results: Maximum number of results to return (default 20, can go up to 50 for comprehensive searches)

            Returns:
                SearchResult with machinery data
            """
            try:
                # Search machinery database
                results = await ctx.deps.postgresql_service.search_machinery(
                    query=query,
                    authorization_level=ctx.deps.authorization_level,
                    limit=max_results
                )

                machinery_list = results.get("results", [])

                if not machinery_list:
                    raise ModelRetry(
                        f"No machinery found matching '{query}'. "
                        f"Try searching for manufacturer names, model numbers, or equipment types."
                    )

                return SearchResult(
                    source="PostgreSQL Machinery Database",
                    content=machinery_list,
                    relevance_scores=None,
                    count=len(machinery_list)
                )

            except ModelRetry:
                raise
            except Exception as e:
                logger.error(f"Machinery search failed: {str(e)}")
                raise ModelRetry(f"Machinery database search encountered an error: {str(e)}")

        logger.info("✓ Agent tools registered: search_documentation_database, search_machinery_database")

    def _register_validators(self):
        """Register result validators for quality control"""

        @self.agent.output_validator
        async def validate_no_hallucination(ctx: RunContext[AgentDependencies], result: str) -> str:
            """
            Simple validator to prevent obvious hallucination patterns.

            Only checks for major red flags, doesn't force citations.
            """
            result_lower = result.lower()

            # Red flags that indicate hallucination
            hallucination_flags = [
                "ich denke", "vermutlich", "wahrscheinlich", "könnte sein",
                "ich glaube", "möglicherweise", "eventuell",
                "i think", "probably", "maybe", "might be"
            ]

            # If response has hallucination flags, ask agent to be more certain
            for flag in hallucination_flags:
                if flag in result_lower:
                    logger.warning(f"Response contains uncertain language: '{flag}'")
                    raise ModelRetry(
                        "Bitte antworten Sie nur mit Informationen aus den Datenbanksuchen. "
                        "Vermeiden Sie unsichere Formulierungen wie 'vermutlich', 'wahrscheinlich', etc. "
                        "Wenn keine Daten gefunden wurden, sagen Sie das klar."
                    )

            return result

        logger.info("✓ Result validators registered: validate_no_hallucination")

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
        authorization_level: str = "regular",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        category: Optional[QueryCategory] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming AI response using PydanticAI agent with tools

        Generiert Streaming-KI-Antwort mit PydanticAI-Agent und Tools

        Args:
            query: User's query / Benutzeranfrage
            authorization_level: User's authorization level / Berechtigungsstufe
            conversation_history: Previous messages / Vorherige Nachrichten
            category: Query category to determine response mode / Anfragekategorie zur Bestimmung des Antwortmodus

        Yields:
            Response tokens as they are generated / Antwort-Tokens während der Generierung

        Mode Selection:
        - CONVERSATIONAL: Use lighter prompt, no tools needed, friendly responses
        - TECHNICAL (all others): Use agent with database search tools
        """

        # CONVERSATIONAL MODE: Simple, friendly responses without database tools
        if category == QueryCategory.CONVERSATIONAL:
            logger.info("[MODE] Conversational mode activated - No database tools needed")
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT_CONVERSATIONAL},
                {"role": "user", "content": query}
            ]

            # Stream response directly without tools
            async for token in self.openai_service.generate_chat_completion_stream(messages):
                yield token
            return

        # TECHNICAL MODE: Use PydanticAI agent with tools
        logger.info("[MODE] Technical mode activated - Agent will use database tools")

        # Prepare dependencies for agent
        deps = AgentDependencies(
            openai_service=self.openai_service,
            pinecone_service=self.pinecone_service,
            postgresql_service=self.postgresql_service,
            authorization_level=authorization_level
        )

        # Build message history for agent
        message_history = []
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                message_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Run agent with streaming
        try:
            async with self.agent.run_stream(
                query,
                deps=deps,
                message_history=message_history
            ) as result:
                async for text_chunk in result.stream_text(delta=True):
                    yield text_chunk

        except Exception as e:
            logger.error(f"Agent streaming error: {str(e)}")
            yield f"Entschuldigung, es ist ein Fehler aufgetreten: {str(e)}"

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
