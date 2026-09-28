#!/usr/bin/env python3
"""
Agora stimulus helper for auto_run.sh.
======================================

Produces the Korean stimulus text that auto_run.sh hands to
agora/run_agora.py, through claude_cli.run_claude (pinned model, effort
forum_config.effort_by_task.agora, isolation, sidecar under logs/).

Usage:
    python3 scripts/agora_stimulus.py finding articles/<paper>.md
    python3 scripts/agora_stimulus.py news

Prints the result text on stdout. Exit codes: 0 ok, 1 failure,
75 (claude_cli.EXIT_USAGE_LIMIT) on a usage limit.
"""

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import claude_cli  # noqa: E402

HELPER_PROMPT = ("You are a helper for the Yeouido Agora citizen discussion of the KNA research "
                 "forum. Do exactly what the user message asks and nothing else.")

FINDING_MESSAGE = (
    "Read {article} and extract the key finding in 2-3 sentences in Korean. This is for Korean "
    "citizens to discuss. Summarize what the research found, why it matters, and one surprising "
    "number. Korean only. No English."
)

NEWS_MESSAGE = (
    "Fetch the latest Korean politics headlines from Yonhap RSS. Run: curl -sL "
    "'https://www.yna.co.kr/rss/politics.xml' | head -100. Pick the ONE headline most likely to "
    "spark citizen debate (elections, policy, scandal, reform). Expand it into 1-2 sentences of "
    "context in Korean. Return ONLY the Korean text, nothing else."
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Agora stimulus text through the forum wrapper")
    sub = ap.add_subparsers(dest="mode", required=True)
    f = sub.add_parser("finding", help="Key finding of a published article (Mode A)")
    f.add_argument("article", help="Article path, absolute or relative to the repository root")
    sub.add_parser("news", help="Most debate-worthy Yonhap politics headline (Mode B)")
    args = ap.parse_args(argv)

    if args.mode == "finding":
        article = Path(args.article)
        article = article if article.is_absolute() else BASE_DIR / article
        message, tools = FINDING_MESSAGE.format(article=article), ["Read"]
    else:
        message, tools = NEWS_MESSAGE, ["Bash"]

    try:
        res = claude_cli.run_claude("agora", HELPER_PROMPT, user_message=message, tools=tools)
    except claude_cli.ClaudeCLIError as e:
        print(f"agora_stimulus: {e}", file=sys.stderr)
        return 1
    if res.ok:
        # Text of a failed run is never printed, so an error message cannot
        # become the stimulus.
        if res.text:
            print(res.text)
        return 0
    print(f"agora_stimulus: {res.failure} (run {res.run_id})", file=sys.stderr)
    return claude_cli.EXIT_USAGE_LIMIT if res.failure == "usage_limit" else 1


if __name__ == "__main__":
    sys.exit(main())
