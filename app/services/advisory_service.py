"""
services/advisory_service.py - Gemini LLM-powered ICAR advisory for AgroGuard-AI.

Architecture:
    Primary  → Google Gemini 1.5 Flash (free tier, dynamic AI-generated advisory)
    Fallback → Hardcoded ICAR knowledge base (if Gemini fails or quota exceeded)

Gemini generates contextual, ICAR-aligned treatment advisories for each
banana disease and severity level detected by the ML model.
"""

from google import genai

from app.config import get_settings
from app.utils.logger import get_logger

logger   = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Gemini setup
# ---------------------------------------------------------------------------
_gemini_client = None


def _get_gemini_model():
    """Lazy-load Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        try:
            _gemini_client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options={"api_version": "v1beta"}
            )
            logger.info("✓ Gemini 2.5 Flash client initialised.")
        except Exception as exc:
            logger.error("✗ Gemini initialisation failed: %s", exc)
            _gemini_client = None
    return _gemini_client


# ---------------------------------------------------------------------------
# System prompt — strict ICAR alignment
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """You are AgroGuard-AI, an expert agricultural advisor specializing 
in banana crop disease management. You provide treatment advisories strictly aligned 
with ICAR (Indian Council of Agricultural Research) guidelines, specifically from 
ICAR-NRCB (National Research Centre for Banana), Trichy, India.

