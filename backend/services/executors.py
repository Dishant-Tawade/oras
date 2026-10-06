"""Thread pools shared by the request handlers and the timer service."""
from concurrent.futures import ThreadPoolExecutor

# Year-lock simulations (NumPy plus GIL-bound Python).
SIMULATION_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="sim")

# Broadcast fan-out, kept apart so it never queues behind simulations.
BROADCAST_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="broadcast")
