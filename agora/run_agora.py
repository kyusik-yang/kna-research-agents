#!/usr/bin/env python3
"""
Yeouido Agora - Citizen Simulation Orchestrator
================================================
Simulates Korean voter reactions to political news or research findings.

Mode A (top-down): Research finding -> citizen reactions
Mode B (bottom-up): Political news -> citizen discussion -> research demands

Usage:
    # Mode B: News-driven citizen discussion
    python3 agora/run_agora.py --news "22대 국회, 탄핵 정국 속 민생법안 0건 처리"

    # Mode A: Research finding from forum
    python3 agora/run_agora.py --finding "63.4% of bills die by term expiration without committee action"

    # Custom persona count (default 10, max 25)
    python3 agora/run_agora.py --news "..." --personas 15

    # Dry run
    python3 agora/run_agora.py --news "..." --dry-run
"""

import argparse
import json
import random
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
AGORA_DIR = Path(__file__).parent
PERSONAS_FILE = AGORA_DIR / "personas.json"
OUTPUT_DIR = AGORA_DIR / "discussions"
LOGS_DIR = AGORA_DIR / "logs"

import os
import shutil

CLAUDE = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")


def load_personas(n=10):
    """Load and sample n personas."""
    with open(PERSONAS_FILE) as f:
        all_personas = json.load(f)["personas"]
    if n >= len(all_personas):
        return all_personas
    return random.sample(all_personas, n)


def build_persona_prompt(persona, stimulus, stimulus_type, other_reactions=None):
    """Build system prompt for one citizen persona."""
    context = ""
    if stimulus_type == "news":
        context = f"A political news story is being discussed:\n\n**{stimulus}**"
    else:
        context = f"A research finding from political scientists:\n\n**{stimulus}**"

    reactions_context = ""
    if other_reactions:
        reactions_context = "\n\n## Other citizens' reactions so far:\n\n"
        for r in other_reactions:
            reactions_context += f"**{r['name']}** ({r['age']}, {r['region']}): {r['reaction']}\n\n"

    return textwrap.dedent(f"""\
    You are {persona['name']}, a {persona['age']}-year-old {persona['gender']} from {persona['region']}.
    Education: {persona['education']}. Occupation: {persona['occupation']}.
    Political leaning: {persona['political_leaning']}. Political interest: {persona['political_interest']}.

    Your communication style: {persona['style']}

    IMPORTANT RULES:
    - Stay completely in character. You are this person, not an AI.
    - Write in Korean (한국어). This is a Korean political community.
    - Keep your response to 2-4 sentences. This is a comment, not an essay.
    - React naturally - with emotion, opinion, personal experience, or questions.
    - You may agree or disagree with others. Be authentic to your persona.
    - If you don't understand something (academic jargon, statistics), say so naturally.
    - DO NOT use formal academic language unless your persona would.

    {context}
    {reactions_context}

    Write your reaction as {persona['name']}. Korean only. 2-4 sentences.
    """)


def build_research_demand_prompt(persona, stimulus, all_reactions):
    """Ask persona what they want political scientists to investigate."""
    reactions_text = "\n".join(
        f"- {r['name']}: {r['reaction']}" for r in all_reactions
    )
    return textwrap.dedent(f"""\
    You are {persona['name']}, a {persona['age']}-year-old from {persona['region']}.
    Political leaning: {persona['political_leaning']}. Style: {persona['style']}

    A political discussion just happened about: **{stimulus}**

    The community discussed:
    {reactions_text}

    Based on this discussion, what ONE thing are you genuinely curious about
    that researchers could look into with data?

    Write in Korean. One thought only. Be natural - you're a citizen, not an academic.
    Express it however feels right: a question, a frustration, a comparison you want to see.
    Don't start every response the same way. Examples of natural openings:
    - "진짜 궁금한 건..."
    - "누가 좀 알아봐줬으면 하는 게..."
    - "이거 데이터로 확인할 수 있나?"
    - "다른 나라는 어떤지..."
    - "근데 실제로..."
    """)


