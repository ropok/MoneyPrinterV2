"""
CLI tool for managing the prompt database.

Usage:
    python manage_prompts.py list                    # List all prompts
    python manage_prompts.py list --status pending   # Filter by status
    python manage_prompts.py stats                   # Show stats
    python manage_prompts.py add                     # Add a prompt interactively
    python manage_prompts.py seed                    # Seed with math topics
    python manage_prompts.py reset --id 5            # Reset prompt #5 to pending
    python manage_prompts.py reset --failed          # Reset all failed
    python manage_prompts.py delete --id 5           # Delete prompt #5
    python manage_prompts.py search "pythagoras"     # Search prompts
    python manage_prompts.py export                  # Export to prompts.csv
    python manage_prompts.py import --file my.csv    # Import from CSV
"""

import sys
import os
import argparse
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_db import PromptDB


# -----------------------------------------------------------------------
# Pre-loaded math prompt library — 30 topics ready to go
# -----------------------------------------------------------------------
MATH_PROMPTS = [
    {
        "topic": "Pythagorean Theorem",
        "prompt": "Create a 60-second YouTube Shorts script about the Pythagorean Theorem. Hook (5s): 'Before GPS existed, THIS formula guided every ship at sea...' Formula (15s): Explain a² + b² = c² simply, like talking to a 12-year-old. History (20s): Pythagoras discovered it in 570 BC, but Babylonians used it 1000 years earlier. Real world (15s): Used in GPS, architecture, game physics engines. CTA (5s): Follow for a new math secret every day. Tone: Energetic, conversational, no jargon."
    },
    {
        "topic": "Euler's Number (e)",
        "prompt": "Create a 60-second YouTube Shorts script about Euler's Number e ≈ 2.718. Hook: 'This number appears in nature, finance, and black holes.' Explain what e is simply. History: Discovered by Jacob Bernoulli studying compound interest in 1683. Real world: Used in population growth, radioactive decay, and loan calculations. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Fibonacci Sequence",
        "prompt": "Create a 60-second YouTube Shorts script about the Fibonacci Sequence. Hook: 'Sunflowers, galaxies, and your own hand use THIS sequence.' Explain 1,1,2,3,5,8,13... simply. History: Named after Leonardo Fibonacci, 1202 AD, but Indians knew it 1000 years earlier. Real world: Appears in flower petals, spiral shells, financial markets. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Pi (π)",
        "prompt": "Create a 60-second YouTube Shorts script about Pi π ≈ 3.14159. Hook: 'Why is THIS number infinite and non-repeating?' Explain π as circumference divided by diameter. History: Archimedes estimated it in 250 BC using polygons. Real world: Used in engineering, signal processing, GPS calculations. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Quadratic Formula",
        "prompt": "Create a 60-second YouTube Shorts script about the Quadratic Formula. Hook: 'How rockets are aimed using THIS formula.' Explain x = (-b ± √(b²-4ac)) / 2a simply. History: Ancient Babylonians solved quadratics in 2000 BC. Real world: Used in physics, engineering, and computer graphics. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Pascal's Triangle",
        "prompt": "Create a 60-second YouTube Shorts script about Pascal's Triangle. Hook: 'One triangle hides 100 math secrets inside it.' Explain the pattern of adding adjacent numbers. History: Known in China (1303) and India (10th century), before Pascal (1653). Real world: Used in probability, algebra, and computer science. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Imaginary Numbers",
        "prompt": "Create a 60-second YouTube Shorts script about Imaginary Numbers. Hook: 'Numbers that SHOULDN'T exist but power your phone.' Explain i = √(-1) simply. History: Invented by Gerolamo Cardano in 1545 who called them fictitious. Real world: Used in electrical engineering, quantum physics, signal processing. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Prime Numbers",
        "prompt": "Create a 60-second YouTube Shorts script about Prime Numbers. Hook: 'Why banks use PRIME numbers to protect your money.' Explain what primes are simply. History: Euclid proved there are infinite primes around 300 BC. Real world: Used in RSA encryption protecting every online transaction. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Zero (0)",
        "prompt": "Create a 60-second YouTube Shorts script about the number Zero. Hook: 'This number was BANNED in Ancient Rome.' Explain what zero is and why it's special. History: Invented in India by Brahmagupta around 628 AD, spread through Arabic mathematicians. Real world: Without zero there would be no computers, no calculus, no modern physics. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Infinity (∞)",
        "prompt": "Create a 60-second YouTube Shorts script about Infinity. Hook: 'Some infinities are BIGGER than other infinities.' Explain the concept simply. History: Georg Cantor proved different sizes of infinity in 1874, was ridiculed for it. Real world: Used in calculus, set theory, and computer science limits. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Euler's Identity",
        "prompt": "Create a 60-second YouTube Shorts script about Euler's Identity: e^(iπ) + 1 = 0. Hook: 'Called the most beautiful equation in mathematics.' Explain why it connects e, i, π, 1 and 0. History: Leonhard Euler derived it in the 18th century. Real world: Foundation of electrical engineering and quantum mechanics. CTA: Follow for daily math secrets."
    },
    {
        "topic": "The Golden Ratio",
        "prompt": "Create a 60-second YouTube Shorts script about the Golden Ratio φ ≈ 1.618. Hook: 'Artists and architects have used THIS ratio for 4000 years.' Explain φ = (1+√5)/2 simply. History: Ancient Greeks used it in the Parthenon, Leonardo da Vinci in art. Real world: Found in face proportions, plant growth, stock market patterns. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Bayes Theorem",
        "prompt": "Create a 60-second YouTube Shorts script about Bayes Theorem. Hook: 'This formula helps doctors diagnose cancer and spam filters block emails.' Explain conditional probability simply. History: Reverend Thomas Bayes, 1763, published after his death. Real world: Used in medical diagnosis, spam filters, AI, weather forecasting. CTA: Follow for daily math secrets."
    },
    {
        "topic": "The Monty Hall Problem",
        "prompt": "Create a 60-second YouTube Shorts script about the Monty Hall Problem. Hook: 'Even mathematicians got this probability puzzle WRONG.' Explain the three doors problem simply. History: Named after game show host Monty Hall, made famous by Marilyn vos Savant in 1990. Real world: Teaches conditional probability and counterintuitive thinking. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Calculus — Derivatives",
        "prompt": "Create a 60-second YouTube Shorts script about Derivatives in Calculus. Hook: 'This math concept helps Tesla calculate when to brake.' Explain rate of change simply. History: Newton and Leibniz invented calculus independently around 1675, causing a huge rivalry. Real world: Used in physics, economics, machine learning. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Game Theory — Nash Equilibrium",
        "prompt": "Create a 60-second YouTube Shorts script about Nash Equilibrium. Hook: 'This theory explains why traffic jams happen even when everyone drives optimally.' Explain Nash Equilibrium simply. History: John Nash won the Nobel Prize for it in 1994 — his story inspired A Beautiful Mind. Real world: Used in economics, politics, evolutionary biology. CTA: Follow for daily math secrets."
    },
    {
        "topic": "The Birthday Paradox",
        "prompt": "Create a 60-second YouTube Shorts script about the Birthday Paradox. Hook: 'In a room of just 23 people, there is a 50% chance two share a birthday.' Explain the probability simply. History: First described by mathematician Richard von Mises in 1939. Real world: Used in cryptography to explain hash collision attacks. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Four Color Theorem",
        "prompt": "Create a 60-second YouTube Shorts script about the Four Color Theorem. Hook: 'You only need 4 colors to color any map so no two neighbors match.' Explain the theorem simply. History: First conjectured in 1852, took 124 years to prove — the first proof used a computer in 1976. Real world: Used in register allocation in compilers and scheduling problems. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Fractals",
        "prompt": "Create a 60-second YouTube Shorts script about Fractals. Hook: 'Coastlines are infinite in length — and this math proves it.' Explain self-similarity simply. History: Benoit Mandelbrot coined fractal in 1975, though patterns known since the 1800s. Real world: Used in computer graphics, antenna design, stock market analysis. CTA: Follow for daily math secrets."
    },
    {
        "topic": "RSA Encryption",
        "prompt": "Create a 60-second YouTube Shorts script about RSA Encryption. Hook: 'Every time you buy something online, THIS math protects your card.' Explain prime factorization encryption simply. History: Invented by Rivest, Shamir, Adleman at MIT in 1977. Real world: Secures HTTPS, email, banking, government communication. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Zeno's Paradox",
        "prompt": "Create a 60-second YouTube Shorts script about Zeno's Paradox. Hook: 'An ancient Greek philosopher PROVED that motion is impossible — using math.' Explain Achilles and the tortoise simply. History: Zeno of Elea, around 450 BC, stumped philosophers for 2000 years. Real world: Led to the invention of limits and calculus to resolve it. CTA: Follow for daily math secrets."
    },
    {
        "topic": "The Number 1729 (Taxicab Number)",
        "prompt": "Create a 60-second YouTube Shorts script about the number 1729. Hook: 'A dying mathematician saw something special in a taxi number.' Explain 1729 = 1³+12³ = 9³+10³. History: Srinivasa Ramanujan noticed it from his hospital bed in 1919 when Hardy visited in cab 1729. Real world: Led to the study of taxicab numbers and number theory. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Statistics — Standard Deviation",
        "prompt": "Create a 60-second YouTube Shorts script about Standard Deviation. Hook: 'This stat tells you if your test score is actually good or just average.' Explain spread of data simply. History: Carl Friedrich Gauss developed it in the early 1800s. Real world: Used in quality control, medicine, finance, and grading on a curve. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Napier's Logarithms",
        "prompt": "Create a 60-second YouTube Shorts script about Logarithms. Hook: 'Before calculators, THIS invention saved astronomers years of work.' Explain log as the inverse of exponential. History: John Napier published logarithm tables in 1614, a revolution in calculation. Real world: Used in earthquake magnitude, sound decibels, pH scale, and computer algorithms. CTA: Follow for daily math secrets."
    },
    {
        "topic": "The Travelling Salesman Problem",
        "prompt": "Create a 60-second YouTube Shorts script about the Travelling Salesman Problem. Hook: 'This problem could be worth a million dollars if you solve it.' Explain finding the shortest route simply. History: Formulated in the 1930s, still unsolved for large cases. Real world: Used in delivery routing, circuit board design, DNA sequencing. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Boolean Algebra",
        "prompt": "Create a 60-second YouTube Shorts script about Boolean Algebra. Hook: 'Every computer on Earth runs on THIS math invented in 1854.' Explain TRUE/FALSE logic simply. History: George Boole invented it in 1854, Claude Shannon applied it to circuits in 1937. Real world: Foundation of all digital computers, logic gates, programming. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Vectors",
        "prompt": "Create a 60-second YouTube Shorts script about Vectors. Hook: 'THIS math is how your phone knows which direction you are facing.' Explain magnitude and direction simply. History: William Rowan Hamilton developed vector algebra in the 1840s. Real world: Used in GPS, game physics, AI, robotics, and 3D graphics. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Matrix Multiplication",
        "prompt": "Create a 60-second YouTube Shorts script about Matrix Multiplication. Hook: 'Every AI you have ever used runs on THIS operation millions of times per second.' Explain matrices as grids of numbers simply. History: Arthur Cayley introduced matrix algebra in 1858. Real world: Foundation of machine learning, computer graphics, and Google PageRank. CTA: Follow for daily math secrets."
    },
    {
        "topic": "Topology — Seven Bridges of Königsberg",
        "prompt": "Create a 60-second YouTube Shorts script about the Seven Bridges of Königsberg. Hook: 'A city puzzle stumped everyone until Euler invented a whole new branch of math.' Explain the bridge-crossing problem simply. History: Euler solved it in 1736, founding graph theory and topology. Real world: Used in network design, route planning, and internet architecture. CTA: Follow for daily math secrets."
    },
    {
        "topic": "The Riemann Hypothesis",
        "prompt": "Create a 60-second YouTube Shorts script about the Riemann Hypothesis. Hook: 'Solve THIS and win one million dollars — no one has in 165 years.' Explain prime number distribution simply. History: Bernhard Riemann proposed it in 1859, one of the Clay Millennium Prize Problems. Real world: Proves the pattern of prime numbers, fundamental to cryptography. CTA: Follow for daily math secrets."
    },
]


