
# 4. Create configuration files

# swarm_config.yaml
swarm_config = """# Swarm-100 MacOS Configuration
# Optimized for M3 Max 36GB

swarm:
  name: "Swarm-100-MacOS"
  max_concurrent_bots: 12  # Start conservative, scale based on testing
  batch_size: 6
  total_bot_target: 100
  
  scaling:
    mode: "progressive"  # progressive | fixed | adaptive
    start_bots: 2
    increment: 2
    max_bots: 24
    
  resource_limits:
    max_memory_percent: 80  # Don't use more than 80% of available RAM
    max_cpu_percent: 90
    memory_per_bot_gb: 1.5  # Estimated for gemma3:270m
    
  task_distribution:
    strategy: "round_robin"  # round_robin | least_loaded | random
    queue_size: 256
    task_timeout_seconds: 30
    
  error_handling:
    max_retries: 3
    retry_delay_seconds: 2
    failure_threshold: 0.2  # Stop if >20% failure rate
    
ollama:
  host: "http://localhost:11434"
  num_parallel: 6  # Concurrent requests Ollama can handle
  max_loaded_models: 1
  keep_alive: "5m"
  timeout_seconds: 60
  
model:
  name: "gemma3:270m"
  context_length: 2048  # Reduce from 32K to save memory
  temperature: 0.7
  top_k: 40
  top_p: 0.9
  
monitoring:
  enabled: true
  interval_seconds: 5
  metrics:
    - "cpu_percent"
    - "memory_used_gb"
    - "bot_count"
    - "success_rate"
    - "avg_response_time"
    - "queue_size"
    
logging:
  level: "INFO"  # DEBUG | INFO | WARNING | ERROR
  directory: "./logs"
  rotation: "daily"
  max_size_mb: 100
"""

with open("swarm_macos/config/swarm_config.yaml", "w") as f:
    f.write(swarm_config)

print("✅ Created: config/swarm_config.yaml")

# models.yaml
models_config = """# Model configurations for different test scenarios

models:
  gemma3_270m:
    name: "gemma3:270m"
    parameters: 270000000
    memory_footprint_gb: 0.5
    recommended_context: 2048
    max_context: 32768
    use_case: "High concurrency testing"
    
  gemma3_3b:
    name: "gemma3:3b"
    parameters: 3000000000
    memory_footprint_gb: 2.5
    recommended_context: 4096
    max_context: 32768
    use_case: "Medium concurrency, better quality"
    
  llama32_3b:
    name: "llama3.2:3b"
    parameters: 3000000000
    memory_footprint_gb: 2.5
    recommended_context: 4096
    max_context: 131072
    use_case: "Alternative 3B model"

test_prompts:
  simple:
    - "What is 2+2?"
    - "Classify: This is great!"
    - "Summarize: AI is transforming software."
    
  medium:
    - "Explain the concept of async programming in 2 sentences."
    - "Extract key entities from: Apple announced new products in California yesterday."
    - "Classify sentiment: The movie was disappointing but had good visuals."
    
  complex:
    - "Compare and contrast synchronous vs asynchronous programming paradigms."
    - "Analyze this text for sentiment, entities, and key themes: {{text}}"
    - "Generate a creative story about AI in 3 sentences."
"""

with open("swarm_macos/config/models.yaml", "w") as f:
    f.write(models_config)

print("✅ Created: config/models.yaml")
