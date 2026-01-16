import os
import shutil
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg"}


# -----------------------
# Detection / skip logic
# -----------------------

def is_bright_uniform_banded(gray: np.ndarray, band: int = 25, coverage: float = 0.80) -> bool:
    """
    Returns True if >= coverage of pixels fall into some contiguous intensity band of width 'band'.
    Faster than scanning every possible band with repeated sums: use cumulative histogram.
    """
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).astype(np.float32).ravel()
    total = float(gray.size)
    cdf = np.cumsum(hist)

    # Sum in [i, i+band)
    for i in range(0, 256 - band):
        band_sum = cdf[i + band - 1] - (cdf[i - 1] if i > 0 else 0.0)
        if (band_sum / total) >= coverage:
            return True
    return False


def glow_ratio_hsv(bgr: np.ndarray) -> float:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    glow_mask = ((h > 120) & (h < 170)) & (s > 50) & (v > 100)
    return float(np.count_nonzero(glow_mask)) / float(glow_mask.size)


def is_strongly_pink(bgr: np.ndarray) -> bool:
    b, g, r = cv2.mean(bgr)[:3]
    return (r > 180) and (g < 130) and (b < 180)


def is_low_edge_complexity(bgr: np.ndarray) -> bool:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=3)
    lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=3)
    return (np.var(sobel) < 50.0) and (np.var(lap) < 10.0)


def is_final_glow_stroke(bgr: np.ndarray, w: int, h: int) -> bool:
    aspect_ratio = max(w, h) / max(1, min(w, h))
    if aspect_ratio <= 1.3:
        return False

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    if not is_bright_uniform_banded(gray):
        return False
    if glow_ratio_hsv(bgr) <= 0.12:
        return False
    if not is_strongly_pink(bgr):
        return False
    if not is_low_edge_complexity(bgr):
        return False

    return True


def should_skip(image_bgr: np.ndarray, filename: str) -> bool:
    h, w = image_bgr.shape[:2]

    # Cheapest checks first
    lower = filename.lower()
    if h < 32 or w < 32:
        logging.info(f"Skipped tiny sprite: {filename}")
        return True
    if any(tag in lower for tag in ("eff", "glow")) or lower.endswith("_2.png"):
        logging.info(f"Skipped by tag: {filename}")
        return True
    if is_final_glow_stroke(image_bgr, w, h):
        logging.info(f"Skipped soft glow stroke: {filename}")
        return True

    return False


# -----------------------
# Enhancement
# -----------------------

def enhance_with_upscale(bgr: np.ndarray, scale_factor: int, sigma_color: float, sigma_space: float) -> np.ndarray:
    h, w = bgr.shape[:2]
    up = cv2.resize(bgr, (w * scale_factor, h * scale_factor), interpolation=cv2.INTER_LINEAR)
    filtered = cv2.bilateralFilter(up, d=9, sigmaColor=sigma_color, sigmaSpace=sigma_space)
    down = cv2.resize(filtered, (w, h), interpolation=cv2.INTER_AREA)
    return down


def unsharp_mask_bgr(bgr: np.ndarray, radius: float = 1.0, amount: float = 1.0, threshold: int = 5) -> np.ndarray:
    """
    OpenCV unsharp mask. 'amount' ~ 1.0 equals moderate sharpening.
    """
    blurred = cv2.GaussianBlur(bgr, ksize=(0, 0), sigmaX=radius)
    sharpened = cv2.addWeighted(bgr, 1.0 + amount, blurred, -amount, 0)
    if threshold > 0:
        low_contrast = np.abs(bgr.astype(np.int16) - blurred.astype(np.int16)) < threshold
        sharpened[low_contrast] = bgr[low_contrast]
    return sharpened


def read_image_keep_alpha(path: Path):
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None, None, None

    if img.ndim == 2:
        # grayscale
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return bgr, None, "GRAY"

    if img.shape[2] == 4:
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        alpha = img[:, :, 3].copy()
        return bgr, alpha, "BGRA"

    return img, None, "BGR"


def write_image_atomic(path: Path, bgr: np.ndarray, alpha=None):
    # temp file keeps the SAME extension so OpenCV picks the right encoder
    tmp_path = path.with_name(path.stem + ".__tmp__" + path.suffix)

    if alpha is not None and path.suffix.lower() == ".png":
        bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = alpha
        ok = cv2.imwrite(str(tmp_path), bgra)
    else:
        ok = cv2.imwrite(str(tmp_path), bgr)

    if not ok:
        raise RuntimeError("cv2.imwrite failed")
    os.replace(tmp_path, path)

def enhance_one(
    image_path: Path,
    sigma_color: float,
    sigma_space: float,
    backup_dir: Path | None,
    size_threshold: int,
    dry_run: bool,
    scale_factor: int = 4,
):
    filename = image_path.name

    try:
        bgr, alpha, mode = read_image_keep_alpha(image_path)
        if bgr is None:
            logging.warning(f"Unable to read image: {filename}")
            return

        if should_skip(bgr, filename):
            return

        if dry_run:
            logging.info(f"[Dry Run] Would enhance: {filename}")
            return

        if backup_dir is not None:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, backup_dir / filename)

        h, w = bgr.shape[:2]
        if h >= size_threshold and w >= size_threshold:
            out = enhance_with_upscale(bgr, scale_factor=scale_factor, sigma_color=sigma_color, sigma_space=sigma_space)
        else:
            out = unsharp_mask_bgr(bgr, radius=1.0, amount=1.0, threshold=5)

        write_image_atomic(image_path, out, alpha=alpha)
        logging.info(f"Enhanced: {filename}")

    except Exception as e:
        logging.error(f"Error enhancing {filename}: {e}")


def batch_enhance(
    folder: Path,
    sigma_color: float,
    sigma_space: float,
    dry_run: bool = False,
    size_threshold: int = 64,
    workers: int | None = None,
):
    images = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    if not images:
        logging.info("No images found.")
        return

    backup_dir = folder / "backup"
    if dry_run:
        backup_dir = None

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [
            ex.submit(
                enhance_one,
                p,
                sigma_color,
                sigma_space,
                backup_dir,
                size_threshold,
                dry_run,
            )
            for p in images
        ]
        for _ in as_completed(futures):
            pass  # ensures we wait, and exceptions are handled inside enhance_one


if __name__ == "__main__":
    # keep your interactive flow if you want; this just shows folder usage:
    folder_path = Path(input("Enter full path to folder: ").strip('"'))
    sigma_color = float(input("Enter sigmaColor (e.g., 75): ").strip())
    sigma_space = float(input("Enter sigmaSpace (e.g., 75): ").strip())
    dry = input("Dry run? (y/n): ").strip().lower() == "y"

    batch_enhance(folder_path, sigma_color, sigma_space, dry_run=dry)
