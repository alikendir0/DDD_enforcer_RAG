"""Model pricing configuration for cost estimation."""

# Pricing per 1 million tokens in USD
# Source: Google AI pricing (as of December 2025)
MODEL_PRICING = {
    "gemini-2.5-flash": {
        "input_price_per_million": 0.0,  # Free tier
        "output_price_per_million": 0.0   # Free tier
    },
}


def get_model_price(model_name: str) -> dict:
    """Get pricing for a specific model.

    Args:
        model_name: AI model identifier (e.g., "gemini-2.5-flash")

    Returns:
        Dictionary with input_price_per_million and output_price_per_million.
        Returns $0.00 pricing if model not found (assumes free tier).
    """
    return MODEL_PRICING.get(model_name, {
        "input_price_per_million": 0.0,
        "output_price_per_million": 0.0
    })
