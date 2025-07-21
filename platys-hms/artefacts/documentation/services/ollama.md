# Ollama

Get up and running with Llama 2, Mistral, Gemma, and other large language models.  

**[Website](https://ollama.com/)** | **[Documentation](https://github.com/ollama/ollama)** | **[GitHub](https://github.com/ollama/ollama)**

## How to enable?

```
platys init --enable-services OLLAMA
platys gen
```

By default, the `ollama2` llm is automatically downloaded. You can change it by overwriting the `OLLAMA_llm` config setting.

## How to use it?

Generate a completion

```bash
<<<<<<< Updated upstream
curl http://192.168.1.112:11434/api/generate -d '{
=======
curl http://10.156.72.251:11434/api/generate -d '{
>>>>>>> Stashed changes
  "model": "llama2",
  "prompt":"Why is the sky blue?"
}'
```

Generate embeddings from a model

```
<<<<<<< Updated upstream
curl http://192.168.1.112:11434/api/embeddings -d '{
=======
curl http://10.156.72.251:11434/api/embeddings -d '{
>>>>>>> Stashed changes
  "model": "llama2",
  "prompt": "Here is an article about llamas..."
}'
```