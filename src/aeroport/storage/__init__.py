from concurrent.futures import ThreadPoolExecutor

from sunhead.conf import settings

storage_executor = ThreadPoolExecutor(max_workers=getattr(settings, 'STORAGE_DEFAULT_WORKERS_NUMBER', 10))
