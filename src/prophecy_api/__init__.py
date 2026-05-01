"""Python client for the Prophecy REST API."""

from prophecy_api.client import ProphecyClient
from prophecy_api.exceptions import ProphecyAPIError, ProphecyError, ProphecyHTTPError
from prophecy_api.resources.pipelines import TERMINAL_STATUSES

__version__ = "0.1.0"

__all__ = [
    "ProphecyClient",
    "ProphecyError",
    "ProphecyHTTPError",
    "ProphecyAPIError",
    "TERMINAL_STATUSES",
    "__version__",
]
