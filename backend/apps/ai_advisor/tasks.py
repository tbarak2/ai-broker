"""Celery tasks for the AI advisor app."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="ai_advisor.run_ai_analysis")
def run_ai_analysis(portfolio_id: int):
    """Run full AI analysis cycle for a portfolio."""
    from .services import AIAdvisorService
    svc = AIAdvisorService()
    recs = svc.run_full_analysis(portfolio_id)
    logger.info(
        "AI analysis complete for portfolio %s: %d recommendations",
        portfolio_id, len(recs),
    )
    return {"portfolio_id": portfolio_id, "recommendations": len(recs)}


@shared_task(name="ai_advisor.run_analysis_all_portfolios")
def run_analysis_all_portfolios():
    """Trigger AI analysis for all portfolios with active strategy configs."""
    from .models import StrategyConfig
    count = 0
    for config in StrategyConfig.objects.filter(is_active=True):
        run_ai_analysis.delay(config.portfolio_id)
        count += 1
    return {"queued": count}


@shared_task(name="ai_advisor.expire_old_recommendations")
def expire_old_recommendations():
    """Mark stale PENDING recommendations as EXPIRED."""
    from .services import AIAdvisorService
    count = AIAdvisorService().expire_old_recommendations()
    return {"expired": count}
