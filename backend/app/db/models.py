"""Compatibility shim for the canonical ORM package.

The live model definitions are owned by `app.db.models/`. This module remains
import-safe for any older code paths that still import `app.db.models`.
"""

from app.db.models import *  # noqa: F401,F403
