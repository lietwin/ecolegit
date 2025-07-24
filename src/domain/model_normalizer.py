"""Model name normalization for handling typos and variations."""

import re
from typing import List, Tuple, Optional


def normalize_model_name(model_name: str) -> str:
    """Normalize model name to handle common typos and variations."""
    if not model_name:
        return model_name
        
    name = model_name.lower().strip()
    
    # Return original if only whitespace (to preserve behavior)
    if not name:
        return model_name
    
    # Direct typo mappings for common mistakes
    typo_patterns = {
        # OpenAI variations
        'gpt4o': 'gpt-4o',
        'gpt-4o': 'gpt-4o',  # Already correct
        'gpt4omini': 'gpt-4o-mini',
        'gpt-4o-mini': 'gpt-4o-mini',  # Already correct
        'gpt4o-mini': 'gpt-4o-mini',
        'gpt-4omini': 'gpt-4o-mini',
        'gpt35turbo': 'gpt-3.5-turbo',
        'gpt-35-turbo': 'gpt-3.5-turbo',
        'gpt3.5turbo': 'gpt-3.5-turbo',
        'gpt4': 'gpt-4',
        
        # Claude variations
        'claudeopus': 'claude-3-opus',
        'claude3opus': 'claude-3-opus',
        'claude-3opus': 'claude-3-opus',
        'claudesonnet': 'claude-3-sonnet',
        'claude3sonnet': 'claude-3-sonnet',
        'claude-3sonnet': 'claude-3-sonnet',
        'claudehaiku': 'claude-3-haiku',
        'claude3haiku': 'claude-3-haiku',
        'claude-3haiku': 'claude-3-haiku',
        'claude35sonnet': 'claude-3-5-sonnet',
        'claude-35-sonnet': 'claude-3-5-sonnet',
        'claude3.5sonnet': 'claude-3-5-sonnet',
        
        # Gemini variations
        'geminipro': 'gemini-pro',
        'gemini1.5pro': 'gemini-1.5-pro',
        'gemini15pro': 'gemini-1.5-pro',
        'gemini-15-pro': 'gemini-1.5-pro',
    }
    
    # Check direct mappings first
    if name in typo_patterns:
        return typo_patterns[name]
    
    # Auto-fix patterns for GPT models
    if 'gpt' in name and '-' not in name:
        # Handle patterns like gpt4o, gpt35turbo
        if re.match(r'gpt4o', name):
            if 'mini' in name:
                return 'gpt-4o-mini'
            else:
                return 'gpt-4o'
        elif re.match(r'gpt35', name) or re.match(r'gpt3\.5', name):
            return 'gpt-3.5-turbo'
        elif re.match(r'gpt4\b', name):
            return 'gpt-4'
    
    # Auto-fix patterns for Claude models
    if 'claude' in name and re.match(r'claude\d', name):
        # Handle patterns like claude3opus, claude35sonnet
        if 'opus' in name:
            return 'claude-3-opus'
        elif 'sonnet' in name:
            if '35' in name or '3.5' in name:
                return 'claude-3-5-sonnet'
            else:
                return 'claude-3-sonnet'
        elif 'haiku' in name:
            return 'claude-3-haiku'
    
    # Auto-fix patterns for Gemini models
    if 'gemini' in name and '-' not in name:
        if '1.5' in name or '15' in name:
            return 'gemini-1.5-pro'
        elif 'pro' in name:
            return 'gemini-pro'
    
    # Return original if no pattern matches
    return model_name


def find_similar_models(model_name: str, available_models: List[str]) -> List[Tuple[str, float]]:
    """Find similar model names for suggestions using simple string matching."""
    if not model_name or not available_models:
        return []
    
    name_lower = model_name.lower().strip()
    suggestions = []
    
    for model in available_models:
        model_lower = model.lower()
        
        # Exact match (shouldn't happen if we're here, but just in case)
        if name_lower == model_lower:
            suggestions.append((model, 1.0))
            continue
        
        # Substring match
        if name_lower in model_lower or model_lower in name_lower:
            # Longer matches get higher scores
            overlap = len(set(name_lower) & set(model_lower))
            score = overlap / max(len(name_lower), len(model_lower))
            suggestions.append((model, score + 0.3))  # Boost substring matches
            continue
        
        # Character overlap
        common_chars = len(set(name_lower) & set(model_lower))
        total_chars = len(set(name_lower) | set(model_lower))
        if total_chars > 0:
            score = common_chars / total_chars
            if score > 0.4:  # Only suggest if reasonably similar
                suggestions.append((model, score))
    
    # Sort by score descending and return top 3
    suggestions.sort(key=lambda x: x[1], reverse=True)
    return suggestions[:3]


def get_suggestion_message(original_name: str, available_models: List[str]) -> Optional[str]:
    """Generate a helpful error message with model suggestions."""
    suggestions = find_similar_models(original_name, available_models)
    
    if not suggestions:
        return f"Model '{original_name}' not supported. Check /models for available models."
    
    if len(suggestions) == 1:
        return f"Model '{original_name}' not found. Did you mean '{suggestions[0][0]}'?"
    
    suggestion_names = [s[0] for s in suggestions]
    return f"Model '{original_name}' not found. Did you mean: {', '.join(suggestion_names)}?"