RULES:
1. Always recommend treatments from ICAR-NRCB guidelines only
2. Include specific chemical names with exact dosages (e.g., Mancozeb 75 WP @ 0.2%)
3. Include biological control options where applicable
4. Structure response with numbered steps
5. Add urgency indicators for High severity (⚠ URGENT)
6. Add ✅ for healthy plants
7. Always end with: Source: ICAR-NRCB, Trichy
8. Keep response practical and farmer-friendly
9. Do NOT recommend unverified treatments
10. Response must be in English only"""


# ---------------------------------------------------------------------------
# Hardcoded ICAR fallback knowledge base
# Used when Gemini is unavailable or quota exceeded
# ---------------------------------------------------------------------------
_FALLBACK_KB: dict[str, dict[str, str]] = {
    "panama": {
        "High": (
            "⚠ URGENT — Panama Disease (Fusarium Wilt) Confirmed.\n\n"
            "There is NO chemical cure for this disease. Take immediate action:\n"
            "1. Uproot and destroy all infected plants by burning — do NOT compost.\n"
            "2. Quarantine the affected plot; restrict movement of soil, tools, and water.\n"
            "3. Solarise the infected soil for 6–8 weeks using transparent polythene.\n"
            "4. Apply Trichoderma viride (ICAR-recommended bioagent) @ 2.5 kg/ha to soil.\n"
            "5. For replanting, switch to Fusarium-resistant varieties such as Grand Nain, "
            "FHIA-01, FHIA-17, or Nendran (disease-free certified suckers only).\n"
            "6. Maintain field drainage to prevent root waterlogging.\n"
            "7. Report the outbreak to your nearest Horticulture Department immediately.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Panama Disease (Fusarium Wilt) — Moderate Signs Detected.\n\n"
            "1. Remove and burn all wilting or yellowing plants.\n"
            "2. Apply Trichoderma viride @ 25 g per plant in the root zone.\n"
            "3. Avoid overhead irrigation; use drip irrigation.\n"
            "4. Disinfect all farm tools with 2% formaldehyde solution.\n"
            "5. Monitor neighbouring plants every 3 days.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Early Panama Disease Indicators — Remain Vigilant.\n\n"
            "1. Improve field drainage; avoid waterlogging at the root zone.\n"
            "2. Apply Pseudomonas fluorescens @ 2 kg/ha as a soil drench.\n"
            "3. Scout the plantation weekly for yellowing lower leaves.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },
    "black sigatoka": {
        "High": (
            "⚠ URGENT — Severe Black Sigatoka Detected.\n\n"
            "1. Remove and burn all heavily infected leaves immediately.\n"
            "2. Apply Propiconazole 25 EC @ 0.1% at 10-day intervals.\n"
            "3. Apply copper oxychloride @ 0.2% as protective spray.\n"
            "4. Avoid overhead irrigation; use drip irrigation.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Moderate Black Sigatoka Detected.\n\n"
            "1. Remove lower infected leaves and destroy them.\n"
            "2. Apply Mancozeb 75 WP @ 0.2% fungicide spray.\n"
            "3. Improve canopy ventilation by thinning excess suckers.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Early Black Sigatoka Signs Observed.\n\n"
            "1. Apply preventive copper-based fungicide spray.\n"
            "2. Ensure balanced NPK fertilisation.\n"
            "3. Monitor weekly; remove leaves showing streak symptoms.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },
    "yellow sigatoka": {
        "High": (
            "⚠ URGENT — Severe Yellow Sigatoka Detected.\n\n"
            "1. Remove all leaves with more than 50% lesion coverage immediately.\n"
            "2. Apply Carbendazim 50 WP @ 0.1% OR Propiconazole 25 EC @ 0.1%.\n"
            "3. Spray at 14-day intervals during wet season.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Moderate Yellow Sigatoka Detected.\n\n"
            "1. Carry out regular leaf pruning to remove infected material.\n"
            "2. Apply Mancozeb 75 WP @ 0.25% as foliar spray.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Early Yellow Sigatoka Signs.\n\n"
            "1. Preventive spray with copper oxychloride @ 0.3%.\n"
            "2. Maintain adequate drainage to keep leaves dry.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },
    "weevil": {
        "High": (
            "⚠ URGENT — Severe Pseudostem Weevil Infestation Detected.\n\n"
            "1. Apply Carbofuran 3G granules @ 40 g per plant at pseudostem base.\n"
            "2. Install pheromone traps @ 10 traps per hectare.\n"
            "3. Apply Chlorpyrifos 20 EC @ 2.5 ml/litre as pseudostem drench.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Moderate Pseudostem Weevil Infestation.\n\n"
            "1. Apply Carbofuran 3G @ 25 g per plant.\n"
            "2. Install pheromone traps @ 5 traps per hectare.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Minor Pseudostem Weevil Activity.\n\n"
            "1. Maintain field sanitation.\n"
            "2. Install 2–3 pheromone traps per hectare for monitoring.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },
    "bunchy": {
        "High": (
            "⚠ URGENT — Banana Bunchy Top Virus (BBTV) Confirmed.\n\n"
            "There is NO chemical cure. Immediate action:\n"
            "1. Uproot and destroy ALL infected plants by burning.\n"
            "2. Apply Imidacloprid 17.8 SL @ 0.3 ml/litre to control aphid vectors.\n"
            "3. Establish 50-metre buffer zone.\n"
            "4. Use ONLY certified virus-free TC planting material.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "BBTV — Moderate Infection Detected.\n\n"
            "1. Rogue out all symptomatic plants and destroy immediately.\n"
            "2. Apply Imidacloprid 17.8 SL @ 0.5 ml/litre.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Early BBTV Symptoms Suspected.\n\n"
            "1. Control aphid populations with Imidacloprid spray.\n"
            "2. Remove and destroy symptomatic plants immediately.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },
    "anthracnose": {
        "High": (
            "⚠ URGENT — Severe Anthracnose Detected.\n\n"
            "1. Apply Carbendazim 50 WP @ 0.1% fungicide spray.\n"
            "2. Hot water treatment: immerse bunches at 52°C for 3 minutes.\n"
            "3. Store at 13–14°C with 90–95% relative humidity.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Moderate Anthracnose Detected.\n\n"
            "1. Apply Carbendazim fungicide spray.\n"
            "2. Use post-harvest hot water treatment @ 52°C for 3 minutes.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Minor Anthracnose Signs.\n\n"
            "1. Apply preventive Mancozeb 75 WP @ 0.2% during flowering.\n"
            "2. Ensure careful harvesting to minimise fruit wounds.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },
    "healthy": {
        "None": (
            "✅ Your banana plant appears HEALTHY!\n\n"
            "Continue good agricultural practices:\n"
            "1. Apply NPK @ 200:60:300 g per plant per year in 4 split doses.\n"
            "2. Maintain soil moisture at 70–75% field capacity; drip irrigation preferred.\n"
            "3. Scout weekly for early signs of Sigatoka, weevils, and BBTV.\n"
            "4. Remove dry and diseased leaves regularly.\n"
            "5. Retain only one ratoon sucker per mat.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },
}

_GENERIC_FALLBACK: dict[str, str] = {
    "High":   "⚠ URGENT: Severe disease detected. Contact your nearest ICAR-NRCB office immediately. Source: ICAR-NRCB, Trichy.",
    "Medium": "Moderate disease detected. Apply ICAR-recommended treatments and monitor every 3–5 days. Source: ICAR-NRCB, Trichy.",
    "Low":    "Mild symptoms detected. Continue monitoring and apply preventive treatments. Source: ICAR-NRCB, Trichy.",
    "None":   "Plant appears healthy. Maintain ICAR-recommended practices. Source: ICAR-NRCB, Trichy.",
}


class AdvisoryService:
    """
    Gemini LLM-powered ICAR advisory service.

    Primary:  Gemini 1.5 Flash → dynamic, contextual AI advisory
    Fallback: Hardcoded ICAR KB → reliable static advisory
    """

    def get_advisory(self, disease_name: str, severity: str) -> str:
        """
        Generate ICAR-aligned advisory using Gemini LLM.
        Falls back to hardcoded KB if Gemini fails.

        Args:
            disease_name: Detected banana disease label.
            severity:     Low, Medium, High, or None.

        Returns:
            Advisory string with actionable ICAR treatment steps.
        """
        # Try Gemini first
        advisory = self._get_gemini_advisory(disease_name, severity)

        if advisory:
            logger.info(
                "Gemini advisory generated for disease='%s' severity='%s'",
                disease_name, severity,
            )
            return advisory

        # Fallback to hardcoded KB
        logger.warning(
            "Gemini unavailable — using fallback KB for disease='%s' severity='%s'",
            disease_name, severity,
        )
        return self._get_fallback_advisory(disease_name, severity)

    def _get_gemini_advisory(self, disease_name: str, severity: str) -> str | None:
        """Call Gemini API to generate dynamic advisory."""
        try:
            model = _get_gemini_model()
            if model is None:
                return None

            prompt = f"""{_SYSTEM_PROMPT}

Generate a detailed ICAR-aligned treatment advisory for the following banana crop disease detection:

Disease Detected: {disease_name}
Severity Level: {severity}
Detection System: AgroGuard-AI (Deep Learning Model)
Guidelines: ICAR-NRCB, Trichy

Provide a structured, numbered advisory with:
- Immediate actions required
- Specific chemical treatments with exact dosages
- Biological control options
- Preventive measures
- Monitoring schedule

Keep it practical for Indian banana farmers."""

            response = model.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            if response and response.text:
                return response.text.strip()

            return None

        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            return None

    def _get_fallback_advisory(self, disease_name: str, severity: str) -> str:
        """Return hardcoded ICAR advisory as fallback."""
        disease_lower = disease_name.lower()

        for keyword, severity_map in _FALLBACK_KB.items():
            if keyword in disease_lower:
                advice = severity_map.get(severity, _GENERIC_FALLBACK.get(severity, ""))
                logger.info("Fallback KB matched keyword='%s' severity='%s'", keyword, severity)
                return advice

        return _GENERIC_FALLBACK.get(severity, "No advisory available.")