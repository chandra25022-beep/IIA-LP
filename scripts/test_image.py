"""
CLI tool to test license plate detection on single images or entire test directories.

Usage:
    # Test a specific image
    python scripts/test_image.py test_assets/assets/test7.jpg

    # Test all images in test_assets/assets
    python scripts/test_image.py --all

    # Test via the live backend REST API
    python scripts/test_image.py --api test_assets/assets/test7.jpg
"""
import sys
import os
import argparse
import json

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def test_single_file(pipeline, file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        data = f.read()

    res = pipeline.process_image_bytes(data)
    print("\n" + "=" * 60)
    print(f"File:        {os.path.basename(file_path)}")
    print(f"Plate:       {res.get('plate')}")
    print(f"Confidence:  {res.get('ocr_confidence', 0.0) * 100:.2f}%")
    print(f"Strategy:    {res.get('detection_strategy')}")
    print(f"Vehicle:     {res.get('vehicle_type')} ({res.get('detected_color')})")
    print(f"Valid Ind?:  {res.get('is_valid_format')}")
    origin = res.get('decoded_origin')
    if origin:
        print(f"Origin:      {origin.get('state', 'Unknown')} ({origin.get('country', '')})")
    
    candidates = res.get('candidate_plates', [])
    if candidates:
        print("\nCandidate Hypotheses:")
        for idx, c in enumerate(candidates[:5], 1):
            print(f"  {idx}. {c.get('plate'):15s} | Conf: {c.get('confidence'):.3f} | Strat: {c.get('strategy')}")
    print("=" * 60)


def test_all_files(pipeline, assets_dir: str):
    if not os.path.exists(assets_dir):
        print(f"Error: Assets directory not found: {assets_dir}")
        return

    files = sorted([
        f for f in os.listdir(assets_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.webp', '.png'))
    ])

    print("=" * 75)
    print(f"{'Image':25s} | {'Plate':15s} | {'Confidence':10s} | {'Strategy':18s}")
    print("=" * 75)

    for fname in files:
        fpath = os.path.join(assets_dir, fname)
        with open(fpath, "rb") as f:
            data = f.read()
        res = pipeline.process_image_bytes(data)
        plate = str(res.get("plate"))
        conf = f"{res.get('ocr_confidence', 0.0) * 100:.1f}%"
        strat = str(res.get("detection_strategy"))[:18]
        print(f"{fname:25s} | {plate:15s} | {conf:10s} | {strat:18s}", flush=True)

    print("=" * 75)


def test_via_api(file_path: str, api_url: str = "http://127.0.0.1:8000/api/vehicle/scan"):
    import urllib.request
    import mimetypes

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    print(f"Sending {os.path.basename(file_path)} to {api_url}...")
    try:
        import requests
        with open(file_path, "rb") as f:
            response = requests.post(api_url, files={"file": f}, timeout=15)
        if response.status_code == 200:
            print("\nAPI Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"API Error ({response.status_code}): {response.text}")
    except ImportError:
        # Fallback to curl
        os.system(f'curl.exe -s -F "file=@{file_path}" {api_url}')


def main():
    parser = argparse.ArgumentParser(description="Test License Plate Recognition")
    parser.add_argument("image_path", nargs="?", help="Path to image file to test")
    parser.add_argument("--all", action="store_true", help="Test all images in test_assets/assets")
    parser.add_argument("--dir", default=os.path.join(PROJECT_ROOT, "test_assets", "assets"), help="Assets directory")
    parser.add_argument("--api", action="store_true", help="Send to running backend server via HTTP")

    args = parser.parse_args()

    if args.api:
        if not args.image_path:
            print("Please specify an image path when using --api. Example: python scripts/test_image.py --api test_assets/assets/test7.jpg")
            return
        test_via_api(args.image_path)
        return

    from backend.app.detection.anpr_pipeline import ANPRPipeline
    pipeline = ANPRPipeline()

    if args.all:
        test_all_files(pipeline, args.dir)
    elif args.image_path:
        test_single_file(pipeline, args.image_path)
    else:
        print("Please provide an image path or use --all. Examples:")
        print("  python scripts/test_image.py test_assets/assets/test7.jpg")
        print("  python scripts/test_image.py --all")


if __name__ == "__main__":
    main()
