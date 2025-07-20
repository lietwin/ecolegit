"""Model discovery and matching services."""

import logging
import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a discovered model."""
    name: str
    provider: str
    available: bool
    aliases: List[str]


@dataclass
class ModelMatch:
    """Result of model name matching."""
    matched_name: str
    original_name: str
    confidence: float
    match_type: str  # exact, fuzzy, transform


class ModelDiscoveryService:
    """Service for discovering and matching model names dynamically."""
    
    def __init__(self, ecologits_repo, cache_ttl_seconds: int = 3600):
        self._ecologits_repo = ecologits_repo
        self._cache_ttl = cache_ttl_seconds
        self._models_cache: Dict[str, ModelInfo] = {}
        self._cache_timestamp = 0
        self._common_transforms = {
            # Common user input variations to standard names
            'gpt4o': 'gpt-4o',
            'gpt4o-mini': 'gpt-4o-mini', 
            'gpt35-turbo': 'gpt-3.5-turbo',
            'gpt-35-turbo': 'gpt-3.5-turbo',
            'claude3-opus': 'claude-3-opus',
            'claude3-sonnet': 'claude-3-sonnet',
            'claude3-haiku': 'claude-3-haiku',
            'claude35-sonnet': 'claude-3-5-sonnet',
        }
    
    def discover_models(self, force_refresh: bool = False) -> Dict[str, ModelInfo]:
        """Discover available models from EcoLogits."""
        current_time = time.time()
        
        # Check cache validity
        if (not force_refresh and 
            self._models_cache and 
            (current_time - self._cache_timestamp) < self._cache_ttl):
            return self._models_cache
        
        try:
            logger.info("Discovering models from EcoLogits...")
            available_models = self._ecologits_repo.get_available_models()
            
            self._models_cache = {}
            for model_name, model_obj in available_models.items():
                # Extract provider from model name or object
                provider = self._extract_provider(model_name)
                
                self._models_cache[model_name] = ModelInfo(
                    name=model_name,
                    provider=provider,
                    available=True,
                    aliases=self._generate_aliases(model_name)
                )
            
            self._cache_timestamp = current_time
            logger.info(f"Discovered {len(self._models_cache)} models")
            return self._models_cache
            
        except Exception as e:
            logger.error(f"Failed to discover models: {e}")
            # Return cached models if available, otherwise empty dict
            return self._models_cache or {}
    
    def find_best_match(self, user_input: str) -> Optional[ModelMatch]:
        """Find the best matching model for user input."""
        models = self.discover_models()
        
        if not models:
            return None
        
        user_input_lower = user_input.lower().strip()
        model_names = list(models.keys())
        
        # 1. Exact match
        for model_name in model_names:
            if model_name.lower() == user_input_lower:
                return ModelMatch(
                    matched_name=model_name,
                    original_name=user_input,
                    confidence=1.0,
                    match_type="exact"
                )
        
        # 2. Check aliases
        for model_name, model_info in models.items():
            for alias in model_info.aliases:
                if alias.lower() == user_input_lower:
                    return ModelMatch(
                        matched_name=model_name,
                        original_name=user_input,
                        confidence=0.95,
                        match_type="alias"
                    )
        
        # 3. Common transforms
        transformed = self._common_transforms.get(user_input_lower)
        if transformed:
            for model_name in model_names:
                if model_name.lower() == transformed.lower():
                    return ModelMatch(
                        matched_name=model_name,
                        original_name=user_input,
                        confidence=0.9,
                        match_type="transform"
                    )
        
        # 4. Fuzzy matching
        best_match = None
        best_score = 0.0
        
        for model_name in model_names:
            score = SequenceMatcher(None, user_input_lower, model_name.lower()).ratio()
            if score > best_score and score >= 0.6:  # Minimum 60% similarity
                best_score = score
                best_match = model_name
        
        if best_match:
            return ModelMatch(
                matched_name=best_match,
                original_name=user_input,
                confidence=best_score,
                match_type="fuzzy"
            )
        
        return None
    
    def get_supported_models(self) -> List[str]:
        """Get list of all supported model names."""
        models = self.discover_models()
        return sorted(models.keys())
    
    def get_models_by_provider(self) -> Dict[str, List[str]]:
        """Get models grouped by provider."""
        models = self.discover_models()
        by_provider = {}
        
        for model_name, model_info in models.items():
            provider = model_info.provider
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(model_name)
        
        # Sort each provider's models
        for provider in by_provider:
            by_provider[provider].sort()
        
        return by_provider
    
    def search_models(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Search for models matching the query."""
        models = self.discover_models()
        query_lower = query.lower().strip()
        
        if not query_lower:
            return [(name, 1.0) for name in sorted(models.keys())[:limit]]
        
        matches = []
        for model_name in models.keys():
            # Check exact substring match first
            if query_lower in model_name.lower():
                score = len(query_lower) / len(model_name)  # Longer matches get lower scores
                matches.append((model_name, min(score + 0.5, 1.0)))  # Boost substring matches
            else:
                # Fuzzy match
                score = SequenceMatcher(None, query_lower, model_name.lower()).ratio()
                if score >= 0.3:  # Lower threshold for search
                    matches.append((model_name, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
    
    def _extract_provider(self, model_name: str) -> str:
        """Extract provider name from model name."""
        model_lower = model_name.lower()
        
        if model_lower.startswith(('gpt', 'davinci', 'curie', 'babbage', 'ada')):
            return 'openai'
        elif model_lower.startswith('claude'):
            return 'anthropic'
        elif model_lower.startswith(('gemini', 'palm', 'bison')):
            return 'google'
        elif model_lower.startswith(('command', 'embed')):
            return 'cohere'
        elif model_lower.startswith(('mistral', 'mixtral')):
            return 'mistral'
        else:
            return 'unknown'
    
    def _generate_aliases(self, model_name: str) -> List[str]:
        """Generate common aliases for a model name."""
        aliases = []
        
        # Add version without hyphens
        no_hyphens = model_name.replace('-', '')
        if no_hyphens != model_name:
            aliases.append(no_hyphens)
        
        # Add common abbreviations
        if 'turbo' in model_name:
            aliases.append(model_name.replace('turbo', ''))
        
        # Add version-stripped names for versioned models
        if any(char.isdigit() for char in model_name):
            # Remove dates and version numbers
            import re
            base_name = re.sub(r'-?\d{4}-?\d{2}-?\d{2}', '', model_name)
            base_name = re.sub(r'-?\d{3,4}$', '', base_name)
            if base_name != model_name and base_name:
                aliases.append(base_name)
        
        return aliases
    
    def refresh_cache(self) -> Dict[str, ModelInfo]:
        """Force refresh of model cache."""
        return self.discover_models(force_refresh=True)