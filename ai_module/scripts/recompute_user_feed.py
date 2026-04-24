import argparse

from ai_module.core.logging import configure_logging


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute user feed with item-to-item recommendations")
    parser.add_argument("--top-k", type=int, default=None, help="Max feed size per user")
    parser.add_argument("--lookback-days", type=int, default=None, help="Interactions lookback window")
    parser.add_argument("--half-life-days", type=float, default=None, help="Time-decay half-life")
    parser.add_argument("--max-items-per-user", type=int, default=None, help="Cap of source items per user")
    parser.add_argument("--neighbors-per-item", type=int, default=None, help="Cap of neighbors per article")
    parser.add_argument("--min-score", type=float, default=None, help="Minimum recommendation score")
    args = parser.parse_args()

    configure_logging()
    from ai_module.application.jobs.recompute_user_feed_job import recompute_user_feed_once

    try:
        result = recompute_user_feed_once(
            top_k=args.top_k,
            lookback_days=args.lookback_days,
            half_life_days=args.half_life_days,
            max_items_per_user=args.max_items_per_user,
            neighbors_per_item=args.neighbors_per_item,
            min_score=args.min_score,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1

    if not result.lock_acquired:
        print("SKIPPED: recompute is already running")
        return 0

    print(
        "SUCCESS: users_total=%s users_updated=%s rows_written=%s interactions_total=%s"
        % (
            result.users_total,
            result.users_updated,
            result.rows_written,
            result.interactions_total,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
