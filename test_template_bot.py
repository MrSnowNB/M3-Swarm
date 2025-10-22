#!/usr/bin/env python3
"""
Simple test for bot_agent_template.py
"""

import asyncio
import sys
import os

# Add current directory to import templates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_bot():
    from bot_agent_template import BotAgent

    config = {
        'ollama_host': 'http://localhost:11434',
        'timeout': 30,
        'context_length': 2048,
        'temperature': 0.7,
        'top_k': 40,
        'top_p': 0.9,
        'max_retries': 3,
        'retry_delay_seconds': 2
    }

    print("🚀 Creating bot agent...")
    bot = BotAgent(bot_id=1, model="gemma3:270m", config=config)

    print("✅ Bot initialized successfully")

    print("🔬 Testing health check...")
    healthy = await bot.health_check()
    print(f"Health check result: {healthy}")

    if healthy:
        print("💬 Testing prompt execution...")
        response = await bot.execute("What is 2+2?", timeout=10)
        print(f"Response success: {response.success}")

        if response.success:
            print(f"Response: {response.response[:100]}...")
            print(f"Response time: {response.response_time:.2f}s")

            metrics = bot.get_metrics()
            print(f"Metrics: {metrics}")
        else:
            print(f"Response error: {response.error}")
    else:
        print("⚠️  Bot not healthy, skipping execution test")

    print("✅ Template test completed")

if __name__ == "__main__":
    asyncio.run(test_bot())
