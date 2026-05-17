#!/usr/bin/env python3
"""Download a Hugging Face model repo into a local folder and report size."""
from huggingface_hub import snapshot_download
import argparse
import os


def get_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except Exception:
                pass
    return total


def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P']:
        if abs(num) < 1024.0:
            return f"{num:.2f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.2f}Y{suffix}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-id', required=True, help='Hugging Face model repo id, e.g. sentence-transformers/all-MiniLM-L6-v2')
    parser.add_argument('--dest', default=os.path.join(os.path.dirname(__file__), 'models'), help='Destination cache dir')
    parser.add_argument('--allow-patterns', default=None, help='Comma-separated glob patterns to include (e.g. "*.safetensors,*.json,tokenizer*")')
    args = parser.parse_args()

    dest = os.path.abspath(args.dest)
    os.makedirs(dest, exist_ok=True)

    print(f"Downloading {args.model_id} into {dest} (this may take a few minutes)...")
    patterns = None
    if args.allow_patterns:
        patterns = [p.strip() for p in args.allow_patterns.split(',') if p.strip()]

    repo_dir = snapshot_download(repo_id=args.model_id, cache_dir=dest, resume_download=True, allow_patterns=patterns)

    print("Download complete.")
    print("Model files in:", repo_dir)

    size = get_size(repo_dir)
    print("Total size:", sizeof_fmt(size))


if __name__ == '__main__':
    main()
