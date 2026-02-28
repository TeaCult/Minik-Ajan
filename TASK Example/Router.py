"""
OpenRouter Tiered Cost-Effective Model Router
=============================================
A comprehensive routing system for OpenRouter that selects the most 
cost-effective models across different modalities and requirements.

Sources:
- Pricing: https://llmtokencost.com (312 models from 55 providers)
- Performance: https://arena.ai/leaderboard
- Free Models: https://openrouter.ai/collections/free-models
- Fallback Docs: https://openrouter.ai/docs/guides/routing/model-fallbacks

Author: AI Router Generator
Date: 2025
"""

import os
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal, Union
from enum import Enum
import requests


class Tier(Enum):
    """Cost tiers for models based on input $/1M tokens"""
    FREE = "free"              # $0 (rate limited)
    ULTRA_LOW = "ultra_low"    # < $0.20
    LOW = "low"                # $0.20 - $0.60
    MID = "mid"                # $0.60 - $3.00
    HIGH = "high"              # $3.00 - $10.00
    PREMIUM = "premium"        # > $10.00


class Modality(Enum):
    """Supported modalities"""
    TEXT = "text"
    VISION = "vision"
    AUDIO = "audio"
    CODE = "code"
    REASONING = "reasoning"
    MULTIMODAL = "multimodal"