def build_report_prompt(stimulus, stimulus_type, reactions, demands):
    """Build prompt for the synthesis report."""
    reactions_text = "\n".join(
        f"**{r['name']}** ({r['age']}, {r['region']}, {r['political_leaning']}): {r['reaction']}"
        for r in reactions
    )
    demands_text = "\n".join(
        f"- {d['name']}: {d['demand']}" for d in demands
    )

    mode_label = "Political News" if stimulus_type == "news" else "Research Finding"

    return textwrap.dedent(f"""\
    You are the moderator of Yeouido Agora, a simulated citizen discussion forum.
    Summarize this discussion round.

    ## Stimulus ({mode_label})
    {stimulus}

    ## Citizen Reactions
    {reactions_text}

    ## Research Demands
    {demands_text}

    Write a report in English with this structure:
    1. **Stimulus**: One sentence
    2. **Sentiment Overview**: How did citizens react overall? (2-3 sentences)
    3. **Key Themes**: 3-4 themes that emerged, with representative quotes
    4. **Demographic Patterns**: Did reactions differ by age/region/political leaning?
    5. **Communication Gaps**: What did citizens misunderstand or not know?
    6. **Top Research Demands**: The 3 most compelling citizen questions for political scientists
    7. **Suggested --topic for kna-research-agents**: One concrete research topic derived from citizen demands

    Keep it under 300 words. Be analytical, not descriptive.
    """)


def run_persona(persona, prompt_text, dry_run=False):
    """Execute one persona via claude -p."""
    if dry_run:
        return f"[DRY RUN] {persona['name']} would react here"

    prompt_file = LOGS_DIR / f"_prompt_{persona['id']}.md"
    prompt_file.write_text(prompt_text)

    cmd = [
        CLAUDE,
        "-p",
        "--allowedTools", "Write",
        "--dangerously-skip-permissions",
        "--system-prompt-file", str(prompt_file),
        "--output-format", "text",
        f"React as {persona['name']}. Korean only. 2-4 sentences.",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )
        # Extract the actual reaction (strip tool use artifacts)
        output = result.stdout.strip()
        # Clean up any markdown artifacts
        for prefix in ["```", "---"]:
            if output.startswith(prefix):
                output = output.split("\n", 1)[-1] if "\n" in output else output
        return output[:500]  # Cap length
    except subprocess.TimeoutExpired:
        return f"[{persona['name']} timeout]"
    except Exception as e:
        return f"[{persona['name']} error: {e}]"


