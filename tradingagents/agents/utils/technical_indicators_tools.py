from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

# Aliases for common LLM hallucinations → correct indicator keys
_INDICATOR_ALIASES = {
    "macd_histogram": "macdh",
    "macd_hist": "macdh",
    "macdhistogram": "macdh",
    "macd_signal": "macds",
    "macdsignal": "macds",
    "sma_50": "close_50_sma",
    "sma50": "close_50_sma",
    "50_sma": "close_50_sma",
    "sma_200": "close_200_sma",
    "sma200": "close_200_sma",
    "200_sma": "close_200_sma",
    "ema_10": "close_10_ema",
    "ema10": "close_10_ema",
    "10_ema": "close_10_ema",
    "bollinger_middle": "boll",
    "bollinger_upper": "boll_ub",
    "bollinger_lower": "boll_lb",
    "boll_middle": "boll",
    "bb_upper": "boll_ub",
    "bb_lower": "boll_lb",
    "bb_middle": "boll",
    "average_true_range": "atr",
    "money_flow_index": "mfi",
    "volume_weighted_ma": "vwma",
    "vwap": "vwma",
}


def _normalize_indicator(indicator: str) -> str:
    """Normalize an indicator name, resolving known LLM aliases."""
    normalized = indicator.strip().lower()
    return _INDICATOR_ALIASES.get(normalized, normalized)


@tool
def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
) -> str:
    """
    Retrieve a single technical indicator for a given ticker symbol.
    Uses the configured technical_indicators vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): A single technical indicator name, e.g. 'rsi', 'macd'. Call this tool once per indicator.
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
    Returns:
        str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.
    """
    # LLMs sometimes pass multiple indicators as a comma-separated string;
    # split and process each individually.
    indicators = [_normalize_indicator(i) for i in indicator.split(",") if i.strip()]
    if len(indicators) > 1:
        results = []
        for ind in indicators:
            results.append(route_to_vendor("get_indicators", symbol, ind, curr_date, look_back_days))
        return "\n\n".join(results)
    return route_to_vendor("get_indicators", symbol, _normalize_indicator(indicator), curr_date, look_back_days)