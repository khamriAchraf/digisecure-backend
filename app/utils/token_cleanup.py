"""
Utility script to clean up expired tokens (refresh tokens and password reset tokens)
This can be run as a scheduled task (cron job) to keep the database clean
"""

import asyncio
from datetime import datetime, timedelta, timezone

from app.core.logger import logger
from app.db.crud import password_reset_token as password_reset_token_crud
from app.db.crud import refresh_token as refresh_token_crud
from app.db.session import get_db


async def cleanup_expired_tokens():
    """Clean up expired refresh tokens and password reset tokens from the database"""
    try:
        db = next(get_db())

        # Clean up expired refresh tokens
        refresh_cleaned = refresh_token_crud.cleanup_expired_tokens(db)
        logger.info(f"Cleaned up {refresh_cleaned} expired refresh tokens")

        # Clean up expired password reset tokens
        reset_cleaned = password_reset_token_crud.cleanup_expired_password_reset_tokens(
            db
        )
        logger.info(f"Cleaned up {reset_cleaned} expired password reset tokens")

        total_cleaned = refresh_cleaned + reset_cleaned
        return total_cleaned
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
    logger.info("Starting token cleanup (refresh + password reset)...")

    # Run cleanup tasks
    asyncio.run(cleanup_expired_tokens())
    asyncio.run(cleanup_old_used_tokens())

    logger.info("Token cleanup completed")


if __name__ == "__main__":
    main()
