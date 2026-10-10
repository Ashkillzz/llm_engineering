"""
Container keep-warm utility for Modal Serverless deployment.
Periodically pings the container to prevent scale-to-zero cold starts.
"""

from datetime import datetime
import time
import modal

Pricer = modal.Cls.lookup("pricer-service", "Pricer")
pricer = Pricer()

print(f"Starting keep-warm service for pricer-service...")
while True:
    try:
        reply = pricer.wake_up.remote()
        print(f"[{datetime.now()}] Modal Ping Response: {reply}")
    except Exception as e:
        print(f"[{datetime.now()}] Ping failed: {e}")
    time.sleep(30)
