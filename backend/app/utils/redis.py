import redis
from app.config import settings

def get_redis_client():
    """
    Creates a Redis client capable of handling both Local and Cloud connections.
    """
    redis_url = settings.REDIS_URL
    
    # Base configuration
    kwargs = {
        "decode_responses": True, # Returns strings instead of bytes
        "socket_timeout": 5       # Don't wait forever if Redis is down
    }

    # SMART SWITCH:
    # If the URL starts with 'rediss://' (note the double 's'), it's a Secure Cloud.
    # We apply 'ssl_cert_reqs=None' to fix the Mac certificate error.
    # If it's 'redis://' (Local), we skip this so it connects normally.
    if redis_url.startswith("rediss://"):
        kwargs["ssl_cert_reqs"] = None

    try:
        client = redis.from_url(redis_url, **kwargs)
        
        # Quick test to see if it works
        client.ping()
        print(f"✅ Redis Connected: {'Secure Cloud' if redis_url.startswith('rediss') else 'Local'}")
        return client
        
    except redis.ConnectionError as e:
        print(f"⚠️ Redis Connection Failed: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Redis Error: {e}")
        return None

# Create a single instance to be imported anywhere in your app
redis_client = get_redis_client()