class ReasoningLevel(Enum):
    """Reasoning requirements"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    model_id: str
    cost_input: float           # $ per 1M input tokens
    cost_output: float          # $ per 1M output tokens
    context_window: int
    tier: Tier
    modalities: List[Modality]
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    arena_rank: Optional[int] = None
    fallback_models: List[str] = field(default_factory=list)
    
    @property
    def avg_cost(self) -> float:
        """Average cost per 1M tokens"""
        return (self.cost_input + self.cost_output) / 2


class ModelRegistry:
    """Registry of cost-effective OpenRouter models by tier and modality"""
    
    # TIER 0: FREE (Rate limited, great for testing/budget constraints)
    FREE_MODELS: Dict[str, ModelConfig] = {
        "openrouter/free": ModelConfig(
            model_id="openrouter/free",
            cost_input=0.0, cost_output=0.0,
            context_window=200000, tier=Tier.FREE,
            modalities=[Modality.TEXT, Modality.MULTIMODAL],
            strengths=["auto_selection", "zero_cost", "good_for_testing"],
            fallback_models=[
                "openai/gpt-oss-120b:free",
                "qwen/qwen3-235b-a22b-thinking-2507:free",
                "nvidia/llama-3.1-nemotron-30b-a3b:free"
            ]
        ),
        "openai/gpt-oss-120b:free": ModelConfig(
            model_id="openai/gpt-oss-120b:free",
            cost_input=0.0, cost_output=0.0,
            context_window=131072, tier=Tier.FREE,
            modalities=[Modality.TEXT, Modality.CODE, Modality.REASONING],
            strengths=["117B_MoE", "configurable_reasoning", "open_weights"],
            arena_rank=None,
            fallback_models=[
                "nvidia/llama-3.1-nemotron-30b-a3b:free",
                "z-ai/glm-4.5-air:free"
            ]
        ),
        "qwen/qwen3-235b-a22b-thinking-2507:free": ModelConfig(
            model_id="qwen/qwen3-235b-a22b-thinking-2507:free",
            cost_input=0.0, cost_output=0.0,
            context_window=262144, tier=Tier.FREE,
            modalities=[Modality.TEXT, Modality.CODE, Modality.REASONING],
            strengths=["235B_MoE", "22B_active", "260K_context", "math", "logic", "STEM"],
            arena_rank=None,
            fallback_models=[
                "qwen/qwen3-vl-235b-a22b-thinking:free",
                "upstage/solar-pro-3:free"
            ]
        ),
        "qwen/qwen3-vl-235b-a22b-thinking:free": ModelConfig(
            model_id="qwen/qwen3-vl-235b-a22b-thinking:free",
            cost_input=0.0, cost_output=0.0,
            context_window=131072, tier=Tier.FREE,
            modalities=[Modality.VISION, Modality.MULTIMODAL, Modality.REASONING],
            strengths=["multimodal", "vision_reasoning", "document_OCR", "STEM"],
            fallback_models=[
                "nvidia/nemotron-nano-12b-2-vl:free",
                "qwen/qwen3-vl-30b-a3b-thinking:free"
            ]
        ),
        "nvidia/nemotron-nano-12b-2-vl:free": ModelConfig(
            model_id="nvidia/nemotron-nano-12b-2-vl:free",
            cost_input=0.0, cost_output=0.0,
            context_window=81920, tier=Tier.FREE,
            modalities=[Modality.VISION, Modality.MULTIMODAL],
            strengths=["video_understanding", "document_intelligence", "transformer_mamba"],
            fallback_models=[
                "qwen/qwen3-vl-235b-a22b-thinking:free"
            ]
        ),
        "nvidia/llama-3.1-nemotron-30b-a3b:free": ModelConfig(
            model_id="nvidia/llama-3.1-nemotron-30b-a3b:free",
            cost_input=0.0, cost_output=0.0,
            context_window=131072, tier=Tier.FREE,
            modalities=[Modality.TEXT, Modality.CODE],
            strengths=["30B_MoE", "agentic_specialized", "long_context"],
            fallback_models=[
                "z-ai/glm-4.5-air:free",
                "arcee-ai/trinity-mini:free"
            ]
        ),
        "z-ai/glm-4.5-air:free": ModelConfig(
            model_id="z-ai/glm-4.5-air:free",
            cost_input=0.0, cost_output=0.0,
            context_window=131072, tier=Tier.FREE,
            modalities=[Modality.TEXT, Modality.REASONING],
            strengths=["agentic", "thinking_mode", "open_weights"],
            fallback_models=[
                "arcee-ai/trinity-large-preview:free"
            ]
        ),
        "arcee-ai/trinity-large-preview:free": ModelConfig(
            model_id="arcee-ai/trinity-large-preview:free",
            cost_input=0.0, cost_output=0.0,
            context_window=131072, tier=Tier.FREE,
            modalities=[Modality.TEXT, Modality.MULTIMODAL],
            strengths=["400B_MoE", "13B_active", "512K_context", "creative_writing", "voice"],
            fallback_models=[
                "stepfun/step-3.5-flash:free"
            ]
        ),
        "stepfun/step-3.5-flash:free": ModelConfig(
            model_id="stepfun/step-3.5-flash:free",
            cost_input=0.0, cost_output=0.0,
            context_window=262144, tier=Tier.FREE,
            modalities=[Modality.TEXT, Modality.REASONING],
            strengths=["196B_MoE", "11B_active", "long_context", "speed_efficient"],
            fallback_models=[]
        ),
    }
    
    # TIER 1: ULTRA LOW COST (< $0.20/m input)
    ULTRA_LOW_MODELS: Dict[str, ModelConfig] = {
        "qwen/qwen-turbo": ModelConfig(
            model_id="qwen/qwen-turbo",
            cost_input=0.05, cost_output=0.20,
            context_window=131072, tier=Tier.ULTRA_LOW,
            modalities=[Modality.TEXT],
            strengths=["fast", "qwen_ecosystem", "reliable"],
            fallback_models=[
                "qwen/qwen-2.5-7b-instruct",
                "google/gemma-3-4b-it"
            ]
        ),
        "qwen/qwen-2.5-7b-instruct": ModelConfig(
            model_id="qwen/qwen-2.5-7b-instruct",
            cost_input=0.04, cost_output=0.10,
            context_window=32768, tier=Tier.ULTRA_LOW,
            modalities=[Modality.TEXT, Modality.CODE],
            strengths=["compact", "fast_inference", "qwen_framework"],
            fallback_models=[
                "qwen/qwen-2.5-coder-7b-instruct"
            ]
        ),
        "qwen/qwen-2.5-coder-7b-instruct": ModelConfig(
            model_id="qwen/qwen-2.5-coder-7b-instruct",
            cost_input=0.03, cost_output=0.09,
            context_window=32768, tier=Tier.ULTRA_LOW,
            modalities=[Modality.CODE],
            strengths=["code_specialized", "7B_parameters", "very_cheap"],
            fallback_models=[
                "qwen/qwen-turbo"
            ]
        ),
        "google/gemini-2.0-flash-lite-001": ModelConfig(
            model_id="google/gemini-2.0-flash-lite-001",
            cost_input=0.075, cost_output=0.30,
            context_window=1000000, tier=Tier.ULTRA_LOW,
            modalities=[Modality.TEXT, Modality.MULTIMODAL],
            strengths=["1M_context", "google_quality", "speed"],
            fallback_models=[
                "google/gemini-2.0-flash-001",
                "openai/gpt-4o-mini"
            ]
        ),
        "google/gemma-3-4b-it": ModelConfig(
            model_id="google/gemma-3-4b-it",
            cost_input=0.04, cost_output=0.08,
            context_window=131072, tier=Tier.ULTRA_LOW,
            modalities=[Modality.TEXT],
            strengths=["4B_parameters", "open_weights", "google"],
            fallback_models=[]
        ),
    }
    
    # TIER 2: LOW COST ($0.20 - $0.60/m input)
    LOW_COST_MODELS: Dict[str, ModelConfig] = {
        "openai/gpt-4o-mini": ModelConfig(
            model_id="openai/gpt-4o-mini",
            cost_input=0.15, cost_output=0.60,
            context_window=128000, tier=Tier.LOW,
            modalities=[Modality.TEXT, Modality.VISION, Modality.AUDIO],
            strengths=["reliable", "vision", "openai_quality", "tool_use"],
            fallback_models=[
                "google/gemini-2.0-flash-001",
                "qwen/qwen-turbo"
            ]
        ),
        "google/gemini-2.0-flash-001": ModelConfig(
            model_id="google/gemini-2.0-flash-001",
            cost_input=0.10, cost_output=0.40,
            context_window=1000000, tier=Tier.LOW,
            modalities=[Modality.TEXT, Modality.VISION, Modality.MULTIMODAL],
            strengths=["1M_context", "fast", "multimodal", "workspace_native"],
            arena_rank=113,
            fallback_models=[
                "openai/gpt-4o-mini",
                "x-ai/grok-3-mini"
            ]
        ),
        "anthropic/claude-3-haiku": ModelConfig(
            model_id="anthropic/claude-3-haiku",
            cost_input=0.25, cost_output=1.25,
            context_window=200000, tier=Tier.LOW,
            modalities=[Modality.TEXT, Modality.VISION],
            strengths=["200K_context", "anthropic_reliability", "haiku_quality"],
            fallback_models=[
                "openai/gpt-4o-mini",
                "google/gemini-2.0-flash-001"
            ]
        ),
        "x-ai/grok-3-mini": ModelConfig(
            model_id="x-ai/grok-3-mini",
            cost_input=0.30, cost_output=0.50,
            context_window=131072, tier=Tier.LOW,
            modalities=[Modality.TEXT],
            strengths=["realtime", "x_data", "fast"],
            fallback_models=[
                "qwen/qwen-turbo",
                "google/gemini-2.0-flash-001"
            ]
        ),
        "x-ai/grok-3-mini-beta": ModelConfig(
            model_id="x-ai/grok-3-mini-beta",
            cost_input=0.30, cost_output=0.50,
            context_window=131072, tier=Tier.LOW,
            modalities=[Modality.TEXT],
            strengths=["realtime", "x_data_beta"],
            fallback_models=[
                "x-ai/grok-3-mini"
            ]
        ),
        "openai/gpt-4.1-mini": ModelConfig(
            model_id="openai/gpt-4.1-mini",
            cost_input=0.40, cost_output=1.60,
            context_window=1000000, tier=Tier.LOW,
            modalities=[Modality.TEXT, Modality.VISION],
            strengths=["1M_context", "openai_reliable", "improved_over_4o_mini"],
            fallback_models=[
                "openai/gpt-4o-mini"
            ]
        ),
        "qwen/qwen-plus": ModelConfig(
            model_id="qwen/qwen-plus",
            cost_input=0.40, cost_output=1.20,
            context_window=1000000, tier=Tier.LOW,
            modalities=[Modality.TEXT, Modality.CODE],
            strengths=["1M_context", "qwen_plus_quality", "reasoning"],
            fallback_models=[
                "qwen/qwen-turbo"
            ]
        ),
        "google/gemini-2.5-flash-lite": ModelConfig(
            model_id="google/gemini-2.5-flash-lite",
            cost_input=0.10, cost_output=0.40,
            context_window=1000000, tier=Tier.LOW,
            modalities=[Modality.TEXT, Modality.MULTIMODAL],
            strengths=["1M_context", "thinking_available", "cost_efficient"],
            fallback_models=[
                "google/gemini-2.0-flash-001"
            ]
        ),
    }
    
    # TIER 3: MID COST ($0.60 - $3.00/m input)
    MID_COST_MODELS: Dict[str, ModelConfig] = {
        "google/gemini-2.5-flash": ModelConfig(
            model_id="google/gemini-2.5-flash",
            cost_input=0.30, cost_output=2.50,
            context_window=1000000, tier=Tier.MID,
            modalities=[Modality.TEXT, Modality.VISION, Modality.CODE, Modality.REASONING],
            strengths=["1M_context", "thinking", "fast", "multimodal", "excellent_balance"],
            arena_rank=63,
            fallback_models=[
                "google/gemini-2.5-pro",
                "anthropic/claude-3.5-haiku"
            ]
        ),
        "anthropic/claude-3.5-haiku": ModelConfig(
            model_id="anthropic/claude-3.5-haiku",
            cost_input=0.80, cost_output=4.00,
            context_window=200000, tier=Tier.MID,
            modalities=[Modality.TEXT],
            strengths=["improved_over_haiku", "instruction_following", "200K_context"],
            fallback_models=[
                "anthropic/claude-3-haiku",
                "anthropic/claude-sonnet-4.5"
            ]
        ),
        "anthropic/claude-sonnet-4-20250514": ModelConfig(
            model_id="anthropic/claude-sonnet-4-20250514",
            cost_input=3.00, cost_output=15.00,
            context_window=1000000, tier=Tier.MID,
            modalities=[Modality.TEXT, Modality.VISION, Modality.CODE],
            strengths=["1M_context", "coding", "reasoning", "agentic", "claude_quality"],
            fallback_models=[
                "anthropic/claude-sonnet-4.5",
                "anthropic/claude-3.5-sonnet"
            ]
        ),
        "moonshotai/kimi-k2.5-instant": ModelConfig(
            model_id="moonshotai/kimi-k2.5-instant",
            cost_input=0.40, cost_output=1.20,
            context_window=262144, tier=Tier.MID,
            modalities=[Modality.TEXT, Modality.CODE],
            strengths=["260K_context", "arena_competitive", "chinese_english"],
            arena_rank=33,
            fallback_models=[
                "qwen/qwen-plus"
            ]
        ),
        "openai/gpt-4o": ModelConfig(
            model_id="openai/gpt-4o",
            cost_input=2.50, cost_output=10.00,
            context_window=128000, tier=Tier.MID,
            modalities=[Modality.TEXT, Modality.VISION, Modality.AUDIO, Modality.MULTIMODAL],
            strengths=["omni_multimodal", "tool_use", "reliable", "vision"],
            fallback_models=[
                "openai/gpt-4.1",
                "anthropic/claude-sonnet-4.5"
            ]
        ),
    }
    
    # TIER 4: HIGH COST ($3.00 - $10.00/m input)
    HIGH_COST_MODELS: Dict[str, ModelConfig] = {
        "google/gemini-2.5-pro": ModelConfig(
            model_id="google/gemini-2.5-pro",
            cost_input=1.25, cost_output=10.00,
            context_window=1000000, tier=Tier.HIGH,
            modalities=[Modality.TEXT, Modality.VISION, Modality.CODE, Modality.REASONING, Modality.MULTIMODAL],
            strengths=["1M_context", "arena_22", "vision_1", "stem", "excellent"],
            arena_rank=22,
            fallback_models=[
                "google/gemini-3-pro",
                "anthropic/claude-sonnet-4.5"
            ]
        ),
        "google/gemini-3-pro": ModelConfig(
            model_id="google/gemini-3-pro",
            cost_input=2.00, cost_output=12.00,
            context_window=1000000, tier=Tier.HIGH,
            modalities=[Modality.TEXT, Modality.VISION, Modality.CODE, Modality.MULTIMODAL],
            strengths=["text_5", "vision_1", "gemini_frontier", "multimodal_leader"],
            arena_rank=5,  # Text
            fallback_models=[
                "google/gemini-2.5-pro",
                "anthropic/claude-opus-4.6"
            ]
        ),
        "google/gemini-3.1-pro-preview": ModelConfig(
            model_id="google/gemini-3.1-pro-preview",
            cost_input=2.00, cost_output=12.00,
            context_window=1000000, tier=Tier.HIGH,
            modalities=[Modality.TEXT, Modality.VISION, Modality.CODE, Modality.MULTIMODAL],
            strengths=["text_3", "arena_top", "gemini_latest"],
            arena_rank=3,
            fallback_models=[
                "google/gemini-3-pro",
                "openai/gpt-5.1"
            ]
        ),
        "anthropic/claude-sonnet-4.5": ModelConfig(
            model_id="anthropic/claude-sonnet-4.5",
            cost_input=3.00, cost_output=15.00,
            context_window=200000, tier=Tier.HIGH,
            modalities=[Modality.TEXT, Modality.VISION, Modality.CODE],
            strengths=["code_4", "claude_quality", "coding_excellence", "vision"],
            arena_rank=4,  # Code
            fallback_models=[
                "anthropic/claude-sonnet-4-20250514",
                "google/gemini-3.1-pro-preview"
            ]
        ),
        "openai/gpt-5": ModelConfig(
            model_id="openai/gpt-5",
            cost_input=1.25, cost_output=10.00,
            context_window=400000, tier=Tier.HIGH,
            modalities=[Modality.TEXT, Modality.VISION, Modality.CODE, Modality.REASONING],
            strengths=["400K_context", "gpt_frontier", "improved_reasoning"],
            fallback_models=[
                "openai/gpt-5.1",
                "anthropic/claude-opus-4.6"
            ]
        ),
        "openai/gpt-5.1": ModelConfig(
            model_id="openai/gpt-5.1",
            cost_input=1.25, cost_output=10.00,
            context_window=400000, tier=Tier.HIGH,
            modalities=[Modality.TEXT, Modality.VISION, Modality.CODE],
            strengths=["gpt_latest", "400K_context", "multimodal"],
            fallback_models=[
                "openai/gpt-5",
                "google/gemini-3-pro"
            ]
        ),
    }
    
    # TIER 5: PREMIUM (> $10.00/m input)
    PREMIUM_MODELS: Dict[str, ModelConfig] = {
        "anthropic/claude-opus-4.6": ModelConfig(
            model_id="anthropic/claude-opus-4.6",
            cost_input=5.00, cost_output=25.00,
            context_window=200000, tier=Tier.PREMIUM,
            modalities=[Modality.TEXT, Modality.VISION, Modality.CODE, Modality.REASONING],
            strengths=["text_1", "code_1", "arena_champion", "best_quality", "complex_reasoning"],
            arena_rank=1,
            fallback_models=[
                "anthropic/claude-opus-4-6-thinking",
                "google/gemini-3-pro"
            ]
        ),
        "anthropic/claude-opus-4-6-thinking": ModelConfig(
            model_id="anthropic/claude-opus-4-6-thinking",
            cost_input=5.00, cost_output=25.00,
            context_window=200000, tier=Tier.PREMIUM,
            modalities=[Modality.TEXT, Modality.CODE, Modality.REASONING],
            strengths=["extended_thinking", "best_coding", "deep_reasoning", "arena_1"],
            arena_rank=1,
            fallback_models=[
                "anthropic/claude-opus-4-6",
                "openai/o1"
            ]
        ),
        "openai/gpt-5-pro": ModelConfig(
            model_id="openai/gpt-5-pro",
            cost_input=15.00, cost_output=120.00,
            context_window=400000, tier=Tier.PREMIUM,
            modalities=[Modality.TEXT, Modality.VISION, Modality.REASONING],
            strengths=["highest_gpt_quality", "expert_tasks", "premium"],
            fallback_models=[
                "anthropic/claude-opus-4.6",
                "openai/o1-pro"
            ]
        ),
        "openai/o1": ModelConfig(
            model_id="openai/o1",
            cost_input=15.00, cost_output=60.00,
            context_window=200000, tier=Tier.PREMIUM,
            modalities=[Modality.TEXT, Modality.REASONING],
            strengths=["reasoning_specialist", "math", "science", "logic"],
            fallback_models=[
                "openai/o1-pro",
                "anthropic/claude-opus-4-6-thinking"
            ]
        ),
        "openai/o1-pro": ModelConfig(
            model_id="openai/o1-pro",
            cost_input=150.00, cost_output=600.00,
            context_window=200000, tier=Tier.PREMIUM,
            modalities=[Modality.TEXT, Modality.REASONING],
            strengths=["maximum_reasoning", "most_careful"],
            fallback_models=[
                "openai/o1",
                "anthropic/claude-opus-4.6"
            ]
        ),
        "google/gemini-3.1-pro-preview-customtools": ModelConfig(
            model_id="google/gemini-3.1-pro-preview-customtools",
            cost_input=2.00, cost_output=12.00,
            context_window=1000000, tier=Tier.HIGH,
            modalities=[Modality.TEXT, Modality.CODE, Modality.REASONING],
            strengths=["custom_tools", "advanced_agentic"],
            fallback_models=[
                "google/gemini-3.1-pro-preview"
            ]
        ),
    }
    
    # Merged registry
    ALL_MODELS: Dict[str, ModelConfig] = {}
    
    def __init__(self):
        self.ALL_MODELS = {}
        self.ALL_MODELS.update(self.FREE_MODELS)
        self.ALL_MODELS.update(self.ULTRA_LOW_MODELS)
        self.ALL_MODELS.update(self.LOW_COST_MODELS)
        self.ALL_MODELS.update(self.MID_COST_MODELS)
        self.ALL_MODELS.update(self.HIGH_COST_MODELS)
        self.ALL_MODELS.update(self.PREMIUM_MODELS)
    
    def get_models_by_tier(self, tier: Tier) -> List[ModelConfig]:
        """Get all models in a specific tier"""
        return [m for m in self.ALL_MODELS.values() if m.tier == tier]
    
    def get_models_by_modality(self, modality: Modality, tier: Optional[Tier] = None) -> List[ModelConfig]:
        """Get models supporting a specific modality, optionally filtered by tier"""
        models = [m for m in self.ALL_MODELS.values() if modality in m.modalities]
        if tier:
            models = [m for m in models if m.tier.value == tier.value]
        return models
    
    def get_cheapest_for_modality(self, modality: Modality) -> Optional[ModelConfig]:
        """Get cheapest model for a modality"""
        models = self.get_models_by_modality(modality)
        if not models:
            return None
        return min(models, key=lambda m: m.cost_input)
    
    def get_best_for_code(self, max_tier: Tier = Tier.PREMIUM) -> ModelConfig:
        """Get the best available model for code tasks within tier limit"""
        # Based on arena.ai rankings
        code_rankings = [
            "anthropic/claude-opus-4-6-thinking",
            "anthropic/claude-opus-4.6",
            "anthropic/claude-sonnet-4.6",
            "anthropic/claude-sonnet-4-20250514",
            "google/gemini-3.1-pro-preview",
        ]
        for model_id in code_rankings:
            if model_id in self.ALL_MODELS:
                model = self.ALL_MODELS[model_id]
                # Check if within tier limit
                tier_order = [t.value for t in Tier]
                if tier_order.index(model.tier.value) <= tier_order.index(max_tier.value):
                    return model
        # Fallback to cheapest available
        return self.get_cheapest_for_modality(Modality.CODE)
    
    def get_best_for_vision(self, max_tier: Tier = Tier.PREMIUM) -> ModelConfig:
        """Get the best available model for vision tasks within tier limit"""
        # Based on arena.ai vision rankings
        vision_rankings = [
            "google/gemini-3-pro",
            "google/gemini-3.1-pro-preview",
            "google/gemini-3-flash",
            "openai/gpt-5.2-chat-latest",
            "moonshotai/kimi-k2.5-thinking",
        ]
        for model_id in vision_rankings:
            if model_id in self.ALL_MODELS:
                model = self.ALL_MODELS[model_id]
                if modality.VISION in model.modalities:
                    tier_order = [t.value for t in Tier]
                    if tier_order.index(model.tier.value) <= tier_order.index(max_tier.value):
                        return model
        # Fallback to cheapest vision model
        return self.get_cheapest_for_modality(Modality.VISION)


class CostOptimizedRouter:
    """
    Intelligent router for OpenRouter that optimizes cost while maintaining quality.
    
    Features:
    - Tier-based model selection
    - Automatic fallback cascades
    - Modality-aware routing
    - Reasoning requirement handling
    - Cost tracking and budgeting
    - Provider preference support
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_tier: Tier = Tier.LOW,
        max_budget_per_request: Optional[float] = None,
        provider_preferences: Optional[Dict] = None
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key required. Set OPENROUTER_API_KEY env var.")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.registry = ModelRegistry()
        self.default_tier = default_tier
        self.max_budget = max_budget_per_request
        self.provider_prefs = provider_preferences or {}
        
        # Cost tracking
        self.total_cost = 0.0
        self.total_tokens = 0
        self.request_count = 0
    
    def select_model(
        self,
        modality: Modality = Modality.TEXT,
        reasoning_level: ReasoningLevel = ReasoningLevel.NONE,
        context_length: int = 8192,
        required_capabilities: Optional[List[str]] = None,
        max_tier: Optional[Tier] = None,
        prefer_arena_rank: bool = False
    ) -> ModelConfig:
        """
        Select the most cost-effective model for requirements
        
        Args:
            modality: Primary modality (text, vision, audio, code, reasoning)
            reasoning_level: Required reasoning depth
            context_length: Needed context window size
            required_capabilities: List of required features (e.g., ['function_calling'])
            max_tier: Maximum tier allowed
            prefer_arena_rank: Prioritize arena ranking over pure cost
        """
        max_tier = max_tier or self.default_tier
        
        # Get candidates
        candidates = self.registry.get_models_by_modality(modality)
        
        # Filter by tier
        tier_order = [Tier.FREE, Tier.ULTRA_LOW, Tier.LOW, Tier.MID, Tier.HIGH, Tier.PREMIUM]
        max_idx = tier_order.index(max_tier)
        candidates = [m for m in candidates if tier_order.index(m.tier) <= max_idx]
        
        # Filter by context length
        candidates = [m for m in candidates if m.context_window >= context_length]
        
        # Filter by reasoning requirement
        if reasoning_level == ReasoningLevel.HIGH or reasoning_level == ReasoningLevel.EXTREME:
            candidates = [m for m in candidates if Modality.REASONING in m.modalities]
        
        if not candidates:
            # Fallback: expand to higher tier or budget tier
            candidates = self._get_fallback_candidates(modality, context_length)
        
        # Sort by cost, or by arena rank if preferred
        if prefer_arena_rank:
            candidates = sorted(candidates, key=lambda m: (m.arena_rank or 999, m.cost_input))
        else:
            candidates = sorted(candidates, key=lambda m: m.cost_input)
        
        return candidates[0] if candidates else self.registry.ALL_MODELS["openai/gpt-4o-mini"]
    
    def _get_fallback_candidates(self, modality: Modality, context_length: int) -> List[ModelConfig]:
        """Get fallback candidates when primary selection fails"""
        # Try next tier up
        all_candidates = self.registry.get_models_by_modality(modality)
        return [m for m in all_candidates if m.context_window >= context_length]
    
    def build_fallback_chain(
        self,
        primary_model: str,
        chain_length: int = 3,
        mix_tiers: bool = True
    ) -> List[str]:
        """
        Build a fallback chain of models
        
        Args:
            primary_model: Primary model ID
            chain_length: Number of fallbacks to include
            mix_tiers: Include cheaper alternatives if primary is expensive
        """
        if primary_model not in self.registry.ALL_MODELS:
            return [primary_model]
        
        primary = self.registry.ALL_MODELS[primary_model]
        chain = [primary_model]
        
        # Add model's defined fallbacks
        for fallback in primary.fallback_models[:chain_length]:
            if fallback in self.registry.ALL_MODELS and fallback not in chain:
                chain.append(fallback)
        
        # Add tier-based fallbacks
        if mix_tiers and len(chain) < chain_length:
            tier_idx = [t.value for t in Tier].index(primary.tier.value)
            # Look at current and lower tiers
            for tier_value in [t.value for t in Tier][:tier_idx+1]:
                for model_id, model in self.registry.ALL_MODELS.items():
                    if model.tier.value == tier_value and model_id not in chain:
                        # Check modality overlap
                        if any(m in primary.modalities for m in model.modalities):
                            chain.append(model_id)
                            if len(chain) >= chain_length:
                                return chain
        
        return chain
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        modality: Modality = Modality.TEXT,
        reasoning_level: ReasoningLevel = ReasoningLevel.NONE,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        tier: Optional[Tier] = None,
        use_fallbacks: bool = True,
        **kwargs
    ) -> Dict:
        """
        Send chat completion request with automatic model selection and fallbacks
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            modality: Required modality
            reasoning_level: Reasoning complexity needed
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            tier: Preferred cost tier
            use_fallbacks: Enable automatic fallback chain
            **kwargs: Additional API parameters
        """
        # Select best model
        max_tier = tier or self.default_tier
        model = self.select_model(
            modality=modality,
            reasoning_level=reasoning_level,
            max_tier=max_tier
        )
        
        # Build request
        models = self.build_fallback_chain(model.model_id) if use_fallbacks else [model.model_id]
        
        payload = {
            "model": models[0],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if len(models) > 1:
            payload["models"] = models
        
        # Add OpenRouter specific options
        if self.provider_prefs:
            payload["provider"] = self.provider_prefs
        
        payload.update(kwargs)
        
        # Make request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": kwargs.get("referer", "https://app.local"),
            "X-OpenRouter-Title": kwargs.get("app_name", "CostOptimizedRouter")
        }
        
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        latency = time.time() - start_time
        
        response.raise_for_status()
        result = response.json()
        
        # Track costs
        self._track_cost(result, model)
        self.request_count += 1
        
        result['_router_metadata'] = {
            'model_used': result.get('model', models[0]),
            'fallback_chain': models,
            'latency_seconds': latency,
            'estimated_cost': self._estimate_cost(result, model)
        }
        
        return result
    
    def _track_cost(self, response: Dict, model: ModelConfig):
        """Track API usage costs"""
        usage = response.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        input_cost = (prompt_tokens / 1_000_000) * model.cost_input
        output_cost = (completion_tokens / 1_000_000) * model.cost_output
        
        self.total_cost += input_cost + output_cost
        self.total_tokens += prompt_tokens + completion_tokens
    
    def _estimate_cost(self, response: Dict, model: ModelConfig) -> Dict:
        """Estimate cost of the request"""
        usage = response.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        input_cost = (prompt_tokens / 1_000_000) * model.cost_input
        output_cost = (completion_tokens / 1_000_000) * model.cost_output
        
        return {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'input_cost_usd': input_cost,
            'output_cost_usd': output_cost,
            'total_cost_usd': input_cost + output_cost
        }
    
    def get_cost_report(self) -> Dict:
        """Get cost usage report"""
        return {
            'total_requests': self.request_count,
            'total_tokens': self.total_tokens,
            'total_cost_usd': round(self.total_cost, 6),
            'avg_cost_per_request': round(self.total_cost / max(self.request_count, 1), 6),
            'avg_tokens_per_request': round(self.total_tokens / max(self.request_count, 1), 2)
        }


