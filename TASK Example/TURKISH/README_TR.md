# OpenRouter Maliyet-Etkili Model Yönlendirici

Gereksinimlerinize göre otomatik olarak en maliyet-etkili AI modellerini seçen, katmanlı fiyatlandırma, çoklu yetenek desteği ve akıllı yedeklemeler sunan kapsamlı bir OpenRouter Python yönlendiricisi.

## Veri Kaynakları

| Kaynak | URL | Amaç |
|--------|-----|------|
| LLM Token Maliyeti | https://llmtokencost.com | Model fiyatlandırması (312 model, 55 sağlayıcı) |
| Arena Sıralaması | https://arena.ai/leaderboard | Performans sıralamaları |
| OpenRouter Ücretsiz Modeller | https://openrouter.ai/collections/free-models | Ücretsiz katman modelleri |
| OpenRouter Dokümantasyon | https://openrouter.ai/docs/guides/routing/model-fallbacks | Yedekleme stratejileri |

## Özellikler

### 6 Maliyet Katmanı

| Katman | Girdi $/1M | En İyi Kullanım Alanı |
|--------|-----------|----------------------|
| **ÜCRETSİZ** | $0 | Geliştirme, test, prototip |
| **ULTRA_DÜŞÜK** | < $0.20 | Yüksek hacimli metin işleme |
| **DÜŞÜK** | $0.20-$0.60 | Dengeli uygulamalar |
| **ORTA** | $0.60-$3.00 | Kod, mantıksal görevler |
| **YÜKSEK** | $3.00-$10.00 | Karmaşık çoklu yetenekli görevler |
| **PREMIUM** | > $10.00 | Kritik mantık, en yüksek kalite |

### Desteklenen Yetenekler

- **METİN**: Genel metin üretimi
- **GÖRÜNTÜ**: Görüntü analizi ve anlama
- **KOD**: Kod üretimi ve analizi (arena sıralamaları entegre)
- **MANTIK**: Karmaşık mantıksal/matematiksel görevler
- **SES**: Ses işleme (sınırlı destek)
- **ÇOKLU_YETENEK**: Görüntü ve metin birleşimi

## Hızlı Başlangıç

```python
from Router import CostOptimizedRouter, Tier, Modality

# Yönlendiriciyi başlat
router = CostOptimizedRouter(
    api_key="sizin-openrouter-api-anahtariniz",
    default_tier=Tier.DÜŞÜK
)

# Basit istek
response = router.chat_completion(
    messages=[{"role": "user", "content": "Merhaba!"}],
    modality=Modality.METİN
)

print(response['choices'][0]['message']['content'])
print(f"Maliyet: ${response['_router_metadata']['estimated_cost']['total_cost_usd']:.6f}")
```

## Önerilen Yapılandırmalar

### Prototipleme İçin (ÜCRETSİZ)
```python
from Router import SpecializedRouters

router = SpecializedRouters.free_router()
# Kullanır: openrouter/free -> gpt-oss-120b:free -> qwen3:free
```

**En İyi Ücretsiz Modeller:**
- `openrouter/free` - En iyi ücretsiz modeli otomatik seçer
- `openai/gpt-oss-120b:free` - 117B MoE, harika mantık (4.9B token işlendi)
- `qwen/qwen3-235b-a22b-thinking-2507:free` - 235B MoE, 260K bağlam
- `nvidia/llama-3.1-nemotron-30b-a3b:free` - Ajan odaklı
- `qwen/qwen3-vl-235b-a22b-thinking:free` - Ücretsiz çoklu yetenek + görüntü

### Yüksek Hacimli Metin İçin (Ultra Düşük Maliyet)
```python
router = SpecialistRouters.ultra_budget_router()
# $0.20/M girdiden düşük modelleri kullanır
```

**En İyi Ultra Düşük Maliyetli Modeller:**
- `qwen/qwen-turbo`: $0.05/$0.20 - 131K bağlam
- `qwen/qwen-2.5-7b-instruct`: $0.04/$0.10 - Kod yetenekli
- `google/gemini-2.0-flash-lite-001`: $0.075/$0.30 - 1M bağlam
- `google/gemma-3-4b-it`: $0.04/$0.08 - Açık ağırlıklar

### Dengeli Uygulamalar İçin
```python
from Router import quick_route

response = quick_route(
    messages=[{"role": "user", "content": "Açıkla..."}],
    use_case="balanced_chat"
)
```

