### 🇹🇷 Minik-Ajan:

Minik-Ajan, LLM (Büyük Dil Modelleri) ajan kullanımını eğlenerek öğrenmek için yapılmış küçük ve şirin bir örnektir. Hesaplıdır, tutumludur. Bakkaldan sakız alır gibi cent’ler ve kuruşlarla çalışır. MCP vb. protokollerle uğraşmadan, LangChain veya LangGraph gibi araçları öğrenmenin ön yükü olmadan, işlerinizi ve denemelerinizi hızlıca izole edilmiş Docker konteynerlarında test etmeniz için tasarlanmıştır.

![new3.jpeg](Slip%20messages%20during%20task/new3.jpeg)

--- 

Dosya ve dizinleri izole etmek için basit bir kod ve Docker kullanılmıştır; ideal olan Firecracker’dır ancak kapsam dışıdır. Bash komutlarının çalıştırılması prompt ile engellenmiştir. Ancak her yaramaz ajan gibi `use_tools.py` dosyasını okuyarak araç tanımlarını ve limitlerini görüp yine de kullanmaya çalışabilir. Buna rağmen atak yüzeyi oldukça düşüktür ve tamamen engellemeniz için gerekli kod mantığı ve altyapı hazırdır. Herhangi bir LLM’e yapıştırarak ne yapmanız gerektiğini hızlıca anlayabilirsiniz.

Olduğu gibi kullanılabilir ancak atak yüzeyi yaklaşık %1.5–3.5 civarındadır. Yine de bir sanal makine içinde Docker’da çalıştırmanızı tavsiye ederim. Herhangi bir sorumluluk kesinlikle kabul etmiyorum.

DeepInfra API key’i ile çalışır; endpoint, key ve modeli değiştirerek ciddi hız artışı elde edebilirsiniz. Güle güle kullanın — oldukça eğlencelidir.

Lisansı MIT Lisansı’dır. Kullanın, değiştirin, ticari kullanın — sorun yok. Entegre edin, fork edin vs.

---

### Bundan sonra neler eklenebilir / denenebilir:

- Ajan çalışırken hafızasına canlı komut yerleştirme

- Kullanıcıyı canlı bilgilendiren şirin ve sempatik bir diyalog tarzı prompt’a eklenebilir

- Paralel ajanların hızlı bir veri yolu (D-Bus vb.) üzerinden haberleşmesi

- Tüm ajanları izleyen ve koordine eden üst seviye yöneticiler

- Streaming generation’ın meta kullanımları

- memU benzeri akıllı hafıza entegrasyonları

- Birden çok LLM döngüsünün tek ajan içinde ve ajanlar arasında eş zamanlı kullanımı

- Ucuz modellerin, pahalı modeller tarafından rekabetçi şekilde yönlendirilmesi

- Aynı ajanın farklı görevleri / farklı ajanların aynı görevi koordine etmesine yönelik yapılar

---

## 

### 🇬🇧 Minik-Ajan:

Minik-Ajan is a small and cute example project designed to learn agent usage in LLM (Large Language Model) systems in a fun way. It is economical and efficient. It runs on cents and pennies — like buying gum from a corner store.

It is built to let you quickly test your work and experiments inside isolated Docker containers without dealing with protocols such as MCP or the learning overhead of tools like LangChain or LangGraph.

A simple code-based file and directory isolation mechanism is implemented using Docker; Firecracker would be ideal but is out of scope. Bash command execution is restricted via prompting. However, like any mischievous agent, it may still read `use_tools.py`, see the tool definitions and limits, and attempt to use them. Even so, the attack surface is quite small, and the necessary logic and infrastructure are in place if you want to fully harden it. You can paste it into any LLM and quickly understand what needs to be done.

It can be used as-is, but the attack surface is approximately 1.5–3.5%. I still recommend running it inside Docker within a virtual machine. I explicitly accept no liability.

It works with a DeepInfra API key; you can significantly speed it up by changing the endpoint, key, and model. Have fun — it’s quite enjoyable.

Licensed under MIT. Use it, modify it, use it commercially — no problem. Integrate it, fork it, etc.

---

New wrapper-od is in on the way and not yet tested but : 

<img title="" src="file:///home/gediz/.config/marktext/images/2026-02-28-16-23-42-image.png" alt="" width="856" data-align="left">

| Feature / Architecture Metric             | This ONE (Your Wrapper) | SWE-Agent | OpenCLAW | Scientific SOTA |
|:----------------------------------------- |:-----------------------:|:---------:|:--------:|:---------------:|
| **ReAct Loop** (Step reasoning cycle)     | ✅                       | ✅         | ✅        | ✅               |
| **Parallel Tools** (Concurrent execution) | ✅                       | ❗         | ✅        | ✅               |
| **Memory Compression** (Token mgmt)       | ✅                       | ✅         | ✅        | ✅               |
| **External Interrupts** (Live steering)   | ✅                       | ❗         | ✅        | ❗               |
| **Planner / Executor Split**              | ❗                       | ❗         | ✅        | ✅               |
| **Reflection / Self-Correction Loop**     | ❗                       | ✅         | ✅        | ✅               |
| **Strict JSON Schema Enforcement**        | ✅                       | ✅         | ✅        | ✅               |
| **Web Browsing & Fetch Automation**       | ✅                       | ❗         | ✅        | ✅               |
| **Hard-Capped Max Cycles**                | ✅                       | ✅         | ✅        | ✅               |
| **Lightweight & Dependency-Free Core**    | ✅                       | ❗         | ❗        | ❗               |
| **Native Docker / Sandboxing**            | ❗                       | ✅         | ✅        | ❗               |
| **Graph / Tree-of-Thought Branches**      | ❗                       | ❗         | ❗        | ✅               |
| **Semantic Vector Database Memory**       | ❗                       | ❗         | ✅        | ✅               |
| **Automated System Packaging (apt)**      | ✅                       | ✅         | ✅        | ❗               |
| **Specialized Custom Code Linters**       | ❗                       | ✅         | ✅        | ✅               |
| **Multi-Agent Orchestration Swarms**      | ❗                       | ❗         | ✅        | ✅               |


