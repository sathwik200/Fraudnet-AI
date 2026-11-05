"""
FRAUDNET AI — Evidence-Based AML Typology Classifier
=====================================================
Classifies cryptocurrency transaction topological patterns strictly based on
concrete structural evidence from directed graph analytics.

Guiding Principles:
  1. Never assign specific typologies (e.g. peeling, mixing, arbitrage) without
     verifiable, concrete topological evidence.
  2. If structural evidence is insufficient or ambiguous, explicitly report:
     "Insufficient evidence to determine transaction typology."
  3. Every assigned typology must be accompanied by explicit supporting graph
     observations (in-degree, out-degree, fan-in/fan-out ratios, hub status).
"""

from typing import Any, Dict


def classify_aml_typology(
    in_degree: int,
    out_degree: int,
    is_aggregation_hub: bool = False,
    is_distribution_hub: bool = False,
    clustering_coeff: float = 0.0,
) -> Dict[str, Any]:
    """
    Classify transaction topology into an evidence-based AML structural pattern.

    Args:
        in_degree: Number of incoming directed inputs in the temporal partition.
        out_degree: Number of outgoing directed outputs in the temporal partition.
        is_aggregation_hub: True if transaction exceeds partition 99th percentile fan-in.
        is_distribution_hub: True if transaction exceeds partition 99th percentile fan-out.
        clustering_coeff: Local directed clustering coefficient.

    Returns:
        Dict containing:
            - typology: Human-readable typology title.
            - confidence: High, Moderate, or Low.
            - evidence_sufficient: bool indicating whether evidence supports a specific typology.
            - supporting_observations: Concrete graph metrics supporting the determination.
            - compliance_note: Forensic context for AML investigators.
    """
    in_deg = max(0, int(in_degree))
    out_deg = max(0, int(out_degree))

    # Case 1: High Fan-In Aggregation Hub (Consolidation)
    if (in_deg >= 10 and out_deg <= 2) or (is_aggregation_hub and in_deg >= 5 and out_deg <= 2):
        fan_in_ratio = in_deg / max(1, out_deg)
        return {
            "typology": "High Fan-In Aggregation Hub",
            "confidence": "High" if in_deg >= 20 else "Moderate",
            "evidence_sufficient": True,
            "supporting_observations": (
                f"Significant fan-in concentration with {in_deg} upstream inputs consolidating into {out_deg} "
                f"output(s) (fan-in ratio: {fan_in_ratio:.1f}x). "
                f"{'Exceeds 99th percentile aggregation hub threshold.' if is_aggregation_hub else 'High structural fan-in.'}"
            ),
            "compliance_note": (
                "Pattern exhibits structural characteristics typical of payment aggregation, merchant settlement, "
                "or deposit consolidation. Recommend auditing source counterparties for fund origin."
            ),
        }

    # Case 2: High Fan-Out Distribution Hub (Dispersal)
    if (out_deg >= 10 and in_deg <= 2) or (is_distribution_hub and out_deg >= 5 and in_deg <= 2):
        fan_out_ratio = out_deg / max(1, in_deg)
        return {
            "typology": "High Fan-Out Distribution Hub",
            "confidence": "High" if out_deg >= 20 else "Moderate",
            "evidence_sufficient": True,
            "supporting_observations": (
                f"Significant fan-out dispersal with {out_deg} downstream outputs originating from {in_deg} "
                f"input(s) (fan-out ratio: {fan_out_ratio:.1f}x). "
                f"{'Exceeds 99th percentile distribution hub threshold.' if is_distribution_hub else 'High structural fan-out.'}"
            ),
            "compliance_note": (
                "Pattern exhibits structural characteristics typical of exchange batch withdrawals, payout pools, "
                "or rapid dispersal. Recommend verifying destination counterparties against known exchange clusters."
            ),
        }

    # Case 3: Direct Point-to-Point Transfer (Single Input / Single Output)
    if in_deg == 1 and out_deg == 1:
        return {
            "typology": "Direct Point-to-Point Transfer",
            "confidence": "Moderate",
            "evidence_sufficient": True,
            "supporting_observations": (
                "Standard 1-in / 1-out transaction flow. Connectivity does not exhibit structural fan-in, "
                "fan-out, or multi-party pooling."
            ),
            "compliance_note": (
                "Single sequential transfer. Note: 1-to-1 connectivity alone possesses insufficient structural "
                "complexity to establish an AML layering or mixing typology without independent off-chain intelligence."
            ),
        }

    # Case 4: Multi-Input Multi-Output Joint Settlement
    if in_deg >= 3 and out_deg >= 3 and (in_deg + out_deg >= 8):
        return {
            "typology": "Multi-Input Multi-Output Joint Settlement",
            "confidence": "Moderate",
            "evidence_sufficient": True,
            "supporting_observations": (
                f"Complex multi-party transaction with {in_deg} inputs and {out_deg} outputs. "
                f"Local clustering coefficient: {clustering_coeff:.4f}."
            ),
            "compliance_note": (
                "Structure is consistent with multi-party co-spending, joint liquidity settlement, or CoinJoin/mixing pools. "
                "Detailed UTXO denomination matching required to confirm privacy-preserving protocols."
            ),
        }

    # Case 5: Insufficient Structural Evidence (Default fallback)
    return {
        "typology": "Insufficient evidence to determine transaction typology",
        "confidence": "Low",
        "evidence_sufficient": False,
        "supporting_observations": (
            f"Observed graph connectivity ({in_deg} incoming input(s), {out_deg} outgoing output(s)) does not "
            f"exhibit distinctive topological concentration, dispersal, or clustering required to establish an AML pattern."
        ),
        "compliance_note": (
            "No specific money-laundering typology can be reliably attributed based solely on local graph metrics. "
            "Rely on supervised machine learning feature attributions and independent blockchain corroboration."
        ),
    }

