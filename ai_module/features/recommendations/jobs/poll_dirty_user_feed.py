import argparse
import time

from ai_module.app.config import settings
from ai_module.app.logging import configure_logging
from ai_module.infra.db import get_connection
from ai_module.features.recommendations.repository import FeedRepository


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Poll dirty users table and recompute feed in batches"
    )
    parser.add_argument("--batch-size", type=int, default=None, help="Users per batch")
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=None,
        help="Sleep duration when queue is empty",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process at most one batch and exit",
    )
    args = parser.parse_args()

    configure_logging()
    from ai_module.features.recommendations.service import (
        recompute_user_feed_for_user_ids,
    )

    batch_size = (
        settings.reco_dirty_batch_size if args.batch_size is None else args.batch_size
    )
    poll_interval = (
        settings.reco_dirty_poll_interval_seconds
        if args.poll_interval_seconds is None
        else args.poll_interval_seconds
    )

    if batch_size <= 0:
        print("ERROR: batch-size must be > 0")
        return 1

    while True:
        with get_connection() as connection:
            repository = FeedRepository(connection)
            with connection.transaction():
                batch = repository.claim_dirty_user_ids(batch_size=batch_size)

        if not batch.user_ids:
            if args.once:
                print("SUCCESS: queue is empty")
                return 0
            time.sleep(max(0.1, poll_interval))
            continue

        try:
            result = recompute_user_feed_for_user_ids(batch.user_ids)
        except Exception:
            with get_connection() as connection:
                repository = FeedRepository(connection)
                with connection.transaction():
                    repository.mark_dirty_user_ids(batch.user_ids)
            raise
        if not result.lock_acquired:
            with get_connection() as connection:
                repository = FeedRepository(connection)
                with connection.transaction():
                    repository.mark_dirty_user_ids(batch.user_ids)
            print("SKIPPED: recompute is already running")
            if args.once:
                return 0
            time.sleep(max(0.1, poll_interval))
            continue

        print(
            "SUCCESS: users_total=%s users_updated=%s rows_written=%s interactions_total=%s"
            % (
                result.users_total,
                result.users_updated,
                result.rows_written,
                result.interactions_total,
            )
        )

        if args.once:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())



