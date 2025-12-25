"""
DSI Inference Function Registry

Maps YAML `inference_utility_function` names to their Python implementations.

This registry provides:
    - Registration of inference functions by name
    - Lookup of functions at runtime
    - Validation that required functions exist
    - Discovery of available functions

Usage:
    # Registering a function
    @register_inference_function("alliance_membership_basefunction")
    def alliance_membership_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
        ...
    
    # Or register manually
    register_inference_function("my_function", my_function_impl)
    
    # Looking up a function
    func = get_inference_function("alliance_membership_basefunction")
    result = func(entity_id, context)
"""

from typing import Callable, Dict, List, Optional, Set
from functools import wraps

from ..types import SignalResult, InferenceContext


# Type for inference functions
InferenceFunctionType = Callable[[str, InferenceContext], SignalResult]

# Global registry
_INFERENCE_REGISTRY: Dict[str, InferenceFunctionType] = {}


class InferenceFunctionNotFoundError(Exception):
    """Raised when a requested inference function is not registered."""
    
    def __init__(self, function_name: str, available: List[str] = None):
        self.function_name = function_name
        self.available = available or []
        
        message = f"Inference function '{function_name}' not found in registry."
        if self.available:
            message += f" Available functions: {', '.join(sorted(self.available)[:10])}"
            if len(self.available) > 10:
                message += f" ... and {len(self.available) - 10} more"
        
        super().__init__(message)


def register_inference_function(
    name: str,
    func: InferenceFunctionType = None
) -> Callable:
    """
    Register an inference function in the global registry.
    
    Can be used as a decorator or called directly:
    
    As decorator:
        @register_inference_function("my_function")
        def my_function(entity_id: str, context: InferenceContext) -> SignalResult:
            ...
    
    Direct call:
        register_inference_function("my_function", my_function_impl)
    
    Args:
        name: The function name as referenced in YAML config
        func: The function implementation (optional if used as decorator)
    
    Returns:
        The registered function, or a decorator if func is None
    """
    def decorator(f: InferenceFunctionType) -> InferenceFunctionType:
        _INFERENCE_REGISTRY[name] = f
        # Store the registry name on the function for debugging
        f._inference_registry_name = name
        return f
    
    if func is not None:
        # Direct call: register_inference_function("name", func)
        return decorator(func)
    
    # Decorator usage: @register_inference_function("name")
    return decorator


def get_inference_function(name: str) -> InferenceFunctionType:
    """
    Retrieve an inference function by name.
    
    Args:
        name: The function name as referenced in YAML config
    
    Returns:
        The registered inference function
    
    Raises:
        InferenceFunctionNotFoundError: If function is not registered
    """
    if name not in _INFERENCE_REGISTRY:
        raise InferenceFunctionNotFoundError(name, list(_INFERENCE_REGISTRY.keys()))
    
    return _INFERENCE_REGISTRY[name]


def list_inference_functions() -> List[str]:
    """
    List all registered inference function names.
    
    Returns:
        Sorted list of registered function names
    """
    return sorted(_INFERENCE_REGISTRY.keys())


def get_all_inference_functions() -> Dict[str, InferenceFunctionType]:
    """
    Get the entire registry dictionary.
    
    Returns:
        Copy of the registry mapping names to functions
    """
    return dict(_INFERENCE_REGISTRY)


def clear_registry() -> None:
    """
    Clear all registered functions.
    
    Primarily for testing purposes.
    """
    _INFERENCE_REGISTRY.clear()


def validate_config_functions(
    required_functions: Set[str]
) -> Dict[str, bool]:
    """
    Validate that all required functions are registered.
    
    Args:
        required_functions: Set of function names from YAML config
    
    Returns:
        Dict mapping function name to whether it's registered
    
    Example:
        required = {"alliance_membership_basefunction", "codeshare_partner_basefunction"}
        status = validate_config_functions(required)
        # {"alliance_membership_basefunction": True, "codeshare_partner_basefunction": False}
    """
    return {
        name: name in _INFERENCE_REGISTRY
        for name in required_functions
    }


def get_missing_functions(required_functions: Set[str]) -> Set[str]:
    """
    Get functions that are required but not registered.
    
    Args:
        required_functions: Set of function names from YAML config
    
    Returns:
        Set of missing function names
    """
    return required_functions - set(_INFERENCE_REGISTRY.keys())


def get_coverage_functions(coverage_prefix: str) -> List[str]:
    """
    Get all registered functions for a coverage domain.
    
    This is a convenience for discovering functions by naming convention.
    Assumes functions follow pattern like: alliance_membership_basefunction
    
    Args:
        coverage_prefix: Not used directly - returns all functions.
                        Override in domain modules to filter.
    
    Returns:
        List of matching function names
    """
    # For now, return all - domain modules can implement filtering
    return list_inference_functions()
