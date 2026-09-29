"""Pure calculations shared by every API endpoint.

Stocks (children in custody/care) are snapshots. Flows (transfers and
discharges) describe activity during a reporting period; they are never
presented as a measured bed capacity or automatically summed across gaps.
"""

from datetime import date, timedelta
from math import sqrt


FIELDS = ("cbp_intake", "cbp_custody", "transfers", "hhs_care", "discharges")


def enriched(rows):
    """Add transparent metrics to sorted observation dictionaries."""
    result = []
    previous = None
    for row in rows:
        item = dict(row)
        item["total_load"] = item["cbp_custody"] + item["hhs_care"]
        item["net_flow"] = item["transfers"] - item["discharges"]
        item["offset_ratio"] = (item["discharges"] / item["transfers"]
                                if item["transfers"] else None)
        item["gap_days"] = ((date.fromisoformat(item["date"]) -
                             date.fromisoformat(previous["date"])).days
                            if previous else None)
        item["care_change_pct"] = (
            100 * (item["hhs_care"] - previous["hhs_care"]) / previous["hhs_care"]
            if previous and previous["hhs_care"] else None
        )
        item["flag_transfer_gt_custody"] = item["transfers"] > item["cbp_custody"]
        item["flag_discharge_gt_care"] = item["discharges"] > item["hhs_care"]
        result.append(item)
        previous = item
    for index, item in enumerate(result):
        recent = result[max(0, index - 6):index + 1]
        item["load_avg7"] = round(sum(r["total_load"] for r in recent) / 7, 2) if len(recent) == 7 else None
        item["net_avg7"] = round(sum(r["net_flow"] for r in recent) / 7, 2) if len(recent) == 7 else None
        item["pressure_flag"] = len(recent) == 7 and sum(r["net_flow"] for r in recent) > 0 and sum(r["net_flow"] > 0 for r in recent) >= 4
    return result


def summary(rows):
    """Describe the selected range; the latest snapshot is clearly labeled."""
    if not rows:
        return {"count": 0}
    latest = rows[-1]
    recent = rows[-min(30, len(rows)):]
    avg = lambda field: sum(r[field] for r in recent) / len(recent)
    peak = max(rows, key=lambda r: r["total_load"])
    positive = sum(r["net_flow"] > 0 for r in recent)
    return {
        "count": len(rows), "first_date": rows[0]["date"], "last_date": latest["date"],
        "latest": latest, "peak": {"date": peak["date"], "load": peak["total_load"]},
        "recent_window": len(recent), "average_net_flow": round(avg("net_flow"), 1),
        "average_transfers": round(avg("transfers"), 1),
        "average_discharges": round(avg("discharges"), 1),
        "aggregate_offset_ratio": round(sum(r["discharges"] for r in recent) /
                                        sum(r["transfers"] for r in recent), 3)
                                  if sum(r["transfers"] for r in recent) else None,
        "positive_flow_observations": positive,
        "pressure_flag": latest["pressure_flag"],
    }


def quality(rows):
    """Report review flags without declaring timing differences data errors."""
    gaps = [r for r in rows if r["gap_days"] and r["gap_days"] > 1]
    return {
        "observations": len(rows), "reporting_gaps": len(gaps),
        "unobserved_calendar_days": sum(r["gap_days"] - 1 for r in gaps),
        "largest_gap_days": max((r["gap_days"] for r in gaps), default=0),
        "transfers_above_custody": sum(r["flag_transfer_gt_custody"] for r in rows),
        "discharges_above_care": sum(r["flag_discharge_gt_care"] for r in rows),
    }


def monthly(rows):
    """Average stock snapshots and sum observed flows, with row counts."""
    groups = {}
    for row in rows:
        group = groups.setdefault(row["date"][:7], [])
        group.append(row)
    return [{"month": month, "observations": len(group),
             "average_load": round(sum(r["total_load"] for r in group) / len(group), 1),
             "transfers": sum(r["transfers"] for r in group),
             "discharges": sum(r["discharges"] for r in group)}
            for month, group in sorted(groups.items())]


def forecast(rows, days=14, lookback=60):
    """Simple least-squares scenario using calendar time, not a confidence claim."""
    selected = rows[-lookback:]
    if len(selected) < 5:
        return {"points": [], "message": "At least five observations are required."}
    origin = date.fromisoformat(selected[0]["date"])
    xs = [(date.fromisoformat(r["date"]) - origin).days for r in selected]
    ys = [r["hhs_care"] for r in selected]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    denominator = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denominator if denominator else 0
    intercept = my - slope * mx
    residual = sqrt(sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys)) / (len(xs) - 2))
    last = date.fromisoformat(selected[-1]["date"])
    points = []
    for step in range(1, days + 1):
        future = last + timedelta(days=step)
        estimate = max(0, intercept + slope * (future - origin).days)
        points.append({"date": future.isoformat(), "estimate": round(estimate),
                       "illustrative_low": round(max(0, estimate - 1.5 * residual)),
                       "illustrative_high": round(estimate + 1.5 * residual)})
    return {"points": points, "slope_per_calendar_day": round(slope, 2),
            "lookback_observations": len(selected),
            "method": "Linear extrapolation; residual range is illustrative, not a calibrated confidence interval."}
