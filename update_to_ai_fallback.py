#!/usr/bin/env python3
"""
Script to update backend to use the new AI service with fallback
This will update the existing files to use the new service
"""

import os
import sys

def update_imports():
    """Update import statements in relevant files"""
    files_to_update = [
        'src/main.py',
        'src/classification_service.py',
        'src/analytics_service.py',
        'src/letter_service.py'
    ]

    print("📝 Updating import statements...")

    for file_path in files_to_update:
        if os.path.exists(file_path):
            print(f"  Updating {file_path}...")
            with open(file_path, 'r') as f:
                content = f.read()

            # Replace old imports with new
            old_import = "from openrouter_service import OpenRouterService"
            new_import = "from ai_service_with_fallback import get_ai_service, AIServiceWithFallback"

            if old_import in content:
                content = content.replace(old_import, new_import)
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"    ✅ Updated imports in {file_path}")
            else:
                print(f"    ⚠️  Old import not found in {file_path}")

def create_env_template():
    """Create .env template with new variables"""
    env_template = """# AI Model Configuration

# Primary Model: Qwen 3 VL 32B (from your boss)
QWEN_BASE_URL=http://bgpu123.nttdc3.mtailabs.ai:9006/v1

# Fallback Model: OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=qwen/qwen-2.5-vl-72b-instruct

# Timeout for AI requests (seconds)
AI_TIMEOUT=120

# Other existing configurations
VLLM_ENABLED=true
DATABASE_HOST=localhost
DATABASE_NAME=sprm_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
"""

    with open('.env.example.new', 'w') as f:
        f.write(env_template)
    print("✅ Created .env.example.new with new configuration")

def show_integration_guide():
    """Show how to integrate the new service"""
    guide = """
============================================================
🚀 AI Service with Fallback - Integration Guide
============================================================

1. ENVIRONMENT VARIABLES
   Add these to your .env file:
   - QWEN_BASE_URL=http://bgpu123.nttdc3.mtailabs.ai:9006/v1
   - Keep your existing OPENROUTER_API_KEY

2. CODE CHANGES
   Replace OpenRouterService with AIServiceWithFallback:

   OLD CODE:
   ```python
   from openrouter_service import OpenRouterService
   vllm_service = OpenRouterService()
   result = vllm_service.call_openrouter(prompt)
   ```

   NEW CODE:
   ```python
   from ai_service_with_fallback import get_ai_service
   ai_service = get_ai_service()
   result = ai_service.call_ai(prompt)
   ```

3. MAIN.PY INTEGRATION
   In src/main.py, update the VLLM service initialization:

   ```python
   # AI Service (with fallback)
   from ai_service_with_fallback import get_ai_service
   vllm_service = get_ai_service()
   ```

4. STATUS ENDPOINT
   Add a new endpoint to check AI service status:

   ```python
   @app.get("/admin/ai-status", tags=["Admin"])
   async def get_ai_status():
       '''Check AI service status'''
       ai_service = get_ai_service()
       return ai_service.get_status()
   ```

5. TESTING
   Test the service with:
   ```bash
   python test_qwen_model.py
   ```

6. MONITORING
   The service will:
   - Use Qwen 3 VL 32B as primary (faster, cheaper)
   - Automatically fallback to OpenRouter if Qwen fails
   - Re-check Qwen availability every 5 minutes
   - Log which model is being used

============================================================
"""
    print(guide)

def main():
    print("=" * 60)
    print("🔧 Backend AI Service Update Tool")
    print("=" * 60)

    if not os.path.exists('src/main.py'):
        print("❌ Error: Run this from the SPRM_Backend directory")
        sys.exit(1)

    # Create new AI service if it doesn't exist
    if not os.path.exists('src/ai_service_with_fallback.py'):
        print("❌ ai_service_with_fallback.py not found!")
        print("   Please ensure the file was created")
        sys.exit(1)

    print("\nWhat would you like to do?")
    print("1. Show integration guide")
    print("2. Create .env template")
    print("3. Update imports automatically (backup first!)")
    print("4. All of the above")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        show_integration_guide()
    elif choice == "2":
        create_env_template()
    elif choice == "3":
        confirm = input("⚠️  This will modify files. Have you made a backup? (y/n): ")
        if confirm.lower() == 'y':
            update_imports()
        else:
            print("❌ Cancelled. Please backup first.")
    elif choice == "4":
        show_integration_guide()
        create_env_template()
        confirm = input("\n⚠️  Update imports? Have you made a backup? (y/n): ")
        if confirm.lower() == 'y':
            update_imports()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()