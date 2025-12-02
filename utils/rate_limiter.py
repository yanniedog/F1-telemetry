"""
Rate limiting utility for API calls.
Prevents exceeding API rate limits and handles retries.
"""

import time
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
from utils.logger import get_logger

logger = get_logger()


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(
        self,
        max_calls: int = 100,
        period: int = 60,
        retry_delay: float = 1.0,
        max_retries: int = 3
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
            retry_delay: Delay between retries in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.max_calls = max_calls
        self.period = period
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.calls = defaultdict(list)
    
    def _clean_old_calls(self, key: str):
        """Remove calls outside the time window."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.period)
        self.calls[key] = [
            call_time for call_time in self.calls[key]
            if call_time > cutoff
        ]
    
    def _wait_if_needed(self, key: str):
        """Wait if rate limit would be exceeded."""
        self._clean_old_calls(key)
        
        if len(self.calls[key]) >= self.max_calls:
            # Calculate wait time
            oldest_call = min(self.calls[key])
            wait_until = oldest_call + timedelta(seconds=self.period)
            wait_seconds = (wait_until - datetime.now()).total_seconds()
            
            if wait_seconds > 0:
                logger.info(f"Rate limit reached for {key}. Waiting {wait_seconds:.2f} seconds...")
                time.sleep(wait_seconds)
                self._clean_old_calls(key)
    
    def record_call(self, key: str = "default"):
        """Record an API call."""
        self.calls[key].append(datetime.now())
    
    def __call__(self, func: Callable) -> Callable:
        """
        Decorator for rate limiting.
        
        Usage:
            @rate_limiter(max_calls=100, period=60)
            def api_call():
                ...
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = kwargs.get('rate_limit_key', 'default')
            self._wait_if_needed(key)
            
            # Retry logic
            last_exception = None
            for attempt in range(self.max_retries):
                try:
                    self.record_call(key)
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}. "
                            f"Retrying in {wait_time:.2f} seconds..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {self.max_retries} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper


class APIRateLimiter:
    """Rate limiter configured for specific APIs."""
    
    # Rate limits for different APIs (calls per minute)
    RATE_LIMITS = {
        'ergast': {'max_calls': 200, 'period': 60},
        'openf1': {'max_calls': 100, 'period': 60},
        'fastf1': {'max_calls': 50, 'period': 60},  # Conservative limit
        'statsf1': {'max_calls': 30, 'period': 60},  # Web scraping, be respectful
        'f1com': {'max_calls': 30, 'period': 60},   # Web scraping, be respectful
        'fia': {'max_calls': 20, 'period': 60},     # PDF downloads, be respectful
    }
    
    def __init__(self):
        """Initialize API-specific rate limiters."""
        self.limiters = {}
        for api_name, limits in self.RATE_LIMITS.items():
            self.limiters[api_name] = RateLimiter(
                max_calls=limits['max_calls'],
                period=limits['period']
            )
    
    def get_limiter(self, api_name: str) -> RateLimiter:
        """
        Get rate limiter for specific API.
        
        Args:
            api_name: Name of the API
            
        Returns:
            RateLimiter instance
        """
        return self.limiters.get(api_name, self.limiters['ergast'])


# Global rate limiter instance
_rate_limiter_instance: Optional[APIRateLimiter] = None


def get_rate_limiter() -> APIRateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = APIRateLimiter()
    return _rate_limiter_instance

