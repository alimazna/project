"""Analysis endpoints: scenario generation (engine-backed), scenario readback."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.backtest import run_backtest
from app.analysis.engine import compute_scenario
from app.db.session import get_db
from app.models import Candle, NewsArticle, Scenario
from app.providers.base import CandleData

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _candle_data_from_row(c: Candle) -> CandleData:
    return CandleData(
        symbol=c.symbol,
        interval=c.interval,
        open_time=c.open_time,
        open=c.open,
        high=c.high,
        low=c.low,
        close=c.close,
        volume=c.volume,
    )


def _load_candles(db: Session, symbol: str, interval: str, limit: int) -> list[CandleData]:
    rows = (
        db.execute(
            select(Candle)
            .where(Candle.symbol == symbol.upper(), Candle.interval == interval)
            .order_by(Candle.open_time.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    if not rows:
        return []
    return [_candle_data_from_row(c) for c in reversed(rows)]


def _load_news(db: Session, symbol: str, limit: int = 50) -> list[dict]:
    rows = (
        db.execute(
            select(NewsArticle)
            .where(
                NewsArticle.sentiment.in_(["positive", "negative", "mixed", "neutral"]),
                NewsArticle.relevance_score >= 0.1,
                NewsArticle.assets.like(f'%"{symbol.upper()}"%'),
            )
            .order_by(NewsArticle.published_at.desc().nullslast(), NewsArticle.id.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        {
            "url": n.url,
            "title": n.title,
            "summary": n.summary,
            "sentiment": n.sentiment,
            "relevance_score": n.relevance_score,
            "importance": n.importance,
            "published_at": n.published_at,
        }
        for n in rows
    ]


def _to_scenario_row(s: dict, db: Session) -> Scenario:
    now = datetime.now(UTC)
    return Scenario(
        symbol=s["symbol"],
        direction=s["direction"],
        status=s["status"],
        timeframe=s["timeframe"],
        rule_version=s["rule_version"],
        alignment_score=s["alignment_score"],
        risk_reward=s.get("risk_reward"),
        entry_low=s.get("entry_low"),
        entry_high=s.get("entry_high"),
        stop_loss=s.get("stop_loss"),
        take_profits=s.get("take_profits", []),
        invalidation=s.get("invalidation", {}),
        evidence=s.get("evidence", {}),
        decisions=s.get("decisions", []),
        created_at=now,
        updated_at=now,
    )


@router.post("/run")
def run_analysis(
    db: Session = Depends(get_db),
    symbol: str = Query("BTC/USD", description="Canonical symbol, e.g. BTC/USD"),
    interval: str = Query("1h", description="1m|5m|15m|30m|1h|4h|1d|1w"),
    limit: int = Query(200, ge=60, le=1000),
    with_news: bool = Query(True, description="Include scored news in the matrix"),
    persist: bool = Query(True, description="Persist a Scenario row"),
) -> dict:
    """Generate a deterministic scenario from real candles (+ news)."""
    candles = _load_candles(db, symbol, interval, limit)
    if len(candles) < 30:
        raise HTTPException(404, f"No candle data for {symbol.upper()} ({interval})")

    news = _load_news(db, symbol) if with_news else None
    scenario = compute_scenario(
        candles,
        news=news,
        symbol=symbol.upper(),
        timeframe=interval,
    )

    saved_id = None
    if persist:
        row = _to_scenario_row(scenario, db)
        db.add(row)
        db.commit()
        db.refresh(row)
        saved_id = row.id

    return {"scenario": scenario, "saved_scenario_id": saved_id}


@router.get("/scenarios")
def list_scenarios(
    db: Session = Depends(get_db),
    symbol: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    q = select(Scenario).order_by(Scenario.created_at.desc()).limit(limit)
    if symbol:
        q = q.where(Scenario.symbol == symbol.upper())
    rows = db.execute(q).scalars().all()
    return {
        "scenarios": [
            {
                "id": r.id,
                "symbol": r.symbol,
                "direction": r.direction,
                "status": r.status,
                "timeframe": r.timeframe,
                "alignment_score": r.alignment_score,
                "risk_reward": r.risk_reward,
                "entry_low": r.entry_low,
                "entry_high": r.entry_high,
                "stop_loss": r.stop_loss,
                "take_profits": r.take_profits,
                "rule_version": r.rule_version,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "evidence": r.evidence,
            }
            for r in rows
        ]
    }


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(Scenario, scenario_id)
    if row is None:
        raise HTTPException(404, "Scenario not found")
    return {
        "scenario": {
            "id": row.id,
            "symbol": row.symbol,
            "direction": row.direction,
            "status": row.status,
            "timeframe": row.timeframe,
            "alignment_score": row.alignment_score,
            "risk_reward": row.risk_reward,
            "entry_low": row.entry_low,
            "entry_high": row.entry_high,
            "stop_loss": row.stop_loss,
            "take_profits": row.take_profits,
            "invalidation": row.invalidation,
            "evidence": row.evidence,
            "decisions": row.decisions,
            "rule_version": row.rule_version,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
    }


@router.get("/backtest")
def backtest(
    db: Session = Depends(get_db),
    symbol: str = Query("BTC/USD"),
    interval: str = Query("1h"),
    limit: int = Query(400, ge=60, le=2000),
    hold_bars: int = Query(24, ge=1, le=240),
) -> dict:
    candles = _load_candles(db, symbol, interval, limit)
    if len(candles) < 31:
        raise HTTPException(404, f"Not enough candle data for {symbol.upper()} ({interval})")
    return run_backtest(candles, symbol=symbol.upper(), hold_bars=hold_bars)
