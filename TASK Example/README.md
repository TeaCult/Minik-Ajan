# OpenRouter Cost-Effective Model Router

A comprehensive Python router for OpenRouter that automatically selects the most cost-effective AI models based on your requirements, with tiered pricing, modality support, and intelligent fallbacks.

## Data Sources

| Source | URL | Purpose |
|--------|-----|---------|
| LLM Token Cost | https://llmtokencost.com | Model pricing (312 models, 55 providers) |
| Arena Leaderboard | https://arena.ai/leaderboard | Performance rankings |
| OpenRouter Free Models | https://openrouter.ai/collections/free-models | Free tier models |
| OpenRouter Docs | https://openrouter.ai/docs/guides/routing/model-fallbacks | Fallback strategies |

## Features

### 6 Cost Tiers

| Tier | Input $/1M | Best For |
|------|-----------|----------|
| **FREE** | $0 | Development, testing, prototypes |
| **ULTRA_LOW** | < $0.20 | High-volume text processing |
| **LOW** | $0.20-$0.60 | Balanced applications |
| **MID** | $0.60-$3.00 | Code, reasoning tasks |
| **HIGH** | $3.00-$10.00 | Complex multimodal tasks |
| **PREMIUM** | > $10.00 | Critical reasoning, highest quality |

### Modalities Supported

- **TEXT**: General text generation
- **VISION**: Image analysis and understanding
- **CODE**: Code generation and analysis (top Arena rankings integrated)
- **REASONING**: Complex logical/mathematical tasks
- **AUDIO**: Audio processing (limited support)
- **MULTIMODAL**: Combined vision and text

## Quick Start

```python
from Router import CostOptimizedRouter, Tier, Modality

# Initialize router
router = CostOptimizedRouter(
    api_key="your-openrouter-api-key",
    default_tier=Tier.LOW
)

# Simple request
response = router.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    modality=Modality.TEXT
)

print(response['choices'][0]['message']['content'])
print(f"Cost: ${response['_router_metadata']['estimated_cost']['total_cost_usd']:.6f}")
```

## Recommended Configurations

### For Prototyping (FREE)
```python
from Router import SpecializedRouters

router = SpecializedRouters.free_router()
# Uses: openrouter/free -> gpt-oss-120b:free -> qwen3:free
```

**Best Free Models:**
- `openrouter/free` - Auto-selects best available free model
- `openai/gpt-oss-120b:free` - 117B MoE, great reasoning (4.9B tokens processed)
- `qwen/qwen3-235b-a22b-thinking-2507:free` - 235B MoE, 260K context
- `nvidia/llama-3.1-nemotron-30b-a3b:free` - Agentic specialized
- `qwen/qwen3-vl-235b-a22b-thinking:free` - Free multimodal + vision

### For High-Volume Text (Ultra Low Cost)
```python
router = SpecialistRouters.ultra_budget_router()
# Uses models < $0.20/M input
```

**Top Ultra Low Cost Models:**
- `qwen/qwen-turbo`: $0.05/$0.20 - 131K context
- `qwen/qwen-2.5-7b-instruct`: $0.04/$0.10 - Code capable
- `google/gemini-2.0-flash-lite-001`: $0.075/$0.30 - 1M context
- `google/gemma-3-4b-it`: $0.04/$0.08 - Open weights

### For Balanced Applications
```python
from Router import quick_route

response = quick_route(
    messages=[{"role": "user", "content": "Explain..."}],
    use_case="balanced_chat"
)
```

**Recommended:**
- `openai/gpt-4o-mini`: $0.15/$0.60 - Reliable, vision capable
- `google/gemini-2.0-flash-001`: $0.10/$0.40 - 1M context
- `anthropic/claude-3-haiku`: $0.25/$1.25 - 200K context

### For Coding (Arena Rankings Integrated)
```python
from Router import Modality, ReasoningLevel

response = router.chat_completion(
    messages=[{"role": "user", "content": "Write a Python function..."}],
    modality=Modality.CODE,
    reasoning_level=ReasoningLevel.MEDIUM
)
```

**Arena Code Rankings:**
1. `anthropic/claude-opus-4-6` ($5/$25) - #1 Code
2. `anthropic/claude-opus-4-6-thinking` ($5/$25) - #1 Text
3. `anthropic/claude-sonnet-4-6` ($3/$15) - #3 Code
4. `google/gemini-3.1-pro-preview` ($2/$12) - #7 Code
5. `google/gemini-3-flash` - #8 Code

**Cost-Effective Code Options:**
- `anthropic/claude-sonnet-4-20250514`: $3/$15 - Strong coding
- `google/gemini-2.5-flash`: $0.30/$2.50 - Arena #63, excellent balance
- `qwen/qwen-2.5-coder-7b-instruct`: $0.03/$0.09 - Ultra cheap

### For Vision Tasks (Arena Rankings)
```python
from Router import Modality

router = CostOptimizedRouter(default_tier=Tier.HIGH)

response = router.chat_completion(
    messages=[{
        "role": "user",
        "content": [{"type": "text", "text": "Describe:"},
                    {"type": "image_url", "image_url": {"url": "..."}}]
    }],
    modality=Modality.VISION
)
```

**Arena Vision Rankings:**
1. `google/gemini-3-pro` - #1 Vision
2. `google/gemini-3.1-pro-preview` - #2 Vision
3. `google/gemini-3-flash` - #3 Vision
4. `openai/gpt-5.2-chat` - #4 Vision
5. `google/gemini-2.5-pro` - #9 Vision

**Cost-Effective Vision:**
- `google/gemini-2.5-flash`: $0.30/$2.50 - Excellent value for vision
- `openai/gpt-4o-mini`: $0.15/$0.60 - Cheapest with vision
- `anthropic/claude-3-haiku`: $0.25/$1.25 - 200K context

