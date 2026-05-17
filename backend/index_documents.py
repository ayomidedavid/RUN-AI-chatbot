from pathlib import Path
import pickle
import argparse
import sys
from sentence_transformers import SentenceTransformer
import faiss


def chunk_text(text, min_len=100):
    # Simple paragraph splitter; combine very short paragraphs
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    buf = ""
    for p in paras:
        if len(p) < min_len and buf:
            buf += "\n\n" + p
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    return chunks


def build_index(source_path='backend/extracted_data.txt', model_name=None, out_dir=None):
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file {source_path} not found")

    text = src.read_text(encoding='utf-8')
    chunks = chunk_text(text)

    # Prefer local model folder if present to avoid remote downloads on Windows
    base = Path(__file__).resolve().parent
    local_model = base / 'models' / 'all-MiniLM-L6-v2'
    if model_name is None:
        model_name = str(local_model) if local_model.exists() else 'all-MiniLM-L6-v2'

    print(f"Loading SentenceTransformer model: {model_name}")
    try:
        model = SentenceTransformer(str(model_name))
    except Exception as e:
        print("Failed to load model. If you're offline, pass a local model folder path via --model.")
        raise

    embeddings = model.encode(chunks, show_progress_bar=True, convert_to_numpy=True)

    # normalize for cosine with inner product
    import numpy as np
    faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    if out_dir is None:
        out_dir = Path(__file__).resolve().parent
    else:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(out_dir / 'faiss.index'))
    with open(out_dir / 'chunks.pkl', 'wb') as f:
        pickle.dump(chunks, f)

    print(f'Indexed {len(chunks)} chunks. Saved faiss.index and chunks.pkl in {out_dir}')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Build FAISS index of backend/extracted_data.txt using SBERT')
    parser.add_argument('--source', '-s', default='backend/extracted_data.txt', help='Path to source text file')
    parser.add_argument('--model', '-m', default='all-MiniLM-L6-v2', help='SentenceTransformer model name or local path')
    parser.add_argument('--out', '-o', default=None, help='Output directory to save faiss.index and chunks.pkl (defaults to backend)')
    args = parser.parse_args(argv)

    try:
        build_index(source_path=args.source, model_name=args.model, out_dir=args.out)
    except Exception as e:
        print('Index build failed:', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