def cmd_list(db: PromptDB, status: str = None):
    if status:
        rows = db.get_pending(statuses=[status])
    else:
        rows = db.get_all()

    if not rows:
        print("No prompts found.")
        return

    print(f"\n{'ID':>4}  {'Status':<12}  {'Topic':<45}  {'Scheduled'}")
    print("-" * 80)
    for r in rows:
        scheduled = r.get("scheduled_date") or ""
        print(f"{r['id']:>4}  {r['status']:<12}  {r['topic'][:45]:<45}  {scheduled}")
    print(f"\nTotal: {len(rows)}\n")


def cmd_stats(db: PromptDB):
    stats = db.get_stats()
    total = sum(stats.values())
    print(f"\n{'='*35}")
    print(f"  PROMPT DATABASE STATS")
    print(f"{'='*35}")
    for status, count in sorted(stats.items()):
        bar = "█" * min(count, 30)
        print(f"  {status:<12} {count:>4}  {bar}")
    print(f"  {'TOTAL':<12} {total:>4}")
    print(f"{'='*35}\n")


def cmd_add(db: PromptDB):
    print("\nAdd a new prompt (Ctrl+C to cancel)")
    topic = input("Topic: ").strip()
    if not topic:
        print("Topic cannot be empty.")
        return
    print("Prompt (paste your full prompt, press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    prompt = "\n".join(lines).strip()
    if not prompt:
        print("Prompt cannot be empty.")
        return
    new_id = db.add_prompt(topic, prompt)
    print(f"✅ Added prompt #{new_id}: {topic}")


def cmd_seed(db: PromptDB):
    existing = db.get_all()
    existing_topics = {r["topic"] for r in existing}
    new_prompts = [p for p in MATH_PROMPTS if p["topic"] not in existing_topics]

    if not new_prompts:
        print("✅ All seed prompts already in database.")
        return

    count = db.add_prompts_bulk(new_prompts)
    print(f"✅ Seeded {count} new prompts into database.")
    print(f"   Skipped {len(MATH_PROMPTS) - count} already existing.")


def cmd_reset(db: PromptDB, prompt_id: int = None, all_failed: bool = False):
    if all_failed:
        db.reset_all_failed()
        print("✅ Reset all failed prompts to pending.")
    elif prompt_id:
        db.reset_status(prompt_id)
        print(f"✅ Reset prompt #{prompt_id} to pending.")
    else:
        print("Specify --id N or --failed")


def cmd_delete(db: PromptDB, prompt_id: int):
    row = db.get_by_id(prompt_id)
    if not row:
        print(f"❌ Prompt #{prompt_id} not found.")
        return
    confirm = input(f"Delete '{row['topic']}'? (yes/no): ")
    if confirm.lower() == "yes":
        db.delete_prompt(prompt_id)
        print(f"✅ Deleted prompt #{prompt_id}.")


def cmd_search(db: PromptDB, keyword: str):
    rows = db.search(keyword)
    if not rows:
        print(f"No prompts found matching '{keyword}'")
        return
    print(f"\nFound {len(rows)} result(s) for '{keyword}':\n")
    for r in rows:
        print(f"  [{r['id']}] ({r['status']}) {r['topic']}")
        print(f"       {r['prompt'][:80]}...")
    print()


def cmd_export(db: PromptDB, filepath: str = "prompts_export.csv"):
    rows = db.get_all()
    if not rows:
        print("No prompts to export.")
        return
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Exported {len(rows)} prompts to {filepath}")


def cmd_import(db: PromptDB, filepath: str):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        items = []
        for row in reader:
            if "topic" in row and "prompt" in row:
                items.append({"topic": row["topic"], "prompt": row["prompt"]})
    if not items:
        print("❌ No valid rows found. CSV must have 'topic' and 'prompt' columns.")
        return
    count = db.add_prompts_bulk(items)
    print(f"✅ Imported {count} prompts from {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Manage video generation prompts")
    subparsers = parser.add_subparsers(dest="command")

    # list
    p_list = subparsers.add_parser("list", help="List prompts")
    p_list.add_argument("--status", help="Filter by status (pending/generated/uploaded/failed)")

    # stats
    subparsers.add_parser("stats", help="Show database statistics")

    # add
    subparsers.add_parser("add", help="Add a prompt interactively")

    # seed
    subparsers.add_parser("seed", help="Seed database with 30 math topics")

    # reset
    p_reset = subparsers.add_parser("reset", help="Reset prompt(s) to pending")
    p_reset.add_argument("--id", type=int, help="Prompt ID to reset")
    p_reset.add_argument("--failed", action="store_true", help="Reset all failed")

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a prompt")
    p_delete.add_argument("--id", type=int, required=True)

    # search
    p_search = subparsers.add_parser("search", help="Search prompts")
    p_search.add_argument("keyword")

    # export
    p_export = subparsers.add_parser("export", help="Export to CSV")
    p_export.add_argument("--file", default="prompts_export.csv")

    # import
    p_import = subparsers.add_parser("import", help="Import from CSV")
    p_import.add_argument("--file", required=True)

    args = parser.parse_args()
    db = PromptDB()

    if args.command == "list":
        cmd_list(db, getattr(args, "status", None))
    elif args.command == "stats":
        cmd_stats(db)
    elif args.command == "add":
        cmd_add(db)
    elif args.command == "seed":
        cmd_seed(db)
    elif args.command == "reset":
        cmd_reset(db, getattr(args, "id", None), getattr(args, "failed", False))
    elif args.command == "delete":
        cmd_delete(db, args.id)
    elif args.command == "search":
        cmd_search(db, args.keyword)
    elif args.command == "export":
        cmd_export(db, args.file)
    elif args.command == "import":
        cmd_import(db, args.file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
