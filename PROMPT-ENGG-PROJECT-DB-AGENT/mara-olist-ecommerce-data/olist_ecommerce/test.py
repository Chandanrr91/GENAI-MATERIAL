class DebugLogger:
    def __call__(self, message):
        """Allows usage like @debug "message"."""
        if "env_logger" in globals():
            env_logger.debug(f"DEBUG: {message}")

debug = DebugLogger()
