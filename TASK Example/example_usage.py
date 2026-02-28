"""
OpenRouter Cost-Effective Router - Usage Examples
=================================================

This shows how to use the Router.py for different scenarios.
"""

from Router import (
    CostOptimizedRouter, SpecializedRouters, quick_route,
    Tier, Modality, ReasoningLevel, ModelRegistry
)
import os

# Set your OpenRouter API key
os.environ["OPENROUTER_API_KEY"] = "your-api-key"


def example_1_basic_usage():
    """Example 1: Basic usage with automatic model selection"""
    
    router = CostOptimizedRouter(default_tier=Tier.LOW)
    
    response = router.chat_completion(
        messages=[
            {"role": "user", "content": "Hello, how are you today?"}
        ],
        modality=Modality.TEXT
    )
    
    print(f"Response: {response['choices'][0]['message']['content']}")
    print(f"Model used: {response['_router_metadata']['model_used']}")
    print(f"Cost: ${response['_router_metadata']['estimated_cost']['total_cost_usd']:.6f}")
    

def example_2_coding_task():
    """Example 2: Coding task with reasoning"""
    
    router = CostOptimizedRouter(default_tier=Tier.MID)
    
    response = router.chat_completion(
        messages=[
            {"role": "user", "content": "Write a Python function to find all prime factors of a number."}
        ],
        modality=Modality.CODE,
        reasoning_level=ReasoningLevel.MEDIUM,
        temperature=0.2  # Lower temperature for code
    )
    
    print(f"Code: {response['choices'][0]['message']['content']}")
    print(f"Model used: {response['_router_metadata']['model_used']}")


def example_3_vision_analysis():
    """Example 3: Vision analysis"""
    
    router = CostOptimizedRouter(default_tier=Tier.HIGH)
    
    response = router.chat_completion(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                ]
            }
        ],
        modality=Modality.VISION
    )
    
    print(f"Analysis: {response['choices'][0]['message']['content']}")


def example_4_free_tier():
    """Example 4: Using completely free models"""
    
    router = SpecializedRouters.free_router()
    
    response = router.chat_completion(
        messages=[
            {"role": "user", "content": "Explain quantum computing in simple terms"}
        ]
    )
    
    print(f"Response: {response['choices'][0]['message']['content']}")
    print(f"Cost: Free!")


def example_5_custom_fallbacks():
    """Example 5: Custom fallback chain"""
    
    router = CostOptimizedRouter()
    
    # Build a custom fallback chain
    fallbacks = router.build_fallback_chain(
        primary_model="anthropic/claude-opus-4.6",
        chain_length=5
    )
    print(f"Fallback chain: {fallbacks}")


def example_6_cost_report():
    """Example 6: Get cost report"""
    
    router = CostOptimizedRouter(default_tier=Tier.LOW)
    
    # Make some requests
    for _ in range(3):
        router.chat_completion(
            messages=[{"role": "user", "content": "Say hello"}]
        )
    
    # Get cost report
    report = router.get_cost_report()
    print(f"\nCost Report: {report}")


def example_7_quick_route():
    """Example 7: Quick routing by use case"""
    
    # Use recommended defaults by use case
    response = quick_route(
        messages=[{"role": "user", "content": "Debug this code: def foo(): return bar"}],
        use_case="coding_assistant"
    )
    
    print(f"Response: {response['choices'][0]['message']['content']}")
    print(f"Metadata: {response['_router_metadata']}")


def example_8_registry_explorer():
    """Example 8: Explore the model registry"""
    
    registry = ModelRegistry()
    
    # Get all free models
    free_models = registry.get_models_by_tier(Tier.FREE)
    print(f"\nFree models: {len(free_models)}")
    for m in free_models[:3]:
        print(f"  - {m.model_id}: {m.strengths[:2]}")
    
    # Get cheapest vision model
    cheapest_vision = registry.get_cheapest_for_modality(Modality.VISION)
    print(f"\nCheapest vision model: {cheapest_vision.model_id}")
    print(f"Cost: ${cheapest_vision.cost_input}/M input, ${cheapest_vision.cost_output}/M output")
    
    # Get best code model
    best_code = registry.get_best_for_code(max_tier=Tier.MID)
    print(f"\nBest mid-tier code model: {best_code.model_id}")


if __name__ == "__main__":
    print("OpenRouter Cost-Effective Router - Examples")
    print("=" * 60)
    
    # Run example 8 (registry explorer) - doesn't need API key
    try:
        example_8_registry_explorer()
    except Exception as e:
        print(f"Note: API key not required for registry exploration")
        print(f"Registry example completed successfully")
    
    print("\n" + "=" * 60)
    print("To run API examples, set OPENROUTER_API_KEY")
