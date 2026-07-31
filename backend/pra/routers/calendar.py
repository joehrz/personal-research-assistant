from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..deps import get_db
from ..models import CalendarFeed
from ..services import calendars

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/feeds", response_model=list[schemas.CalendarFeedOut])
def list_feeds(db: Session = Depends(get_db)):
    return db.execute(select(CalendarFeed).order_by(CalendarFeed.created_at)).scalars().all()


@router.post("/feeds", response_model=schemas.CalendarFeedOut, status_code=201)
def create_feed(body: schemas.CalendarFeedCreate, db: Session = Depends(get_db)):
    feed = CalendarFeed(**body.model_dump())
    db.add(feed)
    db.commit()
    return feed


@router.patch("/feeds/{feed_id}", response_model=schemas.CalendarFeedOut)
def update_feed(feed_id: str, body: schemas.CalendarFeedUpdate, db: Session = Depends(get_db)):
    feed = db.get(CalendarFeed, feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(feed, key, value)
    db.commit()
    return feed


@router.delete("/feeds/{feed_id}", status_code=204)
def delete_feed(feed_id: str, db: Session = Depends(get_db)):
    feed = db.get(CalendarFeed, feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    db.delete(feed)
    db.commit()


@router.get("/events", response_model=schemas.CalendarEventsOut)
def list_events(
    start: datetime = Query(),
    end: datetime = Query(),
    db: Session = Depends(get_db),
):
    feeds = db.execute(select(CalendarFeed).where(CalendarFeed.enabled)).scalars().all()
    events: list[schemas.CalendarEventOut] = []
    errors: list[schemas.CalendarFeedError] = []
    for feed in feeds:
        try:
            ics = calendars.fetch_ics(feed.url)
            for ev in calendars.parse_events(ics, start, end):
                events.append(
                    schemas.CalendarEventOut(
                        feed_id=feed.id, feed_name=feed.name, color=feed.color, **ev
                    )
                )
        except Exception as exc:  # a broken feed must not take down the calendar
            errors.append(schemas.CalendarFeedError(feed_id=feed.id, feed_name=feed.name,
                                                    message=str(exc)[:300]))
    events.sort(key=lambda e: e.start)
    return schemas.CalendarEventsOut(events=events, errors=errors)
