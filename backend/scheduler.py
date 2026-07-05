"""
backend/scheduler.py
====================
Scheduler en segundo plano (APScheduler). Mientras el backend esté arrancado,
refresca precios y evalúa alertas periódicamente, aunque la web no esté abierta.

Esto cubre la opción "app + tareas programadas": el trabajo recurrente vive en
el propio backend. Además, los endpoints `/api/jobs/*` permiten dispararlo a
mano o desde una tarea programada externa (p. ej. el programador de Cowork o el
Task Scheduler de Windows llamando por HTTP).
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from backend.config import (
    PRICE_REFRESH_MINUTES, ALERT_CHECK_MINUTES, NEWS_REFRESH_MINUTES, SUGGESTION_HOUR,
)
from backend.db import session_scope
from backend.services import portfolio as portfolio_svc
from backend.services import alerts_engine
from backend.services import news_store
from backend.services import suggest

logger = logging.getLogger("market_hub.scheduler")
_scheduler: BackgroundScheduler | None = None


def job_refresh_prices():
    with session_scope() as s:
        res = portfolio_svc.refresh_prices(s)
        portfolio_svc.write_snapshot(s)
    logger.info("refresh_prices: %s", res)


def job_check_alerts():
    with session_scope() as s:
        res = alerts_engine.evaluate_all(s)
    logger.info("check_alerts: %s", res)


def job_refresh_news():
    with session_scope() as s:
        res = news_store.refresh_news(s)
    logger.info("refresh_news: %s", res)


def job_daily_suggestion():
    with session_scope() as s:
        suggest.generate(s, period="daily")
    logger.info("daily_suggestion generada")


def job_weekly_suggestion():
    with session_scope() as s:
        suggest.generate(s, period="weekly")
    logger.info("weekly_suggestion generada")


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler:
        return _scheduler
    sch = BackgroundScheduler(daemon=True)
    sch.add_job(job_refresh_prices, "interval", minutes=PRICE_REFRESH_MINUTES,
                id="refresh_prices", replace_existing=True)
    sch.add_job(job_check_alerts, "interval", minutes=ALERT_CHECK_MINUTES,
                id="check_alerts", replace_existing=True)
    sch.add_job(job_refresh_news, "interval", minutes=NEWS_REFRESH_MINUTES,
                id="refresh_news", replace_existing=True)
    hour, minute = (int(x) for x in SUGGESTION_HOUR.split(":"))
    sch.add_job(job_daily_suggestion, "cron", hour=hour, minute=minute,
                id="daily_suggestion", replace_existing=True)
    sch.add_job(job_weekly_suggestion, "cron", day_of_week="mon", hour=hour, minute=minute,
                id="weekly_suggestion", replace_existing=True)
    sch.start()
    _scheduler = sch
    logger.info("Scheduler iniciado (precios cada %s min, alertas cada %s min)",
                PRICE_REFRESH_MINUTES, ALERT_CHECK_MINUTES)
    return sch


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
