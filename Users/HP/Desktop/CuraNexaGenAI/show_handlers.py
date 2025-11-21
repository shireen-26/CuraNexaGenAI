import logging
import backend.app.core.logging_config as lg

print("Before handlers:", [type(h).__name__ for h in logging.getLogger().handlers])
lg.configure_logging()
print("After handlers:", [type(h).__name__ for h in logging.getLogger().handlers])
