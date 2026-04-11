"""
Batch Video Pipeline for EasyMathExplained YouTube Channel.
Reads prompts from prompts.db, generates videos, uploads to YouTube.

Usage:
    python batch_pipeline.py              # Run batch (respects daily limit)
    python batch_pipeline.py --dry-run    # Preview what would run
    python batch_pipeline.py --limit 3    # Generate max 3 videos this run
"""

from classes.Tts import TTS
from prompt_db import PromptDB
import sys
import os
import argparse
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def parse_args():
    parser = argparse.ArgumentParser(description="Batch video generation pipeline")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview pending prompts without generating",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Max videos to generate in this run"
    )
    parser.add_argument(
        "--no-upload", action="store_true", help="Generate videos but skip uploading"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Also retry previously failed prompts",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    db = PromptDB()

    # --- Dry run: just show pending prompts ---
    if args.dry_run:
        pending = db.get_pending()
        print(f"\n{'=' * 50}")
        print(f"  PENDING PROMPTS ({len(pending)} total)")
        print(f"{'=' * 50}")
        for p in pending[:20]:
            print(f"  [{p['id']:3d}] {p['topic'][:60]}")
        if len(pending) > 20:
            print(f"  ... and {len(pending) - 20} more")
        print(f"{'=' * 50}\n")
        return

    # --- Get prompts to process ---
    statuses = ["pending"]
    if args.retry_failed:
        statuses.append("failed")

    prompts = db.get_pending(statuses=statuses)

    if not prompts:
        print("✅ No pending prompts. All done!")
        return

    limit = args.limit or len(prompts)
    prompts = prompts[:limit]

    print(f"\n{'=' * 50}")
    print(f"  BATCH PIPELINE — {len(prompts)} video(s) to generate")
    print(f"  Upload: {'YES' if not args.no_upload else 'NO (--no-upload)'}")
    print(f"{'=' * 50}\n")

    # --- Select Ollama model ---
    from llm_provider import select_model
    from config import get_ollama_model

    configured_model = get_ollama_model()
    if configured_model:
        select_model(configured_model)
    else:
        print("❌ No ollama_model set in config.json")
        print('   Add: "ollama_model": "llama3.1:8b" to config.json')
        return
    # --- Load YouTube account from cache ---
    from cache import get_accounts

    accounts = get_accounts("youtube")

    if not accounts:
        print("❌ No YouTube accounts found. Run main.py first to set up an account.")
        return

    account = accounts[0]
    print(f"  Using account: {account['nickname']}\n")

    # --- Process each prompt ---
    success_count = 0
    fail_count = 0

    for idx, prompt_row in enumerate(prompts, 1):
        prompt_id = prompt_row["id"]
        topic = prompt_row["topic"]
        prompt_text = prompt_row["prompt"]

        print(f"\n[{idx}/{len(prompts)}] Generating: {topic[:60]}")
        print(f"  Prompt: {prompt_text[:80]}...")

        # Mark as in-progress
        db.update_status(prompt_id, "generating")

        try:
            from classes.YouTube import YouTube

            tts = TTS()

            yt = YouTube(
                account_uuid=account["id"],
                account_nickname=account["nickname"],
                fp_profile_path=account["firefox_profile"],
                niche=account["niche"],
                language=account.get("language", "English"),
                custom_prompt=prompt_text,
            )

            # Generate the video
            video_path = yt.generate_video(tts)

            if not video_path or not os.path.exists(video_path):
                raise Exception("Video generation returned empty path")

            print(f"  ✅ Video generated: {video_path}")
            db.update_status(prompt_id, "generated", video_path=video_path)

            # Upload
            if not args.no_upload:
                print(f"  ⬆️  Uploading to YouTube...")
                upload_success = yt.upload_video()

                if upload_success:
                    url = getattr(yt, "uploaded_video_url", "")
                    scheduled = getattr(yt, "_scheduled_date", "")
                    print(f"  ✅ Uploaded! URL: {url}")
                    db.update_status(
                        prompt_id,
                        "uploaded",
                        video_path=video_path,
                        youtube_url=url,
                        scheduled_date=scheduled,
                    )
                    success_count += 1
                else:
                    print(f"  ⚠️  Upload failed — video saved locally")
                    db.update_status(prompt_id, "generated", video_path=video_path)
                    fail_count += 1
            else:
                success_count += 1

            # Small pause between videos
            if idx < len(prompts):
                print(f"  ⏳ Waiting 10 seconds before next video...")
                time.sleep(10)

        except KeyboardInterrupt:
            print("\n\n⛔ Interrupted by user. Progress saved.")
            db.update_status(prompt_id, "pending")  # Reset current
            break
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            db.update_status(prompt_id, "failed", notes=str(e))
            fail_count += 1

    # --- Summary ---
    print(f"\n{'=' * 50}")
    print(f"  BATCH COMPLETE")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Failed:  {fail_count}")
    print(f"  📋 Remaining pending: {len(db.get_pending())}")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()
