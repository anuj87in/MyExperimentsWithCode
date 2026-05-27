"""
================================================================
🏏 MULTI-AGENT CALCULATOR BUILDER (Gemini Flash)
================================================================
Replicates the Wong Qi Han experiment: Solo Agent vs 5-Agent Team
Both approaches build the same calculator app. Compare time + tokens.

Setup:
    pip install google-genai
    
    Set your API key (do ONE of these):
      Option A (Windows CMD):    set GEMINI_API_KEY=your_key_here
      Option B (PowerShell):     $env:GEMINI_API_KEY="your_key_here"
      Option C: Paste directly into API_KEY variable below

Run:
    python multi_agent_calculator.py
================================================================
"""

import os
import time
from google import genai
from google.genai import types

# =========================================================
# CONFIG
# =========================================================
API_KEY = os.getenv("GEMINI_API_KEY") or ""
MODEL = "gemini-2.5-flash"  # change to "gemini-2.0-flash" if 2.5 unavailable or "gemini-2.5-flash-lite"

client = genai.Client(api_key=API_KEY)

# Token tracking
stats = {"calls": 0, "input_tokens": 0, "output_tokens": 0}


def call_agent(role_name, system_prompt, user_message):
    """
    Ek agent = ek LLM call with a specific role.
    Yahi function har 'agent' represent karta hai.
    """
    stats["calls"] += 1

    print(f"\n{'─' * 60}")
    print(f"🎙️  {role_name} is thinking...")
    print(f"{'─' * 60}")

    response = client.models.generate_content(
        model=MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
        ),
    )

    # Track tokens for cost analysis
    if response.usage_metadata:
        stats["input_tokens"] += response.usage_metadata.prompt_token_count or 0
        stats["output_tokens"] += response.usage_metadata.candidates_token_count or 0

    output = response.text or ""
    preview = output[:400] + ("..." if len(output) > 400 else "")
    print(f"📝 {role_name}:\n{preview}")
    return output


# =========================================================
# AGENT ROLES — har "agent" sirf ek system prompt hai
# =========================================================
PM_PROMPT = """You are a Product Manager.
Write clear, concise requirements with acceptance criteria.
Output: numbered list of 5-8 features. No fluff."""

TECH_LEAD_PROMPT = """You are a Tech Lead.
You design architecture, delegate work, integrate code, fix bugs.
Be technical, direct, and brief."""

SWE1_PROMPT = """You are a frontend developer.
Write ONLY HTML and CSS (no JavaScript yet).
Dark theme, responsive grid layout for a calculator.
Output ONLY code inside one ```html block. No explanations."""

SWE2_PROMPT = """You are a JavaScript developer.
Write ONLY the JavaScript logic for a calculator.
Handle: arithmetic, keyboard events, history (last 5), error cases.
Output ONLY code inside one ```javascript block. No explanations."""

QA_PROMPT = """You are a strict QA engineer.
Carefully test the code for bugs and edge cases.
Output format: numbered list of bugs found,
OR exactly the string 'NO_BUGS_FOUND' if everything works."""

SOLO_PROMPT = """You are a senior full-stack developer.
Build complete, polished apps in a single HTML file.
Output ONLY the final HTML code inside one ```html block."""


# =========================================================
# APPROACH 1: SOLO AGENT (1 API call)
# =========================================================
def build_solo(goal):
    print("\n" + "=" * 60)
    print("🏃 SOLO BUILDER — 1 agent, 1 call")
    print("=" * 60)
    return call_agent("Solo Dev 🏃", SOLO_PROMPT, goal)


# =========================================================
# APPROACH 2: 5-AGENT TEAM (the orchestrator)
# =========================================================
def build_with_team(goal):
    print("\n" + "=" * 60)
    print("🏢 CORPORATE TEAM — 5 agents, multiple rounds")
    print("=" * 60)

    # Round 1: PM writes requirements
    requirements = call_agent("PM 🧑‍💼", PM_PROMPT, goal)

    # Round 2: Tech Lead designs architecture
    architecture = call_agent(
        "Tech Lead 🧑‍🔧 (architecture)",
        TECH_LEAD_PROMPT,
        f"Design architecture for these requirements:\n\n{requirements}",
    )

    # Round 3: SWE-1 builds UI
    ui_code = call_agent(
        "SWE-1 (UI) 🎨",
        SWE1_PROMPT,
        f"Build UI for:\n{requirements}\n\nArchitecture:\n{architecture}",
    )

    # Round 4: SWE-2 builds logic
    logic_code = call_agent(
        "SWE-2 (Logic) ⚙️",
        SWE2_PROMPT,
        f"Build JS logic for:\n{requirements}\n\nArchitecture:\n{architecture}",
    )

    # Round 5: Tech Lead integrates
    integrated = call_agent(
        "Tech Lead 🧑‍🔧 (integrate)",
        TECH_LEAD_PROMPT,
        f"""Integrate the UI and logic into ONE complete HTML file.
Output ONLY the final HTML code inside a ```html block.

UI:
{ui_code}

Logic:
{logic_code}""",
    )

    # Round 6: QA tests
    bugs = call_agent(
        "QA 🐛", QA_PROMPT, f"Test this calculator code:\n\n{integrated}"
    )

    # Round 7+: Bug fix loop (max 2 rounds)
    iteration = 0
    while "NO_BUGS_FOUND" not in bugs and iteration < 2:
        iteration += 1
        print(f"\n🔁 BUG FIX ROUND {iteration}")

        integrated = call_agent(
            f"Tech Lead 🧑‍🔧 (fix #{iteration})",
            TECH_LEAD_PROMPT,
            f"""Fix these bugs and output the COMPLETE corrected HTML.
Output ONLY the code inside a ```html block.

Bugs:
{bugs}

Current code:
{integrated}""",
        )

        bugs = call_agent("QA 🐛", QA_PROMPT, f"Test again:\n\n{integrated}")

    return integrated


