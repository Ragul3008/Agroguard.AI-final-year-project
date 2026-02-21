"""
services/advisory_service.py - ICAR-aligned agricultural advisory for banana diseases.

Advisory content is keyed on disease keywords and severity levels.
All recommendations follow ICAR (Indian Council of Agricultural Research)
guidelines for banana plantation management.
"""

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Banana Disease Advisory Knowledge Base
# Aligned with ICAR guidelines for banana crop protection.
# ---------------------------------------------------------------------------
_ADVISORY_KB: dict[str, dict[str, str]] = {

    # ── Panama Disease (Fusarium Wilt) ─────────────────────────────────────
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
            "Source: ICAR–National Research Centre for Banana (NRCB), Trichy."
        ),
        "Medium": (
            "Panama Disease (Fusarium Wilt) — Moderate Signs Detected.\n\n"
            "1. Remove and burn all wilting or yellowing plants.\n"
            "2. Apply Trichoderma viride @ 25 g per plant in the root zone.\n"
            "3. Avoid overhead irrigation; use drip irrigation to reduce soil moisture spread.\n"
            "4. Disinfect all farm tools with 2% formaldehyde solution.\n"
            "5. Monitor neighbouring plants every 3 days.\n"
            "6. Contact your local horticulture officer for soil testing.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Early Panama Disease Indicators — Remain Vigilant.\n\n"
            "1. Improve field drainage; avoid waterlogging at the root zone.\n"
            "2. Apply Pseudomonas fluorescens @ 2 kg/ha as a soil drench.\n"
            "3. Avoid injuring roots during weeding or intercultural operations.\n"
            "4. Scout the plantation weekly for yellowing lower leaves.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },

    # ── Black Sigatoka ─────────────────────────────────────────────────────
    "black sigatoka": {
        "High": (
            "⚠ URGENT — Severe Black Sigatoka Detected.\n\n"
            "1. Remove and burn all heavily infected leaves immediately.\n"
            "2. Apply systemic fungicide: Propiconazole 25 EC @ 0.1% OR "
            "Trifloxystrobin + Tebuconazole @ 0.05% at 10-day intervals.\n"
            "3. Alternate fungicide groups each spray cycle to prevent resistance "
            "(ICAR recommendation).\n"
            "4. Ensure plant spacing of at least 1.8 × 1.8 m for adequate airflow.\n"
            "5. Apply copper oxychloride @ 0.2% as a protective spray on remaining leaves.\n"
            "6. Avoid overhead irrigation; use drip irrigation.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Moderate Black Sigatoka Detected.\n\n"
            "1. Remove lower infected leaves (leaf stripping) and destroy them.\n"
            "2. Apply Mancozeb 75 WP @ 0.2% fungicide spray.\n"
            "3. Improve canopy ventilation by thinning excess suckers.\n"
            "4. Maintain recommended fertiliser schedule (especially potassium).\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Early Black Sigatoka Signs Observed.\n\n"
            "1. Apply preventive copper-based fungicide spray.\n"
            "2. Improve air circulation by removing dry leaf sheaths.\n"
            "3. Ensure balanced NPK fertilisation to boost plant immunity.\n"
            "4. Monitor weekly; remove leaves showing streak symptoms.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },

    # ── Yellow Sigatoka ────────────────────────────────────────────────────
    "yellow sigatoka": {
        "High": (
            "⚠ URGENT — Severe Yellow Sigatoka Detected.\n\n"
            "1. Remove all leaves with more than 50% lesion coverage immediately.\n"
            "2. Apply Carbendazim 50 WP @ 0.1% OR Propiconazole 25 EC @ 0.1% fungicide.\n"
            "3. Spray at 14-day intervals during the wet season.\n"
            "4. Apply Bordeaux mixture (1%) on remaining healthy leaves as a protectant.\n"
            "5. Ensure proper drainage across the plantation.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Moderate Yellow Sigatoka Detected.\n\n"
            "1. Carry out regular leaf pruning to remove infected material.\n"
            "2. Apply Mancozeb 75 WP @ 0.25% as a foliar spray.\n"
            "3. Reduce plant density; maintain adequate spacing.\n"
            "4. Apply balanced potassium fertilisation to strengthen leaf tissue.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Early Yellow Sigatoka Signs.\n\n"
            "1. Preventive spray with copper oxychloride @ 0.3%.\n"
            "2. Remove and destroy dry, infected leaf litter from the field.\n"
            "3. Maintain adequate drainage to keep leaves dry.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },

    # ── Pseudostem Weevil ──────────────────────────────────────────────────
    "weevil": {
        "High": (
            "⚠ URGENT — Severe Pseudostem Weevil Infestation Detected.\n\n"
            "1. Apply Carbofuran 3G granules @ 40 g per plant at the pseudostem base.\n"
            "2. Remove and destroy all heavily infested plants to reduce population.\n"
            "3. Install pheromone traps (Aggregation pheromone — Odoiporus longicollis) "
            "@ 10 traps per hectare for mass trapping per ICAR protocol.\n"
            "4. Apply Chlorpyrifos 20 EC @ 2.5 ml/litre as a pseudostem drench.\n"
            "5. Remove dry leaf sheaths from pseudostems to eliminate breeding sites.\n"
            "6. Avoid ratoon cropping in heavily infested fields.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Moderate Pseudostem Weevil Infestation.\n\n"
            "1. Apply Carbofuran 3G @ 25 g per plant in the stem collar region.\n"
            "2. Install pheromone traps @ 5 traps per hectare.\n"
            "3. Remove dry leaf sheaths and maintain field hygiene.\n"
            "4. Apply Entomopathogenic nematodes (Steinernema carpocapsae) "
            "as a biological control option per ICAR recommendation.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Minor Pseudostem Weevil Activity.\n\n"
            "1. Maintain field sanitation — remove dead plant material and dry sheaths.\n"
            "2. Install 2–3 pheromone traps per hectare for early monitoring.\n"
            "3. Apply preventive Chlorpyrifos drench at planting time.\n"
            "4. Use healthy, weevil-free planting material.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },

    # ── Bunchy Top Virus (BBTV) ────────────────────────────────────────────
    "bunchy": {
        "High": (
            "⚠ URGENT — Banana Bunchy Top Virus (BBTV) Confirmed.\n\n"
            "There is NO chemical cure for viral diseases. Immediate action required:\n"
            "1. Uproot, chop, and destroy ALL infected plants (burning preferred) — "
            "do NOT leave any part in the field as the virus persists.\n"
            "2. Control the aphid vector (Pentalonia nigronervosa) on remaining plants:\n"
            "   - Apply Imidacloprid 17.8 SL @ 0.3 ml/litre foliar spray.\n"
            "   - Apply Thiamethoxam 25 WG @ 0.3 g/litre as a soil drench.\n"
            "3. Establish a 50-metre buffer zone — remove volunteer banana plants.\n"
            "4. Use ONLY certified virus-free TC (tissue culture) planting material "
            "for replanting.\n"
            "5. Report the outbreak to ICAR-NRCB or the State Horticulture Department.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Banana Bunchy Top Virus (BBTV) — Moderate Infection Detected.\n\n"
            "1. Rogue out all plants showing clear BBTV symptoms and destroy immediately.\n"
            "2. Apply Imidacloprid 17.8 SL @ 0.5 ml/litre to control aphid vectors.\n"
            "3. Remove nearby weed hosts that may harbour the aphid vector.\n"
            "4. Survey surrounding plots — BBTV spreads rapidly through aphid colonies.\n"
            "5. Replace removed plants with certified virus-free TC planting material.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Early BBTV Symptoms Suspected.\n\n"
            "1. Inspect plants carefully for marginal chlorosis and narrow upright leaves.\n"
            "2. Control aphid populations with Imidacloprid spray.\n"
            "3. Remove and destroy any symptomatic plants immediately.\n"
            "4. Source only certified virus-free suckers or TC plants for new planting.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },

    # ── Anthracnose ────────────────────────────────────────────────────────
    "anthracnose": {
        "High": (
            "⚠ URGENT — Severe Anthracnose Detected (Colletotrichum musae).\n\n"
            "1. Apply Carbendazim 50 WP @ 0.1% OR Mancozeb 75 WP @ 0.2% fungicide spray.\n"
            "2. Apply post-harvest hot water treatment: immerse fruit bunches in water "
            "at 52°C for 3 minutes (ICAR-recommended).\n"
            "3. Harvest bunches at correct maturity index (75–80% finger filling) "
            "to reduce post-harvest susceptibility.\n"
            "4. Handle fruit carefully to prevent wounds — wounds are the primary "
            "infection site.\n"
            "5. Store and transport at 13–14°C with 90–95% relative humidity.\n"
            "6. Treat harvested bunches with Thiabendazole dip solution.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Medium": (
            "Moderate Anthracnose Detected.\n\n"
            "1. Apply Carbendazim fungicide spray on bunches during the flower-to-harvest stage.\n"
            "2. Use post-harvest hot water treatment @ 52°C for 3 minutes.\n"
            "3. Avoid mechanical damage during harvesting and transportation.\n"
            "4. Ensure proper cold chain storage.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
        "Low": (
            "Minor Anthracnose Signs Detected.\n\n"
            "1. Apply preventive Mancozeb 75 WP @ 0.2% spray during flowering stage.\n"
            "2. Ensure careful harvesting to minimise fruit wounds.\n"
            "3. Maintain cold storage to slow pathogen development.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },

    # ── Healthy Plant ──────────────────────────────────────────────────────
    "healthy": {
        "None": (
            "✅ Your banana plant appears HEALTHY!\n\n"
            "Continue good agricultural practices:\n"
            "1. Fertilisation: Apply NPK @ 200:60:300 g per plant per year in "
            "4 split doses as per ICAR recommendation.\n"
            "2. Irrigation: Maintain soil moisture at 70–75% field capacity; "
            "drip irrigation preferred.\n"
            "3. Pest scouting: Scout weekly for early signs of Sigatoka, weevils, "
            "and BBTV symptoms.\n"
            "4. De-leafing: Remove dry and diseased leaves regularly to improve "
            "air circulation and reduce disease inoculum.\n"
            "5. Sucker management: Retain only one ratoon sucker per mat.\n\n"
            "Source: ICAR-NRCB, Trichy."
        ),
    },
}

# Generic fallback advisory when no keyword matches
_GENERIC_ADVISORY: dict[str, str] = {
    "High": (
        "⚠ URGENT: Severe banana disease detected. Consult your nearest ICAR-NRCB "
        "extension officer or State Horticulture Department immediately. "
        "Apply appropriate crop-protection products and isolate affected plants."
    ),
    "Medium": (
        "Moderate disease severity detected on your banana plant. Apply recommended "
        "pesticide or fungicide per ICAR guidelines, improve field sanitation, "
        "and monitor the crop every 3–5 days."
    ),
    "Low": (
        "Mild disease symptoms detected. Continue regular monitoring, apply preventive "
        "treatments as per ICAR guidelines, and maintain good field hygiene."
    ),
    "None": (
        "Your banana plant appears healthy. Maintain current ICAR-recommended practices "
        "and scout regularly for early disease signs."
    ),
}


class AdvisoryService:
    """Generates ICAR-aligned treatment advice for banana disease detections."""

    def get_advisory(self, disease_name: str, severity: str) -> str:
        """
        Return structured advisory text for the detected disease and severity.

        Args:
            disease_name: Human-readable banana disease label.
            severity:     One of "Low", "Medium", "High", or "None".

        Returns:
            Advisory string with actionable treatment steps.
        """
        disease_lower = disease_name.lower()

        # Search knowledge base for a matching keyword
        for keyword, severity_map in _ADVISORY_KB.items():
            if keyword in disease_lower:
                advice = severity_map.get(severity, _GENERIC_ADVISORY.get(severity, ""))
                logger.info(
                    "Advisory matched keyword='%s' severity='%s'", keyword, severity
                )
                return advice

        # Fall back to generic advice
        advice = _GENERIC_ADVISORY.get(severity, "No advisory available.")
        logger.info(
            "Advisory fallback used for disease='%s' severity='%s'",
            disease_name,
            severity,
        )
        return advice
