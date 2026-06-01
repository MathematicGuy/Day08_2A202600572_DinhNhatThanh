#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
vault_agent.py — Minimal WikiLLM Agent Tool Calling Workflow.

Coordinates:
1. Run check_folder_structure.py to create the Git sandbox and print the ASCII layout.
2. Read loose markdown files sitting directly in the Scratch directory.
3. Run Subagent to summarize and tag notes into a compiled JSON list.
4. Run Master Agent to observe the JSON list and generate move_plan.md.
5. Execute migrations using organize_file_heuristic.py and move_image.py tools.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Ensure UTF-8 encoding is used for standard output/error, especially on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Paths Setup
SCRATCH_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = SCRATCH_DIR / "vault-organizer-agent"

# Environment Variables Loader
def load_env_variables():
    current = SCRATCH_DIR
    for _ in range(5):
        env_path = current / ".env"
        if env_path.is_file():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")
            print(f"[ENV] Loaded environment from {env_path}")
            return True
        parent = current.parent
        if parent == current:
            break
        current = parent
    return False


# Minimal LLM Calling Function
def call_llm(system_prompt: str, user_prompt: str, json_format: bool = False) -> str:
    """Invokes OpenAI or Gemini directly based on loaded environmental variables."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    provider = os.environ.get("DEFAULT_PROVIDER", "openai")
    model_name = os.environ.get("DEFAULT_MODEL", "gpt-4o")

    # Automatic fallback
    if not openai_key and gemini_key:
        provider = "google"
        model_name = "gemini-1.5-pro"
    elif not gemini_key and openai_key:
        provider = "openai"
        model_name = "gpt-4o"

    if provider == "google":
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"response_mime_type": "application/json"} if json_format else None,
            system_instruction=system_prompt
        )
        res = model.generate_content(user_prompt)
        return res.text
    else:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        res = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"} if json_format else None
        )
        return res.choices[0].message.content


def main():
    print("==================================================")
    print("WikiLLM Agent Tool Calling Workflow Initiated")
    print("==================================================\n")

    # Load environment keys
    load_env_variables()

    # Step 1: Git Sandboxing & Folder structure printing (Calling Tool)
    print("--- [STEP 1: Check Folder Structure & Sandbox] ---")
    subprocess.run([sys.executable, str(SCRATCH_DIR / "check_folder_structure.py"), str(SCRATCH_DIR)], check=True)

    # Step 2: Scan and Collect loose Markdown Notes
    print("--- [STEP 2: Scanning Notes] ---")
    notes = []
    for item in sorted(os.listdir(SCRATCH_DIR)):
        if item.lower().endswith(".md") and item.lower() != "readme.md" and "plan" not in item.lower():
            notes.append(item)
    print(f"Found {len(notes)} unorganized notes: {notes}\n")

    if not notes:
        print("[INFO] No loose markdown notes found to organize. Exiting.")
        return

    try:
        # Step 3: Run Subagent to Summarize and Tag each note (semantic mapping)
        print("--- [STEP 3: Subagent Note Summarization] ---")
        with open(PROMPTS_DIR / "SUB-SKILLS.md", "r", encoding="utf-8") as f:
            sub_system_prompt = f.read()

        summarized_notes = []
        for note in notes:
            note_path = SCRATCH_DIR / note
            with open(note_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(1800) # Preview

            print(f"Processing note: {note}...")
            res_text = call_llm(sub_system_prompt, f"File Name: {note}\nContent:\n{content}", json_format=True)
            
            # Clean JSON backticks if present
            res_text = res_text.strip()
            if res_text.startswith("```json"):
                res_text = res_text[7:]
            elif res_text.startswith("```"):
                res_text = res_text[3:]
            if res_text.endswith("```"):
                res_text = res_text[:-3]
                
            data = json.loads(res_text.strip())
            summarized_notes.append(data)
            print(f"  Summary: {data.get('summary')}")
            print(f"  Tags: {data.get('tags')}\n")

        # Step 4: Run Master Agent to formulate move plan
        print("--- [STEP 4: Master Agent Move Plan Compilation] ---")
        with open(PROMPTS_DIR / "SKILL.md", "r", encoding="utf-8") as f:
            master_system_prompt = f.read()

        user_payload = json.dumps(summarized_notes, indent=2, ensure_ascii=False)
        move_plan_md = call_llm(master_system_prompt, f"Analyzed Notes List:\n{user_payload}", json_format=False)
        
        plan_path = SCRATCH_DIR / "move_plan.md"
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(move_plan_md)
        print(f"[SUCCESS] Compiled PARA move plan saved at: {plan_path}\n")

    except Exception as e:
        print("\n==================================================")
        print("❌ [LLM API CONNECTION/AUTHENTICATION ERROR]")
        print("==================================================")
        print(f"Details: {e}")
        print("\nTroubleshooting Steps:")
        print("  1. Make sure you have a valid .env file in a parent directory.")
        print("  2. Verify your API keys (OPENAI_API_KEY / GEMINI_API_KEY) are active and correctly typed.")
        print("  3. Check your internet connection and API quotas.")
        print("==================================================\n")
        print("[INFO] Bypassing AI steps due to API connection error. Proceeding directly to Heuristics step...")
        print("==================================================\n")

    # Step 5: Execute Physical Migrations & Image Migration (Calling Tools)
    print("--- [STEP 5: Executing Physical Move & Image Tools] ---")
    # Run note heuristics migration tool
    subprocess.run([sys.executable, str(SCRATCH_DIR / "organize_file_heuristic.py"), str(SCRATCH_DIR)], check=True)
    # Run image migration tool
    subprocess.run([sys.executable, str(SCRATCH_DIR / "move_image.py"), str(SCRATCH_DIR)], check=True)

    # Step 6: Git Resolution Hand-off to Human
    print("--- [STEP 6: Vault Sandbox Ready for Human Review] ---")
    print("Your note repository has been successfully refactored on your sandbox branch.")
    print("🔍 Open Obsidian and verify that folders are clean and images are grouped.")
    print("Once approved, finalize manually in terminal:")
    print("  1. git checkout master  (Switch to master branch)")
    print("  2. git merge <sandbox-branch-name> (Merge changes)")
    print("  3. git stash pop  (Restore your saved draft work)\n")
    print("==================================================")
    print("Session completed successfully!")
    print("==================================================")


if __name__ == "__main__":
    main()
