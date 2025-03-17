import asyncio
import json
import httpx
import time
import argparse

async def test_model(model_name: str):
    """Test a specific model with both streaming and non-streaming"""
    model_id = AVAILABLE_MODELS.get(model_name)
    if not model_id:
        print(f"Error: Unknown model {model_name}")
        return

    print(f"\nTesting {model_id}:")
    print("-" * 50)

    base_url = "http://localhost:8000"
    async with httpx.AsyncClient() as client:
        # Test non-streaming
        print("\n1. Non-streaming test:")
        try:
            response = await client.post(
                f"{base_url}/api/v1/chat",
                json={
                    "messages": [{"role": "user", "content": "Say hi and introduce yourself in 1-2 sentences."}],
                    "model": model_id
                }
            )
            if response.status_code == 200:
                data = response.json()
                print("✓ Success!")
                print("Response:", data["choices"][0]["message"]["content"])
            else:
                print("✗ Error:", response.status_code)
                print("Response:", response.text)
        except Exception as e:
            print("✗ Exception:", str(e))

        # Test streaming
        print("\n2. Streaming test:")
        try:
            response = await client.post(
                f"{base_url}/api/v1/chat/stream",
                json={
                    "messages": [{"role": "user", "content": "Count from 1 to 3 with a brief pause between each number."}],
                    "model": model_id,
                    "stream": True
                },
                timeout=30.0
            )
            if response.status_code == 200:
                print("✓ Stream started successfully")
                print("\nResponse:")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and data["choices"]:
                                if "delta" in data["choices"][0]:
                                    content = data["choices"][0]["delta"].get("content", "")
                                    if content:
                                        print(content, end="", flush=True)
                                        await asyncio.sleep(0.1)  # Small delay to simulate real-time streaming
                        except json.JSONDecodeError:
                            if data == "[DONE]":
                                break
                            continue
                print("\n✓ Stream completed")
            else:
                print("✗ Error:", response.status_code)
                print("Response:", response.text)
        except Exception as e:
            print("✗ Exception:", str(e))

    print("\nTest complete!")
    print("=" * 50)

AVAILABLE_MODELS = {
    "claude": "anthropic.claude-3-5-sonnet-20241022-v2:0",  # Latest Claude
    "llama": "meta.llama3-3-70b-instruct-v1:0",           # Llama
    "titan": "amazon.titan-text-premier-v1:0",            # Titan
    "mistral": "mistral.mistral-7b-instruct-v0:2"         # Mistral
}

async def main():
    parser = argparse.ArgumentParser(description='Test chat models')
    parser.add_argument('--model', choices=list(AVAILABLE_MODELS.keys()), help='Model to test (e.g., claude, llama, titan, mistral)')
    args = parser.parse_args()

    # If no model specified, test all
    models_to_test = [args.model] if args.model else AVAILABLE_MODELS.keys()
    
    for model in models_to_test:
        await test_model(model)
        time.sleep(2)  # Small delay between tests

if __name__ == "__main__":
    asyncio.run(main())
