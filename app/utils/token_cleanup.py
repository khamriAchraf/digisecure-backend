"""
Utility script to clean up expired refresh tokens
This can be run as a scheduled task (cron job) to keep the database clean
"""

import asyncio
from datetime import datetime, timedelta, timezone

from app.core.logger import logger
from app.db.crud import refresh_token as refresh_token_crud
from app.db.session import get_db


async def cleanup_expired_tokens():
    """Clean up expired refresh tokens from the database"""
    try:
        db = next(get_db())
        cleaned_count = refresh_token_crud.cleanup_expired_tokens(db)
        logger.info(f"Cleaned up {cleaned_count} expired refresh tokens")
        return cleaned_count
    except Exception as e:
        logger.error(f"Error during token cleanup: {str(e)}")
        return 0
    finally:
        db.close()


async def cleanup_old_used_tokens(days_old: int = 7):
    """Clean up old used tokens that are older than specified days"""
    try:
        db = next(get_db())
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        # This would need to be implemented in the CRUD layer
        # For now, we'll just log the intention
        logger.info(f"Would clean up used tokens older than {cutoff_date}")
        return 0
    except Exception as e:
        logger.error(f"Error during old token cleanup: {str(e)}")
        return 0
    finally:
        db.close()


def main():
    """Main function to run cleanup tasks"""
    logger.info("Starting refresh token cleanup...")

    # Run cleanup tasks
    asyncio.run(cleanup_expired_tokens())
    asyncio.run(cleanup_old_used_tokens())

    logger.info("Refresh token cleanup completed")


if __name__ == "__main__":
    main()