class SpecializedRouters:
    """Pre-configured routers for specific use cases"""
    
    @staticmethod
    def free_router() -> CostOptimizedRouter:
        """Router configured for zero-cost operation using free models"""
        return CostOptimizedRouter(
            default_tier=Tier.FREE,
            provider_preferences={"require_parameters": True}
        )
    
    @staticmethod
    def ultra_budget_router() -> CostOptimizedRouter:
        """Router for ultra-low budget (< $0.20/M tokens)"""
        return CostOptimizedRouter(default_tier=Tier.ULTRA_LOW)
    
    @staticmethod
    def balanced_router() -> CostOptimizedRouter:
        """Router balancing cost and quality"""
        return CostOptimizedRouter(default_tier=Tier.LOW)
    
    @staticmethod
    def performance_router() -> CostOptimizedRouter:
        """Router optimized for performance, willing to pay more"""
        return CostOptimizedRouter(default_tier=Tier.HIGH)
    
    @staticmethod
    def coding_router() -> CostOptimizedRouter:
        """Router optimized for code generation"""
        router = CostOptimizedRouter(default_tier=Tier.MID)
        return router


# Dictionary of recommended tiers by use case
RECOMMENDED_CONFIGS = {
    "demo_prototyping": {
        "tier": Tier.FREE,
        "primary": "openrouter/free",
        "fallbacks": ["openai/gpt-oss-120b:free", "qwen/qwen3-235b-a22b-thinking-2507:free"]
    },
    "high_volume_text": {
        "tier": Tier.ULTRA_LOW,
        "primary": "qwen/qwen-turbo",
        "fallbacks": ["google/gemini-2.0-flash-lite-001", "openai/gpt-4o-mini"]
    },
    "balanced_chat": {
        "tier": Tier.LOW,
        "primary": "openai/gpt-4o-mini",
        "fallbacks": ["google/gemini-2.0-flash-001", "anthropic/claude-3-haiku"]
    },
    "coding_assistant": {
        "tier": Tier.MID,
        "primary": "anthropic/claude-sonnet-4-20250514",
        "fallbacks": ["google/gemini-2.5-flash", "openai/gpt-4o"]
    },
    "vision_analysis": {
        "tier": Tier.HIGH,
        "primary": "google/gemini-3-pro",
        "fallbacks": ["google/gemini-2.5-pro", "openai/gpt-4o"]
    },
    "critical_reasoning": {
        "tier": Tier.PREMIUM,
        "primary": "anthropic/claude-opus-4-6-thinking",
        "fallbacks": ["openai/o1", "anthropic/claude-opus-4.6"]
    }
}