**Önerilen:**
- `openai/gpt-4o-mini`: $0.15/$0.60 - Güvenilir, görüntü yetenekli
- `google/gemini-2.0-flash-001`: $0.10/$0.40 - 1M bağlam
- `anthropic/claude-3-haiku`: $0.25/$1.25 - 200K bağlam

### Kodlama İçin (Arena Sıralamaları Entegre)
```python
from Router import Modality, ReasoningLevel

response = router.chat_completion(
    messages=[{"role": "user", "content": "Python fonksiyonu yaz..."}],
    modality=Modality.KOD,
    reasoning_level=ReasoningLevel.ORTA
)
```

**Arena Kod Sıralamaları:**
1. `anthropic/claude-opus-4-6` ($5/$25) - #1 Kod
2. `anthropic/claude-opus-4-6-thinking` ($5/$25) - #1 Metin
3. `anthropic/claude-sonnet-4-6` ($3/$15) - #3 Kod
4. `google/gemini-3.1-pro-preview` ($2/$12) - #7 Kod
5. `google/gemini-3-flash` - #8 Kod

**Maliyet-Etkili Kod Seçenekleri:**
- `anthropic/claude-sonnet-4-20250514`: $3/$15 - Güçlü kodlama
- `google/gemini-2.5-flash`: $0.30/$2.50 - Arena #63, mükemmel denge
- `qwen/qwen-2.5-coder-7b-instruct`: $0.03/$0.09 - Ultra ucuz

### Görüntü Görevleri İçin (Arena Sıralamaları)
```python
from Router import Modality

router = CostOptimizedRouter(default_tier=Tier.YÜKSEK)

response = router.chat_completion(
    messages=[{
        "role": "user",
        "content": [{"type": "text", "text": "Tanımla:"},
                    {"type": "image_url", "image_url": {"url": "..."}}]
    }],
    modality=Modality.GÖRÜNTÜ
)
```

**Arena Görüntü Sıralamaları:**
1. `google/gemini-3-pro` - #1 Görüntü
2. `google/gemini-3.1-pro-preview` - #2 Görüntü
3. `google/gemini-3-flash` - #3 Görüntü
4. `openai/gpt-5.2-chat` - #4 Görüntü
5. `google/gemini-2.5-pro` - #9 Görüntü

**Maliyet-Etkili Görüntü:**
- `google/gemini-2.5-flash`: $0.30/$2.50 - Görüntü için mükemmel değer
- `openai/gpt-4o-mini`: $0.15/$0.60 - Görüntü yetenekli en ucuz
- `anthropic/claude-3-haiku`: $0.25/$1.25 - 200K bağlam

### Kritik Mantık İçin
```python
from Router import SpecializedRouters

router = SpecializedRouters.performance_router()
```

**Premium Seçenekler:**
- `anthropic/claude-opus-4-6-thinking`: $5/$25 - Arena #1 Metin & Kod
- `openai/o1`: $15/$60 - Mantık uzmanı
- `openai/o1-pro`: $150/$600 - Maksimum mantık derinliği

## Model Kayıt Referansı

llmtokencost.com'dan (312 model, 55 sağlayıcı) ve arena.ai'dan tam model verisi:

### Maliyet Katmanları Özeti

| Katman | Modeller | Maliyet Aralığı | En İyi Kullanım Alanı |
|--------|----------|----------------|----------------------|
| ÜCRETSİZ | 10+ | $0 | Test, geliştirme |
| ULTRA_DÜŞÜK | 6 | $0.03-$0.08 | Toplu işleme |
| DÜŞÜK | 8 | $0.15-$0.60 | Günlük kullanım |
| ORTA | 6 | $0.80-$3.00 | Kodlama, mantık |
| YÜKSEK | 6 | $1.25-$5.00 | Kalite-kritik |
| PREMIUM | 6 | $5.00-$150.00 | Uzman görevleri |

## Gelişmiş Kullanım

### Özel Yedekleme Zincirleri
```python
router = CostOptimizedRouter()

fallbacks = router.build_fallback_chain(
    primary_model="anthropic/claude-opus-4.6",
    chain_length=5
)
print(fallbacks)
# Çıktı: ['anthropic/claude-opus-4.6', 
#          'anthropic/claude-opus-4-6-thinking',
#          'google/gemini-3-pro',
#          'anthropic/claude-sonnet-4.5',
#          ...]
```