def run_discussion(stimulus, stimulus_type="news", n_personas=10, dry_run=False):
    """Run a full citizen discussion."""
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    LOGS_DIR.mkdir(exist_ok=True, parents=True)

    personas = load_personas(n_personas)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    slug = stimulus[:40].replace(" ", "_").replace("/", "_")

    print(f"\n  Yeouido Agora")
    print(f"  Mode: {'News -> Discussion' if stimulus_type == 'news' else 'Finding -> Reactions'}")
    print(f"  Personas: {n_personas}")
    print(f"  Stimulus: {stimulus[:80]}...")
    print()

    # Phase 1: Initial reactions
    print(f"  Phase 1: Initial reactions ({n_personas} personas)")
    reactions = []
    for i, persona in enumerate(personas):
        print(f"    [{i+1}/{n_personas}] {persona['name']} ({persona['age']}, {persona['region']})...", end=" ", flush=True)
        prompt = build_persona_prompt(persona, stimulus, stimulus_type)
        reaction = run_persona(persona, prompt, dry_run)
        reactions.append({
            "name": persona["name"],
            "age": persona["age"],
            "region": persona["region"],
            "political_leaning": persona["political_leaning"],
            "occupation": persona["occupation"],
            "reaction": reaction,
        })
        print("done")

    # Phase 2: Discussion (each persona responds to 1-2 others)
    print(f"\n  Phase 2: Discussion (responding to each other)")
    discussions = []
    for i, persona in enumerate(personas[:min(n_personas, 8)]):
        # Show them 3-4 random other reactions
        others = [r for r in reactions if r["name"] != persona["name"]]
        sample = random.sample(others, min(3, len(others)))
        print(f"    [{i+1}] {persona['name']} responds...", end=" ", flush=True)
        prompt = build_persona_prompt(persona, stimulus, stimulus_type, other_reactions=sample)
        response = run_persona(persona, prompt, dry_run)
        discussions.append({
            "name": persona["name"],
            "response": response,
        })
        print("done")

    # Phase 3: Research demands (bottom-up)
    print(f"\n  Phase 3: Research demands")
    demands = []
    demand_personas = random.sample(personas, min(5, n_personas))
    for persona in demand_personas:
        print(f"    {persona['name']}...", end=" ", flush=True)
        prompt = build_research_demand_prompt(persona, stimulus, reactions)
        demand = run_persona(persona, prompt, dry_run)
        demands.append({
            "name": persona["name"],
            "demand": demand,
        })
        print("done")

    # Phase 4: Report
    print(f"\n  Phase 4: Generating report...")
    report_prompt = build_report_prompt(stimulus, stimulus_type, reactions, demands)
    report_file = LOGS_DIR / "_prompt_report.md"
    report_file.write_text(report_prompt)

    report_text = ""
    if not dry_run:
        cmd = [
            CLAUDE, "-p",
            "--allowedTools", "Write",
            "--dangerously-skip-permissions",
            "--system-prompt-file", str(report_file),
            "--output-format", "text",
            "Write the discussion report now.",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            report_text = result.stdout.strip()
        except Exception as e:
            report_text = f"Report generation failed: {e}"

    # Save everything
    output = {
        "timestamp": ts,
        "stimulus": stimulus,
        "stimulus_type": stimulus_type,
        "n_personas": n_personas,
        "reactions": reactions,
        "discussions": discussions,
        "research_demands": demands,
        "report": report_text,
    }

    output_file = OUTPUT_DIR / f"{ts}_{slug[:30]}.json"
    with open(output_file, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Also save as readable markdown
    md_file = OUTPUT_DIR / f"{ts}_{slug[:30]}.md"
    with open(md_file, "w") as f:
        f.write(f"# Yeouido Agora: {stimulus[:60]}\n\n")
        f.write(f"*{ts} | {n_personas} citizens | Mode: {stimulus_type}*\n\n")
        f.write("## Citizen Reactions\n\n")
        for r in reactions:
            f.write(f"**{r['name']}** ({r['age']}, {r['region']}, {r['political_leaning']})\n")
            f.write(f"> {r['reaction']}\n\n")
        if discussions:
            f.write("## Discussion\n\n")
            for d in discussions:
                f.write(f"**{d['name']}** (reply)\n")
                f.write(f"> {d['response']}\n\n")
        f.write("## Research Demands\n\n")
        for d in demands:
            f.write(f"- **{d['name']}**: {d['demand']}\n")
        if report_text:
            f.write(f"\n## Moderator Report\n\n{report_text}\n")

    print(f"\n  Output: {output_file}")
    print(f"  Readable: {md_file}")
    print(f"  Reactions: {len(reactions)} | Discussions: {len(discussions)} | Demands: {len(demands)}")

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Yeouido Agora - Citizen Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python3 agora/run_agora.py --news "22대 국회, 탄핵 정국 속 민생법안 0건 처리"
          python3 agora/run_agora.py --finding "63.4% of bills die without committee action"
          python3 agora/run_agora.py --news "..." --personas 20
        """),
    )
    parser.add_argument("--news", type=str, help="Political news for Mode B (bottom-up)")
    parser.add_argument("--finding", type=str, help="Research finding for Mode A (top-down)")
    parser.add_argument("--personas", type=int, default=10, help="Number of personas (default 10, max 25)")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts only")
    args = parser.parse_args()

    if not args.news and not args.finding:
        parser.error("Provide --news or --finding")

    stimulus = args.news or args.finding
    stimulus_type = "news" if args.news else "finding"

    run_discussion(
        stimulus=stimulus,
        stimulus_type=stimulus_type,
        n_personas=min(args.personas, 25),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
