import httpx
import time
import asyncio

OLLAMA_HOST = "http://localhost:11434"
MODELS = ["nemotron-3-super:cloud", "minimax-m3:cloud", "gemma4:31b-cloud"]
TEST_MESSAGE = [{"role": "user", "content": "Скажи 'Привет' и больше ничего не отвечай."}]

async def test_model(model_name):
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={"model": model_name, "messages": TEST_MESSAGE, "stream": False}
            )
            elapsed = time.time() - start
            print(f"{model_name}: {elapsed:.2f} сек")
            return elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"{model_name}: ОШИБКА ({elapsed:.2f} сек) - {e}")
        return 999

async def main():
    print("=== Замеряем скорость моделей ===\n")
    results = {}
    for model in MODELS:
        results[model] = await test_model(model)
    
    sorted_models = sorted(results.items(), key=lambda x: x[1])
    print("\n=== Результаты (от быстрой к медленной) ===")
    for model, speed in sorted_models:
        print(f"  {speed:.2f} сек — {model}")

if __name__ == "__main__":
    asyncio.run(main())