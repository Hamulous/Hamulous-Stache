import cv2
import os
import shutil
import numpy as np
from PIL import Image, ImageFilter

def is_bright_uniform(image, threshold=25, coverage=0.8):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    total = gray.size
    for i in range(0, 256 - threshold):
        if np.sum(hist[i:i + threshold]) / total > coverage:
            return True
    return False

def is_glow_heavy(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    glow_mask = ((hue > 120) & (hue < 170)) & (sat > 50) & (val > 100)
    glow_ratio = cv2.countNonZero(glow_mask.astype("uint8")) / (image.shape[0] * image.shape[1])
    return glow_ratio > 0.12

def is_strongly_pink(image):
    avg_b, avg_g, avg_r = cv2.mean(image)[:3]
    return avg_r > 180 and avg_g < 130 and avg_b < 180

def is_low_edge_complexity(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 1)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return np.var(sobel) < 50 and np.var(laplacian) < 10

def is_final_glow_stroke(image, width, height):
    aspect_ratio = max(width, height) / min(width, height)
    return (
        aspect_ratio > 1.3 and
        is_bright_uniform(image) and
        is_glow_heavy(image) and
        is_strongly_pink(image) and
        is_low_edge_complexity(image)
    )

def should_skip_image(image, width, height):
    return is_final_glow_stroke(image, width, height)

def enhance_with_upscale(image_cv, scale_factor=4, sigma_color=75, sigma_space=75):
    height, width = image_cv.shape[:2]
    upscaled = cv2.resize(image_cv, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_LINEAR)
    enhanced = cv2.bilateralFilter(upscaled, d=9, sigmaColor=sigma_color, sigmaSpace=sigma_space)
    downscaled = cv2.resize(enhanced, (width, height), interpolation=cv2.INTER_AREA)
    return downscaled

def enhance_image(image_path, sigma_color=75, sigma_space=75, backup_folder=None, size_threshold=64):
    filename = os.path.basename(image_path)
    img_cv = cv2.imread(image_path)
    height, width = img_cv.shape[:2]

    if height < 32 or width < 32:
        print(f"[–] Skipped tiny sprite: {filename}")
        return
    if any(tag in filename.lower() for tag in ["eff", "glow"]) or filename.lower().endswith("_2.png"):
        print(f"[–] Skipped by tag: {filename}")
        return
    if should_skip_image(img_cv, width, height):
        print(f"[–] Skipped soft glow stroke: {filename}")
        return

    if backup_folder:
        os.makedirs(backup_folder, exist_ok=True)
        shutil.copy(image_path, os.path.join(backup_folder, filename))

    if height >= size_threshold and width >= size_threshold:
        final = enhance_with_upscale(img_cv, scale_factor=4, sigma_color=sigma_color, sigma_space=sigma_space)
        cv2.imwrite(image_path, final)
    else:
        img_pil = Image.open(image_path)
        enhanced = img_pil.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=5))
        enhanced.save(image_path)

    print(f"[✓] Enhanced: {filename}")

def batch_enhance_images(folder_path, sigma_color=75, sigma_space=75):
    supported_exts = ('.png', '.jpg', '.jpeg')
    backup_path = os.path.join(folder_path, "backup")

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(supported_exts):
            full_path = os.path.join(folder_path, filename)
            enhance_image(full_path, sigma_color, sigma_space, backup_folder=backup_path)

def main():
    print("Choose Mode:")
    print("[1] Enhance single image")
    print("[2] Enhance all images in a folder")
    choice = input("Enter 1 or 2: ").strip()

    try:
        sigma_color = float(input("Enter color strength (sigmaColor, e.g., 75): ").strip())
        sigma_space = float(input("Enter edge strength (sigmaSpace, e.g., 75): ").strip())
    except ValueError:
        print("Invalid input for sigma values. Exiting.")
        return

    if choice == "1":
        image_path = input("Enter full path to image: ").strip('"')
        if os.path.isfile(image_path):
            folder = os.path.dirname(image_path)
            backup = os.path.join(folder, "backup")
            enhance_image(image_path, sigma_color, sigma_space, backup_folder=backup)
        else:
            print("Invalid image path.")
    elif choice == "2":
        folder_path = input("Enter full path to folder: ").strip('"')
        if os.path.isdir(folder_path):
            batch_enhance_images(folder_path, sigma_color, sigma_space)
            print("[✓] All images enhanced. Originals backed up in /backup.")
        else:
            print("Invalid folder path.")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()