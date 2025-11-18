import asyncio
import logging
from datetime import datetime
from typing import Dict


class LiveMonitor:
    """
    Core live monitoring controller for real-time betting data.

    This class is intentionally minimal here and focused on providing
    a robust async context manager so it can be safely used as:

        async with LiveMonitor(config) as monitor:
            ...
    """

    def __init__(self, config: Dict | None = None) -> None:
        self.config: Dict = config or {}
        self.logger = logging.getLogger(__name__)
        self.running: bool = False
        # Scrapers / AI clients are populated by higher-level orchestration code
        self.scrapers: Dict[str, object] = {}
        self.ai_clients: Dict[str, object] = {}

    async def __aenter__(self) -> "LiveMonitor":
        """
        Proper async context entry.
        Initializes internal components and marks the monitor as running.
        """
        try:
            await self.initialize()
            self.logger.info("✅ LiveMonitor started successfully")
            return self
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("❌ LiveMonitor initialization failed: %s", exc)
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Proper async context exit with cleanup.
        Ensures that all managed resources are shut down cleanly.
        """
        try:
            await self.cleanup()
            self.logger.info("✅ LiveMonitor cleaned up successfully")
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("⚠️ Error during LiveMonitor cleanup: %s", exc)
        # Do not suppress exceptions from inside the context
        return False

    async def initialize(self) -> None:
        """
        Initialize all components.

        In the full system this is where scrapers, AI clients, database
        connections, and messaging backends would be wired up.
        """
        self.running = True
        # Placeholder for future initialization hooks
        # e.g. await self._init_scrapers(), await self._init_ai_clients(), ...
        self.logger.info(
            "🔧 LiveMonitor components initialized at %s", datetime.utcnow().isoformat()
        )

    async def cleanup(self) -> None:
        """
        Clean shutdown of all components.

        Iterates over any registered scrapers and attempts to close them
        asynchronously when they expose an `async close()` method.
        """
        self.running = False

        # Close all scrapers that provide an async close() coroutine
        for name, scraper in list(self.scrapers.items()):
            close_fn = getattr(scraper, "close", None)
            if close_fn is None:
                continue

            try:
                if asyncio.iscoroutinefunction(close_fn):
                    await close_fn()
                else:
                    # Allow synchronous close() for flexibility
                    close_fn()
                self.logger.debug("Closed scraper '%s'", name)
            except Exception:  # pragma: no cover - best-effort cleanup
                self.logger.exception("Error while closing scraper '%s'", name)

        self.logger.info("🧹 LiveMonitor cleanup completed")


