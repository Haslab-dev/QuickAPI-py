"""
State management hooks for the templating engine
"""

import uuid
from typing import Any, Dict, Callable, Tuple, List, Optional


class HookContext:
    """Context for managing component hooks"""
    
    def __init__(self):
        self.component_id: Optional[str] = None
        self.states: Dict[str, Any] = {}
        self.reducers: Dict[str, Dict[str, Any]] = {}
        self.state_counter = 0
        self.reducer_counter = 0
    
    def reset(self):
        """Reset hook context for new render"""
        self.state_counter = 0
        self.reducer_counter = 0
    
    def use_state(self, initial_value: Any) -> Tuple[Any, Callable]:
        """Hook for managing state"""
        state_key = f"state_{self.state_counter}"
        self.state_counter += 1
        
        # Initialize state if not exists
        if state_key not in self.states:
            self.states[state_key] = initial_value
        
        current_value = self.states[state_key]
        
        def set_value(new_value: Any):
            """Function to update the state value"""
            if callable(new_value):
                # If it's a function, call it with current value
                self.states[state_key] = new_value(self.states[state_key])
            else:
                self.states[state_key] = new_value
            # Note: Component update will be handled by the template engine
        
        # Add the state key as an attribute to the setter for easy access
        set_value.state_key = state_key
        
        return current_value, set_value
    
    def use_reducer(self, reducer: Callable, initial_value: Any) -> Tuple[Any, Callable]:
        """Hook for managing state with a reducer function"""
        state_key = f"reducer_{self.reducer_counter}"
        reducer_id = str(uuid.uuid4())
        self.reducer_counter += 1
        
        # Initialize state if not exists
        if state_key not in self.states:
            self.states[state_key] = initial_value
        
        # Store reducer info
        self.reducers[reducer_id] = {
            'reducer': reducer,
            'state_key': state_key
        }
        
        current_value = self.states[state_key]
        
        def dispatch(action: Any):
            """Function to dispatch an action"""
            try:
                new_value = reducer(self.states[state_key], action)
                self.states[state_key] = new_value
                # Note: Component update will be handled by the template engine
                return new_value
            except Exception as e:
                print(f"Reducer error: {e}")
                return self.states[state_key]
        
        return current_value, dispatch


# Global hook context for functional components
_current_hook_context: Optional[HookContext] = None


def use_state(initial_value: Any) -> Tuple[Any, Callable]:
    """Hook for managing state in functional components"""
    if _current_hook_context is None:
        raise RuntimeError("use_state must be called within a component")
    
    return _current_hook_context.use_state(initial_value)


def use_named_state(name: str, initial_value: Any) -> Tuple[Any, Callable]:
    """Hook for managing named state - easier for binding"""
    if _current_hook_context is None:
        raise RuntimeError("use_named_state must be called within a component")
    
    # Use the name as the state key directly
    state_key = name
    
    # Initialize state if not exists
    if state_key not in _current_hook_context.states:
        _current_hook_context.states[state_key] = initial_value
    
    current_value = _current_hook_context.states[state_key]
    
    def set_value(new_value: Any):
        """Function to update the state value"""
        if callable(new_value):
            # If it's a function, call it with current value
            _current_hook_context.states[state_key] = new_value(_current_hook_context.states[state_key])
        else:
            _current_hook_context.states[state_key] = new_value
    
    # Add the state key as an attribute to the setter for easy access
    set_value.state_key = state_key
    
    return current_value, set_value


def use_reducer(reducer: Callable, initial_value: Any) -> Tuple[Any, Callable]:
    """Hook for managing state with a reducer in functional components"""
    if _current_hook_context is None:
        raise RuntimeError("use_reducer must be called within a component")
    
    return _current_hook_context.use_reducer(reducer, initial_value)


def set_hook_context(context: HookContext):
    """Set the current hook context (used by the component system)"""
    global _current_hook_context
    _current_hook_context = context


def clear_hook_context():
    """Clear the current hook context"""
    global _current_hook_context
    _current_hook_context = None