### Maliyet Takibi
```python
# İstekleri yap
for _ in range(10):
    router.chat_completion(...)

# Rapor al
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

### Sağlayıcı Tercihleri
```python
router = CostOptimizedRouter(
    provider_preferences={
        "order": ["DeepSeek", "Together", "Fireworks"],
        "allow_fallbacks": True
    }
)
```

## Maliyet-Etkililik Değerlendirmesindeki Faktörler

1. **Arena Sıralamaları**: Performans/maliyet oranı
2. **Bağlam Uzunluğu**: Daha uzun = daha fazla değer
3. **Sağlayıcı Güvenilirliği**: Çalışma süresi ve gecikme
4. **Yetenek Desteği**: Çoklu yetenek = daha fazla uygulama
5. **Mantık Kalitesi**: STEM ve kodlama kıyaslamaları
6. **Token Verimliliği**: Model mimarisi verimliliği

## Büyük Maliyet-Performans Şampiyonları

### Qwen Ailesi (Alibaba)
- `qwen/qwen-turbo`: $0.05/$0.20 - En iyi ultra düşük maliyetli metin
- `qwen/qwen3-235b-a22b-thinking`: Ücretsiz katman mevcut
- `qwen/qwen3-vl-235b-a22b`: Ücretsiz çoklu yetenek
- Tümü MoE mimarisi, güçlü Çince/İngilizce

### Gemini Ailesi (Google)
- `google/gemini-2.0-flash-lite`: $0.075/$0.30 - En ucuz 1M bağlam
- `google/gemini-2.5-flash`: $0.30/$2.50 - Arena #63, en iyi değer
- `google/gemini-3-pro`: $2/$12 - Görüntü #1, Metin #5
- Çoğu modelde 1M bağlam standart

### Claude Ailesi (Anthropic)
- `anthropic/claude-3-haiku`: $0.25/$1.25 - 200K bağlam
- `anthropic/claude-sonnet-4.6`: $3/$15 - Kod #3
- `anthropic/claude-opus-4.6`: $5/$25 - En iyi genel kalite
- Üstün talimat takibi ve kodlama

### GPT Ailesi (OpenAI)
- `openai/gpt-4o-mini`: $0.15/$0.60 - Güvenilir temel
- `openai/gpt-4.1-mini`: $0.40/$1.60 - 1M bağlam
- `openai/gpt-5`: $1.25/$10 - En son özellikler
- `openai/gpt-oss-120b`: Ücretsiz - Açık ağırlıklar

## Ücretsiz Model Katmanı Detayları

OpenRouter 10+ ücretsiz model sunar (hız limitleri ile):

| Model | Bağlam | İşlenen Token | Güçlü Yönler |
|-------|--------|---------------|--------------|
| gpt-oss-120b | 131K | 4.9B | 117B MoE, mantık |
| qwen3-235b-thinking | 262K | 18.1B | Matematik, mantık, STEM |
| trinity-large-preview | 128K | 555B | 400B MoE, yaratıcılık |
| step-3.5-flash | 256K | 466B | Hız, mantık |
| qwen3-vl-235b | 131K | 19.3B | Çoklu yetenek, görüntü |
| nemotron-nano-12b-vl | 128K | 3.82B | Video, belgeler |

## Kurulum ve Yapılandırma

```bash
# Bağımlılıkları kur
pip install requests

# API anahtarını ayarla
export OPENROUTER_API_KEY="sizin-anahtariniz"

# Veya Python'da
import os
os.environ["OPENROUTER_API_KEY"] = "sizin-anahtariniz"
```

## Dosyalar

- `Router.py` - Ana yönlendirici uygulaması (800+ satır)
- `example_usage.py` - Kullanım örnekleri
- `README.md` - Bu dokümantasyon
- `README_TR.md` - Türkçe dokümantasyon

## API Spesifikasyonu

OpenRouter OpenAI API formatını ek özelliklerle takip eder:

```python
POST https://openrouter.ai/api/v1/chat/completions

Başlıklar:
  Authorization: Bearer {OPENROUTER_API_KEY}
  HTTP-Referer: {SITENIZIN_URL}
  X-OpenRouter-Title: {UYGULAMANIZIN_ADI}

Gövde:
{
  "model": "anthropic/claude-sonnet-4.5",
  "messages": [...],
  "models": ["yedek1", "yedek2"],  # Otomatik yük devretme
  "provider": {"order": ["Anthropic"]},   # Sağlayıcı tercihi
}
```

## Lisans

MIT - Herhangi bir amaçla ücretsiz kullanım.

## Veri Atıfı

- Fiyatlandırma verisi llmtokencost.com'dan (55+ sağlayıcıdan canlı güncellenir)
- Performans sıralamaları arena.ai'dan (gerçek kullanımdan günlük güncellenir)
- Model meta verisi OpenRouter API'den (2025 verisi)