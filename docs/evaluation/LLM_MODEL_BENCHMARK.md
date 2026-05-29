# Local LLM/RAG Model Benchmark

This note records the local model comparison used to justify the prototype's
RAG-grounded report generation model choice. The benchmark is not a general LLM
leaderboard. It evaluates whether each locally deployed model can produce the
prototype's evidence-constrained employability report within practical runtime
limits.

## Test Environment

- CPU: AMD Ryzen 7 2700X, 8 cores, approximately 3.7GHz
- Motherboard: X470 AORUS Ultra Gaming
- Memory: 16GB DDR4 3200MHz, 2x8GB
- GPU: NVIDIA GeForce GTX 1050 Ti 4GB Windforce OC
- Runtime: Ollama local inference
- Prompt strategy: Same RAG prompt, same retrieved evidence, temperature 0.2
- RAG evidence budget: 18 retrieved chunks, 10,443 prompt characters
- Generic output budget for cross-model test: `num_predict=900`

The hardware specification is included because local LLM latency is strongly
dependent on CPU, GPU, memory and quantisation. The results should therefore be
read as prototype-environment measurements rather than universal model speeds.

## Candidate Model Rationale

- `phi3:mini` was tested as a lightweight local SLM baseline. The Phi-3
  technical report frames Phi-3 Mini as a compact model designed for capable
  local deployment.
- `qwen2.5:7b` was tested because Qwen2.5 provides instruction-tuned open-weight
  models in multiple sizes and the technical report highlights improvements in
  instruction following, long text generation and structured data analysis.
- `llama3.1:8b` was tested as the current quality baseline. Meta's Llama 3.1
  release positions the 8B model as part of an open model family with broad
  deployment support.
- `gemma2:9b` was tested as a slightly larger local alternative in the same
  approximate class as Llama/Qwen, based on the Gemma 2 open model family.
- `mistral` was tested as an additional widely used 7B-class instruction
  baseline. The local Ollama package reports 7.2B parameters, Q4_K_M
  quantisation and Apache 2.0 licensing.

Relevant sources:

- Microsoft, Phi-3 Technical Report: <https://arxiv.org/abs/2404.14219>
- Qwen Team, Qwen2.5 Technical Report: <https://arxiv.org/abs/2412.15115>
- Meta, Llama 3.1 release/model information: <https://ai.meta.com/blog/meta-llama-3-1/>
- Google DeepMind, Gemma 2 technical report: <https://openreview.net/forum?id=6c8e3fd1fc8f63c89f22071ab13df828cfe8ecf9>
- Mistral AI, Mistral 7B model card: <https://docs.mistral.ai/models/model-cards/mistral-7b-0-1>
- SLM/RAG retrieval-utilisation concern: <https://arxiv.org/abs/2603.11513>
- RAG prompt engineering for SLMs: <https://arxiv.org/abs/2602.13890>

## Benchmark Results

| Model | Parameters | Size | Quantisation | Total script time | LLM request time | Output tokens | Tokens/sec | Quality gate |
|---|---:|---:|---|---:|---:|---:|---:|---|
| `phi3:mini` | 3.8B | 2.18GB | Q4_0 | 126.135s | 118.932s | 743 | 6.38 | Passed |
| `mistral` | 7.2B | 4.40GB | Q4_K_M | 136.503s | 131.974s | 397 | 3.61 | Passed |
| `qwen2.5:7b` | 7.6B | 4.68GB | Q4_K_M | 178.972s | 173.993s | 565 | 3.76 | Passed |
| `llama3.1:8b` | 8.0B | 4.92GB | Q4_K_M | 217.030s | 211.163s | 591 | 3.18 | Passed |
| `gemma2:9b` | 9.2B | 5.44GB | Q4_0 | 306.676s | 302.029s | n/a | n/a | Failed: timeout |

All successful runs used the same RAG evidence and prompt size. The deterministic
quality gate checks whether required report sections are present, forbidden
overclaiming phrases are absent and no LLM generation warning was returned. It
does not prove factual correctness; human review remains required.

## Qualitative Observations

- `phi3:mini` was the fastest successful model, but its output showed weaker
  evidence handling. It used placeholders such as `[Student ID]`, awkward score
  rendering such as `priority: 0s`, and broader employability phrasing. It is
  suitable as a lightweight comparison model, but less suitable as the primary
  dissertation output model.
- `mistral` was the fastest 7B-class successful model and produced a concise,
  clean report. However, the output was relatively brief and less analytically
  detailed than the stronger Qwen/Llama outputs. It is a useful efficient
  baseline, but not the strongest candidate when report depth is prioritised.
- `qwen2.5:7b` produced a complete, readable and reasonably cautious report. It
  was faster than `llama3.1:8b` in this environment while still passing the same
  quality gate. It is the strongest current candidate for the default model if
  qualitative review confirms adequate grounding.
- `llama3.1:8b` produced stable and evidence-aware output, but with longer
  runtime. It remains a strong quality baseline and a defensible default when
  output conservatism is prioritised over speed.
- `gemma2:9b` timed out under the configured 300-second request limit. On the
  current hardware it is not a practical default for this prototype without
  further optimisation.

## Final Model Selection Direction

The benchmark supports a measured trade-off rather than a single universal best
model:

- Best lightweight/runtime profile: `phi3:mini`
- Best concise 7B runtime profile: `mistral`
- Best current quality/runtime balance: `qwen2.5:7b`
- Strongest existing conservative baseline: `llama3.1:8b`
- Not practical on this hardware under current settings: `gemma2:9b`

The prototype therefore uses `qwen2.5:7b` as the default local LLM for
RAG-grounded report generation. `llama3.1:8b` is kept as the configured fallback
and quality baseline, `mistral` is reported as an efficient 7B-class baseline,
and `phi3:mini` is reported as a lightweight deployment option with known
output-quality limitations.
