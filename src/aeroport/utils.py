import logging

from sunhead.exceptions import DuplicateMetricException
from sunhead.metrics import Metrics

logger = logging.getLogger(__name__)


def register_metric(metrics: Metrics, metric_type: str, name: str, *args) -> str:
    """
    Will register metric in SunHead Metrics system and return its full name for
    later retrieval. Main purpose of this is to shut down duplicates.
    """
    full_name = metrics.prefix("fs_storage_put_kb_total")
    name = "add_{}".format(metric_type)
    try:
        getattr(metrics, name)(full_name, *args)
    except DuplicateMetricException:
        logger.debug("Metric %s exists, passing silently", full_name)

    return full_name
