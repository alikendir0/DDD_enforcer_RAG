"""Configuration management service for UI parameters."""

import json
import time
from pathlib import Path
from typing import Tuple, Optional
from src.models.ui_configuration import UIConfiguration
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages loading, saving, and validating UI configuration parameters."""

    def __init__(self, config_path: str = "config/ui_config.json"):
        """Initialize config manager with file path.

        Args:
            config_path: Path to configuration JSON file
        """
        self.config_path = Path(config_path)
        self.current_config: Optional[UIConfiguration] = None
        self.original_chunk_config: Tuple[int, int] = (512, 0)  # Track changes requiring re-index
        logger.info(f"ConfigManager initialized with path: {self.config_path}")

    def load_config(self) -> UIConfiguration:
        """Load configuration from file or create defaults.

        Returns:
            UIConfiguration object with loaded or default values
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)

                config = UIConfiguration(
                    top_k=data.get('top_k', 3),
                    chunk_size=data.get('chunk_size', 512),
                    chunk_overlap=data.get('chunk_overlap', 0),
                    show_context_enabled=data.get('show_context_enabled', False),
                    last_modified=data.get('last_modified', time.time())
                )

                # Validate loaded config
                is_valid, error_msg = self.validate_config(config)
                if not is_valid:
                    logger.warning(f"Loaded config invalid: {error_msg}. Using defaults.")
                    config = UIConfiguration()

                logger.info(f"Configuration loaded from {self.config_path}")
                self.current_config = config
                self.original_chunk_config = (config.chunk_size, config.chunk_overlap)
                return config

            else:
                logger.info("Config file not found, creating defaults")
                config = UIConfiguration()
                self.current_config = config
                self.original_chunk_config = (config.chunk_size, config.chunk_overlap)
                # Save defaults to file
                self.save_config(
                    config.top_k,
                    config.chunk_size,
                    config.chunk_overlap,
                    config.show_context_enabled
                )
                return config

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file: {e}. Using defaults.")
            config = UIConfiguration()
            self.current_config = config
            return config

        except Exception as e:
            logger.error(f"Error loading config: {e}. Using defaults.", exc_info=True)
            config = UIConfiguration()
            self.current_config = config
            return config

    def save_config(
        self,
        top_k: int,
        chunk_size: int,
        chunk_overlap: int,
        show_context_enabled: bool
    ) -> Tuple[bool, str]:
        """Save configuration to file after validation.

        Args:
            top_k: Number of chunks to retrieve (1-10)
            chunk_size: Token count per chunk (256-1024)
            chunk_overlap: Overlapping tokens (0-256)
            show_context_enabled: Whether to show context by default

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Create new config object for validation
            new_config = UIConfiguration(
                top_k=top_k,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                show_context_enabled=show_context_enabled,
                last_modified=time.time()
            )

            # Validate
            is_valid, error_msg = self.validate_config(new_config)
            if not is_valid:
                return False, f"Validation failed: {error_msg}"

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(self.config_path, 'w') as f:
                json.dump({
                    'top_k': new_config.top_k,
                    'chunk_size': new_config.chunk_size,
                    'chunk_overlap': new_config.chunk_overlap,
                    'show_context_enabled': new_config.show_context_enabled,
                    'last_modified': new_config.last_modified
                }, f, indent=2)

            self.current_config = new_config
            logger.info(f"Configuration saved successfully: {new_config}")
            return True, "Configuration saved successfully"

        except OSError as e:
            error_msg = f"Failed to write config file: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

        except Exception as e:
            error_msg = f"Error saving config: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def get_current_config(self) -> UIConfiguration:
        """Get current configuration (loads if not already loaded).

        Returns:
            UIConfiguration object
        """
        if self.current_config is None:
            return self.load_config()
        return self.current_config

    def reset_to_defaults(self) -> Tuple[bool, UIConfiguration]:
        """Reset configuration to default values.

        Returns:
            Tuple of (success: bool, config: UIConfiguration)
        """
        try:
            default_config = UIConfiguration()
            success, message = self.save_config(
                default_config.top_k,
                default_config.chunk_size,
                default_config.chunk_overlap,
                default_config.show_context_enabled
            )

            if success:
                logger.info("Configuration reset to defaults")
                self.original_chunk_config = (default_config.chunk_size, default_config.chunk_overlap)
                return True, default_config
            else:
                logger.error(f"Failed to reset config: {message}")
                return False, self.current_config or UIConfiguration()

        except Exception as e:
            logger.error(f"Error resetting config: {e}", exc_info=True)
            return False, self.current_config or UIConfiguration()

    def validate_config(self, config: UIConfiguration) -> Tuple[bool, str]:
        """Validate configuration values.

        Args:
            config: UIConfiguration object to validate

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        try:
            # Check top_k range
            if not (1 <= config.top_k <= 10):
                return False, f"top_k must be between 1 and 10, got {config.top_k}"

            # Check chunk_size range
            if not (256 <= config.chunk_size <= 1024):
                return False, f"chunk_size must be between 256 and 1024, got {config.chunk_size}"

            # Check chunk_overlap range
            if not (0 <= config.chunk_overlap <= 256):
                return False, f"chunk_overlap must be between 0 and 256, got {config.chunk_overlap}"

            # Check overlap < chunk_size
            if config.chunk_overlap >= config.chunk_size:
                return False, f"chunk_overlap ({config.chunk_overlap}) must be < chunk_size ({config.chunk_size})"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {e}"

    def detect_reindex_required(self, new_chunk_size: int, new_chunk_overlap: int) -> bool:
        """Detect if re-indexing is required based on chunk size/overlap changes.

        Args:
            new_chunk_size: New chunk size value
            new_chunk_overlap: New chunk overlap value

        Returns:
            True if re-indexing required, False otherwise
        """
        original_size, original_overlap = self.original_chunk_config
        size_changed = new_chunk_size != original_size
        overlap_changed = new_chunk_overlap != original_overlap

        if size_changed or overlap_changed:
            logger.info(
                f"Chunk configuration changed: "
                f"size {original_size}->{new_chunk_size}, "
                f"overlap {original_overlap}->{new_chunk_overlap}. "
                f"Re-indexing required."
            )
            return True

        return False