### For Critical Reasoning
```python
from Router import SpecializedRouters

router = SpecializedRouters.performance_router()
```

**Premium Options:**
- `anthropic/claude-opus-4-6-thinking`: $5/$25 - Arena #1 Text & Code
- `openai/o1`: $15/$60 - Reasoning specialist
- `openai/o1-pro`: $150/$600 - Maximum reasoning depth

## Model Registry Reference

Complete model data from llmtokencost.com (312 models, 55 providers) and arena.ai:

### Cost Tiers Summary

| Tier | Models | Cost Range | Best For |
|------|--------|-----------|----------|
| FREE | 10+ | $0 | Testing, development |
| ULTRA_LOW | 6 | $0.03-$0.08 | Batch processing |
| LOW | 8 | $0.15-$0.60 | Daily use |
| MID | 6 | $0.80-$3.00 | Coding, reasoning |
| HIGH | 6 | $1.25-$5.00 | Quality-critical |
| PREMIUM | 6 | $5.00-$150.00 | Expert tasks |

## Advanced Usage

### Custom Fallback Chains
```python
router = CostOptimizedRouter()

fallbacks = router.build_fallback_chain(
    primary_model="anthropic/claude-opus-4.6",
    chain_length=5
)
print(fallbacks)
# Output: ['anthropic/claude-opus-4.6', 
#          'anthropic/claude-opus-4-6-thinking',
#          'google/gemini-3-pro',
#          'anthropic/claude-sonnet-4.5',
#          ...]
```

### Cost Tracking
```python
# Make requests
for _ in range(10):
    router.chat_completion(...)

# Get report
report = router.get_cost_report()
print(report)
# {
#   'total_requests': 10,
#   'total_tokens': 12500,
#   'total_cost_usd': 0.015,
#   'avg_cost_per_request': 0.0015,
#   'avg_tokens_per_request': 1250.0
# }
```

### Provider Preferences
```python
router = CostOptimizedRouter(
    provider_preferences={
        "order": ["DeepSeek", "Together", "Fireworks"],
        "allow_fallbacks": True
    }
)
```

## Factors in Cost-Effectiveness Rating

1. **Arena Rankings**: Performance vs cost ratio
2. **Context Length**: Longer = more value
3. **Provider Reliability**: Uptime and latency
4. **Modality Support**: Multi-modal = more applications
5. **Reasoning Quality**: STEM and coding benchmarks
6. **Token Efficiency**: Model architecture efficiency

## Major Cost-Performance Champions

### Qwen Family (Alibaba)
- `qwen/qwen-turbo`: $0.05/$0.20 - Best ultra-low cost text
- `qwen/qwen3-235b-a22b-thinking`: Free tier available
- `qwen/qwen3-vl-235b-a22b`: Free multimodal
- All feature MoE architecture, strong Chinese/English

### Gemini Family (Google)
- `google/gemini-2.0-flash-lite`: $0.075/$0.30 - Cheapest 1M context
- `google/gemini-2.5-flash`: $0.30/$2.50 - Arena #63, best value
- `google/gemini-3-pro`: $2/$12 - Vision #1, Text #5
- 1M context standard on most models

### Claude Family (Anthropic)
- `anthropic/claude-3-haiku`: $0.25/$1.25 - 200K context
- `anthropic/claude-sonnet-4.6`: $3/$15 - Code #3
- `anthropic/claude-opus-4.6`: $5/$25 - Best overall quality
- Superior instruction following and coding

### GPT Family (OpenAI)
- `openai/gpt-4o-mini`: $0.15/$0.60 - Reliable baseline
- `openai/gpt-4.1-mini`: $0.40/$1.60 - 1M context
- `openai/gpt-5`: $1.25/$10 - Latest features
- `openai/gpt-oss-120b`: Free - Open weights

## Free Model Tier Details

OpenRouter provides 10+ free models with rate limits:

| Model | Context | Tokens Processed | Strengths |
|-------|---------|-----------------|-----------|
| gpt-oss-120b | 131K | 4.9B | 117B MoE, reasoning |
| qwen3-235b-thinking | 262K | 18.1B | Math, logic, STEM |
| trinity-large-preview | 128K | 555B | 400B MoE, creative |
| step-3.5-flash | 256K | 466B | Speed, reasoning |
| qwen3-vl-235b | 131K | 19.3B | Multimodal, vision |
| nemotron-nano-12b-vl | 128K | 3.82B | Video, documents |

## Installation & Setup

```bash
# Install dependencies
pip install requests

# Set API key
export OPENROUTER_API_KEY="your-key"

# Or in Python
import os
os.environ["OPENROUTER_API_KEY"] = "your-key"
```

## Files

- `Router.py` - Main router implementation (800+ lines)
- `example_usage.py` - Usage examples
- `README.md` - This documentation

## API Specification

OpenRouter follows OpenAI API format with additional features:

```python
POST https://openrouter.ai/api/v1/chat/completions

Headers:
  Authorization: Bearer {OPENROUTER_API_KEY}
  HTTP-Referer: {YOUR_SITE_URL}
  X-OpenRouter-Title: {YOUR_APP_NAME}

Body:
{
  "model": "anthropic/claude-sonnet-4.5",
  "messages": [...],
  "models": ["fallback1", "fallback2"],  # Auto failover
  "provider": {"order": ["Anthropic"]},   # Provider preference
}
```

## License

MIT - Free to use for any purpose.

## Data Attribution

- Pricing data sourced from llmtokencost.com (Updated live from 55+ providers)
- Performance rankings from arena.ai (Updated daily from real-world usage)
- Model metadata from OpenRouter API (2025 data)
