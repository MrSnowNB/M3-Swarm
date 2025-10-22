
# 3. Create requirements.txt
requirements_txt = """# Swarm-100 MacOS Requirements
# Python 3.10+ required

# Core dependencies
ollama>=0.4.0
asyncio>=3.4.3
psutil>=5.9.0
pyyaml>=6.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-timeout>=2.1.0

# Monitoring and diagnostics
aiohttp>=3.8.0
python-dateutil>=2.8.2

# Data handling
pandas>=2.0.0
numpy>=1.24.0

# Logging
colorlog>=6.7.0
"""

with open("swarm_macos/requirements.txt", "w") as f:
    f.write(requirements_txt)

print("✅ Created: requirements.txt")