# =========================================================
# UTILITIES
# =========================================================
def extract_html(text):
    """LLM ka output mein markdown fences hote hain — strip karte hain"""
    if "```html" in text:
        text = text.split("```html", 1)[1]
    elif "```" in text:
        text = text.split("```", 1)[1]
    if "```" in text:
        text = text.rsplit("```", 1)[0]
    return text.strip()


def reset_stats():
    stats["calls"] = 0
    stats["input_tokens"] = 0
    stats["output_tokens"] = 0


def print_stats(label, elapsed):
    total = stats["input_tokens"] + stats["output_tokens"]
    print("\n" + "─" * 60)
    print(f"📊 {label}")
    print("─" * 60)
    print(f"  ⏱️  Time:         {elapsed:.1f} seconds")
    print(f"  📞 API calls:    {stats['calls']}")
    print(f"  📥 Input tokens:  {stats['input_tokens']:,}")
    print(f"  📤 Output tokens: {stats['output_tokens']:,}")
    print(f"  🔢 Total tokens:  {total:,}")
    return {"time": elapsed, "calls": stats["calls"], "tokens": total}


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    GOAL = """Build an interactive calculator with:
- Basic arithmetic (+, -, ×, ÷)
- Keyboard input support
- Calculation history (last 5 entries shown)
- Clear and backspace buttons
- Responsive dark theme with modern styling
- Error handling for division by zero
Deliver as a SINGLE self-contained HTML file."""

    # ---- SOLO RUN ----
    reset_stats()
    t0 = time.time()
    solo_output = build_solo(GOAL)
    solo_metrics = print_stats("SOLO RESULT", time.time() - t0)

    with open("solo_calculator.html", "w", encoding="utf-8") as f:
        f.write(extract_html(solo_output))
    print("  ✅ Saved: solo_calculator.html")

    # ---- TEAM RUN ----
    reset_stats()
    t0 = time.time()
    team_output = build_with_team(GOAL)
    team_metrics = print_stats("TEAM RESULT", time.time() - t0)

    with open("team_calculator.html", "w", encoding="utf-8") as f:
        f.write(extract_html(team_output))
    print("  ✅ Saved: team_calculator.html")

    # ---- COMPARISON (the punchline) ----
    print("\n" + "=" * 60)
    print("🏏 FINAL SCORECARD — Solo vs Team")
    print("=" * 60)
    print(f"{'Metric':<15} {'Solo':>15} {'Team':>15} {'Multiplier':>12}")
    print("-" * 60)

    def fmt_mult(team_val, solo_val):
        if solo_val == 0:
            return "N/A"
        return f"{team_val / solo_val:.1f}×"

    print(
        f"{'Time (s)':<15} "
        f"{solo_metrics['time']:>15.1f} "
        f"{team_metrics['time']:>15.1f} "
        f"{fmt_mult(team_metrics['time'], solo_metrics['time']):>12}"
    )
    print(
        f"{'API calls':<15} "
        f"{solo_metrics['calls']:>15} "
        f"{team_metrics['calls']:>15} "
        f"{fmt_mult(team_metrics['calls'], solo_metrics['calls']):>12}"
    )
    print(
        f"{'Total tokens':<15} "
        f"{solo_metrics['tokens']:>15,} "
        f"{team_metrics['tokens']:>15,} "
        f"{fmt_mult(team_metrics['tokens'], solo_metrics['tokens']):>12}"
    )

    overhead = (
        (team_metrics["tokens"] - solo_metrics["tokens"])
        / team_metrics["tokens"]
        * 100
        if team_metrics["tokens"]
        else 0
    )
    print(f"\n💸 Coordination overhead: {overhead:.1f}% of team tokens")
    print("\n👉 Open both HTML files in your browser to compare quality.")
    print("=" * 60)
