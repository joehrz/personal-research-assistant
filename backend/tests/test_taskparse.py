from datetime import date, datetime, timedelta

from pra.services.taskparse import parse

NOW = datetime(2026, 7, 29, 10, 0)  # a Wednesday
TODAY = NOW.date()


def test_plain_title():
    p = parse("buy a lab notebook", now=NOW)
    assert p.title == "buy a lab notebook"
    assert p.due_date is None
    assert p.priority == 4


def test_full_example():
    p = parse("review CV paper draft friday 2pm #thesis p1 @deep-work", now=NOW)
    assert p.title == "review CV paper draft"
    assert p.due_date == date(2026, 7, 31)  # coming Friday
    assert p.scheduled_at == datetime(2026, 7, 31, 14, 0)
    assert p.priority == 1
    assert p.project == "thesis"
    assert p.tags == ["deep-work"]


def test_today_tomorrow():
    assert parse("do it today", now=NOW).due_date == TODAY
    assert parse("do it tomorrow", now=NOW).due_date == TODAY + timedelta(days=1)


def test_iso_and_month_day():
    assert parse("submit 2026-09-01", now=NOW).due_date == date(2026, 9, 1)
    assert parse("submit sep 1", now=NOW).due_date == date(2026, 9, 1)
    # month/day in the past rolls to next year
    assert parse("review jan 5", now=NOW).due_date == date(2027, 1, 5)


def test_in_n_days_and_next_week():
    assert parse("follow up in 3 days", now=NOW).due_date == TODAY + timedelta(days=3)
    assert parse("plan next week", now=NOW).due_date == date(2026, 8, 3)  # next Monday


def test_weekday_same_day_rolls_forward_with_next():
    p = parse("standup next wednesday", now=NOW)
    assert p.due_date == TODAY + timedelta(days=7)
    p2 = parse("standup wednesday", now=NOW)
    assert p2.due_date == TODAY  # bare weekday matching today stays today


def test_time_without_date_schedules_next_occurrence():
    p = parse("call supervisor at 9am", now=NOW)  # 9am already past at 10:00
    assert p.scheduled_at == datetime(2026, 7, 30, 9, 0)
    assert p.due_date == date(2026, 7, 30)
    p2 = parse("call supervisor at 4pm", now=NOW)
    assert p2.scheduled_at == datetime(2026, 7, 29, 16, 0)


def test_24h_time():
    p = parse("experiment run friday 14:30", now=NOW)
    assert p.scheduled_at == datetime(2026, 7, 31, 14, 30)


def test_priority_not_confused_with_words():
    p = parse("prepare p2 slides", now=NOW)
    assert p.priority == 2
    p2 = parse("prepare pt2 slides", now=NOW)
    assert p2.priority == 4
    assert p2.title == "prepare pt2 slides"


def test_multiple_tags():
    p = parse("read attention paper @ml @reading", now=NOW)
    assert sorted(p.tags) == ["ml", "reading"]
