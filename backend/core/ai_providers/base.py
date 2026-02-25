from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List


@dataclass
class AnalysisContext:
    """
    Serializable context object passed to AI providers.
    Stored in AIRecommendation.analysis_data for audit/replay.
    """
    portfolio_id: int
    symbol: str
    asset_type: str

    # Portfolio state
    cash_balance: float
    total_portfolio_value: float
    risk_tolerance: str  # LOW | MEDIUM | HIGH
    max_position_size_pct: float

    # Price
    current_price: float
    price_change_pct_1d: float

    # Technical indicators
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    volume_avg: Optional[float] = None

    # Fundamentals
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    market_cap: Optional[int] = None
    dividend_yield: Optional[float] = None
    sector: Optional[str] = None

    # News sentiment
    news_sentiment_score: Optional[float] = None  # -1.0 to 1.0
    news_headlines: List[str] = field(default_factory=list)

    # Current position (if any)
    current_position_qty: float = 0.0
    current_position_avg_cost: float = 0.0
    current_position_pnl_pct: float = 0.0

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


@dataclass
class RecommendationData:
    """Structured output from an AI provider."""
    action: str  # BUY | SELL | HOLD | REBALANCE
    confidence: float  # 0.0 to 1.0
    quantity_suggested: float
    price_target: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reasoning: str
    raw_response: str = ""


class BaseAIProvider(ABC):
    """
    Abstract AI provider (Strategy pattern).
    Each concrete class wraps one AI model (Claude, OpenAI, Gemini).
    """

    provider_name: str = "unknown"

    @abstractmethod
    def analyze(self, context: AnalysisContext) -> RecommendationData:
        """
        Analyze market context and return a trading recommendation.
        Raises an exception if the AI call fails.
        """
        ...

    def build_prompt(self, context: AnalysisContext) -> str:
        """Build the analysis prompt. Shared by all providers."""
        max_position_value = context.total_portfolio_value * (context.max_position_size_pct / 100)
        max_qty = int(max_position_value / context.current_price) if context.current_price > 0 else 0

        news_text = ""
        if context.news_headlines:
            news_text = "\n".join(f"  - {h}" for h in context.news_headlines[:5])
            sentiment_label = (
                "POSITIVE" if (context.news_sentiment_score or 0) > 0.2
                else "NEGATIVE" if (context.news_sentiment_score or 0) < -0.2
                else "NEUTRAL"
            )
            news_text = (
                f"\nNEWS SENTIMENT (last 24h): {sentiment_label} "
                f"({context.news_sentiment_score:.2f})\n{news_text}"
            )

        position_text = ""
        if context.current_position_qty > 0:
            position_text = (
                f"\nCURRENT POSITION: {context.current_position_qty} shares "
                f"@ ${context.current_position_avg_cost:.2f} avg cost "
                f"(P&L: {context.current_position_pnl_pct:+.1f}%)"
            )
        else:
            position_text = "\nCURRENT POSITION: None"

        return f"""You are an expert stock analyst and portfolio manager helping a beginner investor.
Be conservative, educational in your reasoning, and always prioritize capital preservation.

PORTFOLIO STATE:
- Cash available: ${context.cash_balance:,.2f}
- Total portfolio value: ${context.total_portfolio_value:,.2f}
- Risk tolerance: {context.risk_tolerance}
- Max position size: {context.max_position_size_pct}% of portfolio (max ~{max_qty} shares)
{position_text}

ANALYSIS FOR: {context.symbol} ({context.asset_type})
Current price: ${context.current_price:.2f} ({context.price_change_pct_1d:+.2f}% today)

TECHNICAL INDICATORS:
- RSI(14): {context.rsi_14 or 'N/A'}{' (oversold <30)' if context.rsi_14 and context.rsi_14 < 30 else ' (overbought >70)' if context.rsi_14 and context.rsi_14 > 70 else ''}
- MACD: {context.macd or 'N/A'} | Signal: {context.macd_signal or 'N/A'} | Histogram: {context.macd_histogram or 'N/A'}
- Bollinger Bands: Upper={context.bb_upper or 'N/A'} | Mid={context.bb_middle or 'N/A'} | Lower={context.bb_lower or 'N/A'}
- EMA 20/50/200: {context.ema_20 or 'N/A'} / {context.ema_50 or 'N/A'} / {context.ema_200 or 'N/A'}

FUNDAMENTALS:
- P/E ratio: {context.pe_ratio or 'N/A'}
- EPS: {context.eps or 'N/A'}
- Market Cap: ${context.market_cap:,} if {context.market_cap} else N/A
- Dividend Yield: {f'{context.dividend_yield:.2%}' if context.dividend_yield else 'N/A'}
- Sector: {context.sector or 'N/A'}
{news_text}

Respond ONLY with valid JSON, no markdown, no explanation outside JSON:
{{
  "action": "BUY" | "SELL" | "HOLD" | "REBALANCE",
  "confidence": <float 0.0-1.0>,
  "quantity_suggested": <integer, max {max_qty}>,
  "price_target": <float or null>,
  "stop_loss": <float or null>,
  "take_profit": <float or null>,
  "reasoning": "<1-3 sentences explaining your recommendation in simple terms>"
}}"""