def quick_route(
    messages: List[Dict[str, str]],
    use_case: str = "balanced_chat",
    api_key: Optional[str] = None
) -> Dict:
    """
    Quick convenience function for routing based on use case
    
    Available use cases:
    - demo_prototyping: Use free tier
    - high_volume_text: Use ultra-low cost for bulk processing
    - balanced_chat: Good balance of cost and quality
    - coding_assistant: Optimized for code
    - vision_analysis: For image/video understanding
    - critical_reasoning: Best quality for complex reasoning
    """
    config = RECOMMENDED_CONFIGS.get(use_case, RECOMMENDED_CONFIGS["balanced_chat"])
    
    router = CostOptimizedRouter(
        api_key=api_key,
        default_tier=config["tier"]
    )
    
    modality = Modality.VISION if use_case == "vision_analysis" else Modality.TEXT
    reasoning = (ReasoningLevel.HIGH 
                if use_case in ["critical_reasoning", "coding_assistant"] 
                else ReasoningLevel.NONE)
    
    return router.chat_completion(
        messages=messages,
        modality=modality,
        reasoning_level=reasoning
    )


# Example usage
if __name__ == "__main__":
    print("OpenRouter Tiered Cost-Effective Model Router")
    print("=" * 60)
    print("\nAvailable Tiers:")
    for tier in Tier:
        print(f"  {tier.name}: {tier.value}")
    
    print("\n" + "=" * 60)
    print("\nRecommended Configurations by Use Case:")
    for use_case, config in RECOMMENDED_CONFIGS.items():
        print(f"\n{use_case}:")
        print(f"  Tier: {config['tier']}")
        print(f"  Primary: {config['primary']}")
        print(f"  Fallbacks: {', '.join(config['fallbacks'][:2])}...")
    
    print("\n" + "=" * 60)
    print("\nSample Model Selections:")
    
    registry = ModelRegistry()
    test_cases = [
        (Modality.TEXT, ReasoningLevel.NONE, "Text (basic)"),
        (Modality.TEXT, ReasoningLevel.HIGH, "Text (high reasoning)"),
        (Modality.VISION, ReasoningLevel.NONE, "Vision"),
        (Modality.CODE, ReasoningLevel.MEDIUM, "Code"),
    ]
    
    router = CostOptimizedRouter(
        api_key=os.getenv("OPENROUTER_API_KEY", "demo_key")
    )
    
    for modality, reasoning, desc in test_cases:
        model = router.select_model(modality=modality, reasoning_level=reasoning)
        print(f"\n{desc}:")
        print(f"  Selected: {model.model_id}")
        print(f"  Cost: ${model.cost_input}/M input, ${model.cost_output}/M output")
        print(f"  Context: {model.context_window:,} tokens")
        print(f"  Tier: {model.tier.name}")
