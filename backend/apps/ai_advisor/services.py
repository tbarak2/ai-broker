"""
AI Advisor service — orchestrates multi-model analysis.

Flow:
  1. Build AnalysisContext from market data + portfolio state
  2. Call each configured AI provider
  3. Persist AIRecommendation records
  4. Fire recommendation_created signal (→ Telegram notification)
"""
import logging
from decimal import Decimal
from typing import List, Optional

from django.utils import timezone

from core.ai_providers.base import AnalysisContext
from core.ai_providers.factory import AIProviderFactory
from core.events.signals import recommendation_created

from .models import AIRecommendation, StrategyConfig

logger = logging.getLogger(__name__)


class AIAdvisorService:
    def build_context(
        self,
        portfolio,
        symbol: str,
        strategy_config: StrategyConfig,
    ) -> AnalysisContext:
        """Assemble AnalysisContext from market data + portfolio state."""
        from apps.market_data.services import MarketDataService

        mkt = MarketDataService()

        # Price data
        try:
            price_data = mkt.get_price_data(symbol)
            current_price = float(price_data.price)
            price_change_pct = price_data.change_pct
        except Exception as exc:
            logger.warning("Could not fetch price for %s: %s", symbol, exc)
            current_price = 1.0
            price_change_pct = 0.0

        # Technical indicators from historical OHLCV
        rsi, macd_val, macd_signal, macd_hist = None, None, None, None
        bb_upper, bb_middle, bb_lower = None, None, None
        ema20, ema50, ema200 = None, None, None
        vol_avg = None

        try:
            df = mkt.get_historical_ohlcv(symbol, "90d")
            if not df.empty and len(df) >= 14:
                import ta
                df["close"] = df["close"].astype(float)
                df["volume"] = df["volume"].astype(float)

                rsi = float(ta.momentum.RSIIndicator(df["close"], window=14).rsi().iloc[-1])

                macd_ind = ta.trend.MACD(df["close"])
                macd_val = float(macd_ind.macd().iloc[-1])
                macd_signal = float(macd_ind.macd_signal().iloc[-1])
                macd_hist = float(macd_ind.macd_diff().iloc[-1])

                bb = ta.volatility.BollingerBands(df["close"])
                bb_upper = float(bb.bollinger_hband().iloc[-1])
                bb_middle = float(bb.bollinger_mavg().iloc[-1])
                bb_lower = float(bb.bollinger_lband().iloc[-1])

                ema20 = float(ta.trend.EMAIndicator(df["close"], window=20).ema_indicator().iloc[-1])
                ema50 = float(ta.trend.EMAIndicator(df["close"], window=50).ema_indicator().iloc[-1])
                if len(df) >= 200:
                    ema200 = float(ta.trend.EMAIndicator(df["close"], window=200).ema_indicator().iloc[-1])

                vol_avg = float(df["volume"].rolling(20).mean().iloc[-1])
        except Exception as exc:
            logger.warning("Indicator computation failed for %s: %s", symbol, exc)

        # Fundamentals
        pe_ratio, eps, market_cap, div_yield, sector = None, None, None, None, None
        try:
            fund = mkt.get_fundamentals(symbol)
            pe_ratio = fund.pe_ratio
            eps = fund.eps
            market_cap = fund.market_cap
            div_yield = fund.dividend_yield
            sector = fund.sector
        except Exception:
            pass

        # News sentiment
        news_score = None
        headlines: List[str] = []
        try:
            news_items = mkt.get_news(symbol, limit=10)
            if news_items:
                scores = [
                    float(n.sentiment_score)
                    for n in news_items
                    if n.sentiment_score is not None
                ]
                if scores:
                    news_score = sum(scores) / len(scores)
                headlines = [n.headline for n in news_items[:5]]
        except Exception:
            pass

        # Current position
        position_qty = 0.0
        position_avg_cost = 0.0
        position_pnl_pct = 0.0
        try:
            from apps.portfolio.repositories import PortfolioRepository
            repo = PortfolioRepository()
            pos = repo.get_position(portfolio.id, symbol)
            if pos and pos.quantity > 0:
                position_qty = float(pos.quantity)
                position_avg_cost = float(pos.avg_cost_price)
                if position_avg_cost > 0:
                    position_pnl_pct = (current_price - position_avg_cost) / position_avg_cost * 100
        except Exception:
            pass

        return AnalysisContext(
            portfolio_id=portfolio.id,
            symbol=symbol,
            asset_type="STOCK",
            cash_balance=float(portfolio.cash_balance),
            total_portfolio_value=float(portfolio.total_value),
            risk_tolerance=strategy_config.risk_tolerance,
            max_position_size_pct=float(strategy_config.max_position_size_pct),
            current_price=current_price,
            price_change_pct_1d=price_change_pct,
            rsi_14=rsi,
            macd=macd_val,
            macd_signal=macd_signal,
            macd_histogram=macd_hist,
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower,
            ema_20=ema20,
            ema_50=ema50,
            ema_200=ema200,
            volume_avg=vol_avg,
            pe_ratio=pe_ratio,
            eps=eps,
            market_cap=market_cap,
            dividend_yield=div_yield,
            sector=sector,
            news_sentiment_score=news_score,
            news_headlines=headlines,
            current_position_qty=position_qty,
            current_position_avg_cost=position_avg_cost,
            current_position_pnl_pct=position_pnl_pct,
        )

    def analyze_symbol(
        self,
        portfolio,
        symbol: str,
        strategy_config: StrategyConfig,
    ) -> List[AIRecommendation]:
        """Run all configured AI providers against one symbol."""
        context = self.build_context(portfolio, symbol, strategy_config)
        recommendations = []

        for provider_name in (strategy_config.ai_providers or ["claude"]):
            try:
                provider = AIProviderFactory.create(provider_name)
                rec_data = provider.analyze(context)

                # Calculate expiry (2x analysis interval)
                expiry_minutes = strategy_config.analysis_interval_minutes * 2
                expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)

                rec = AIRecommendation.objects.create(
                    portfolio=portfolio,
                    provider=provider_name.upper(),
                    symbol=symbol,
                    action=rec_data.action,
                    confidence=Decimal(str(round(rec_data.confidence, 3))),
                    quantity_suggested=Decimal(str(rec_data.quantity_suggested)),
                    price_target=Decimal(str(rec_data.price_target)) if rec_data.price_target else None,
                    stop_loss=Decimal(str(rec_data.stop_loss)) if rec_data.stop_loss else None,
                    take_profit=Decimal(str(rec_data.take_profit)) if rec_data.take_profit else None,
                    reasoning=rec_data.reasoning,
                    analysis_data=context.to_dict(),
                    expires_at=expires_at,
                )
                recommendation_created.send(
                    sender=self.__class__, recommendation=rec
                )
                recommendations.append(rec)
                logger.info(
                    "[%s] %s %s → %s (%.0f%% confidence)",
                    provider_name, rec.action, symbol,
                    rec.reasoning[:60], float(rec.confidence) * 100,
                )
            except Exception as exc:
                logger.error(
                    "AI analysis failed for %s/%s: %s", provider_name, symbol, exc
                )

        return recommendations

    def run_full_analysis(self, portfolio_id: int) -> List[AIRecommendation]:
        """Analyze all watchlist symbols for a portfolio."""
        from apps.portfolio.models import Portfolio

        portfolio = Portfolio.objects.get(id=portfolio_id)
        try:
            config = StrategyConfig.objects.get(portfolio=portfolio)
        except StrategyConfig.DoesNotExist:
            logger.warning("No StrategyConfig for portfolio %s", portfolio_id)
            return []

        all_recs = []
        for symbol in (config.watchlist or []):
            recs = self.analyze_symbol(portfolio, symbol.upper(), config)
            all_recs.extend(recs)

        return all_recs

    def approve_recommendation(self, rec_id: int) -> AIRecommendation:
        """Approve a recommendation — creates an AI-sourced order."""
        from apps.trading.services import TradingService

        rec = AIRecommendation.objects.get(id=rec_id)
        if rec.status != AIRecommendation.Status.PENDING:
            raise ValueError(f"Recommendation {rec_id} is not PENDING")

        rec.status = AIRecommendation.Status.APPROVED
        rec.save(update_fields=["status"])

        if rec.action in ("BUY", "SELL") and rec.quantity_suggested > 0:
            trading_svc = TradingService()
            order = trading_svc.create_ai_order(
                portfolio_id=rec.portfolio_id,
                symbol=rec.symbol,
                side=rec.action,
                quantity=rec.quantity_suggested,
                ai_recommendation_id=rec.id,
                asset_type=rec.asset_type,
            )
            trading_svc.approve_order(order.id)
            rec.status = AIRecommendation.Status.EXECUTED
            rec.save(update_fields=["status"])

        return rec

    def reject_recommendation(self, rec_id: int) -> AIRecommendation:
        rec = AIRecommendation.objects.get(id=rec_id)
        if rec.status != AIRecommendation.Status.PENDING:
            raise ValueError(f"Recommendation {rec_id} is not PENDING")
        rec.status = AIRecommendation.Status.REJECTED
        rec.save(update_fields=["status"])
        return rec

    def expire_old_recommendations(self) -> int:
        """Mark all PENDING recommendations past their expiry as EXPIRED."""
        now = timezone.now()
        count = AIRecommendation.objects.filter(
            status=AIRecommendation.Status.PENDING,
            expires_at__lt=now,
        ).update(status=AIRecommendation.Status.EXPIRED)
        logger.info("Expired %d recommendations", count)
        return count
