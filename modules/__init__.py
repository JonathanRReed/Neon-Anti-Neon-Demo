"""
Illusion Modules Package for Color Perception Laboratory

Each module implements a specific color perception illusion or experiment.
"""

from typing import Protocol, Optional
import numpy as np


class IllusionModule(Protocol):
    """Protocol defining the interface for illusion modules."""
    
    @property
    def name(self) -> str:
        """Human-readable name of the illusion."""
        ...
    
    @property
    def description(self) -> str:
        """Brief description of the illusion."""
        ...
    
    @property
    def has_safety_warning(self) -> bool:
        """Whether this module requires safety warnings."""
        ...
    
    def render(self, width: int, height: int) -> np.ndarray:
        """Render the illusion to an image buffer."""
        ...
    
    def get_proof_info(self) -> Optional[str]:
        """Get pixel proof information if applicable."""
        ...


# Module registry
AVAILABLE_MODULES = {}


def register_module(module_class):
    """Decorator to register an illusion module."""
    AVAILABLE_MODULES[module_class.__name__] = module_class
    return module_class


def get_module(name: str):
    """Get a module class by name."""
    return AVAILABLE_MODULES.get(name)


def list_modules():
    """List all available modules."""
    return list(AVAILABLE_MODULES.keys())
