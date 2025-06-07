import os
from PIL import Image

def resize_rename_trim_pngs(folder_path, prefix, scale_percent=100):
    folder_name = os.path.basename(folder_path).replace('resized_images', '').strip('_')
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".png"):
            file_path = os.path.join(folder_path, filename)
            
            with Image.open(file_path) as img:
                img = img.convert("RGBA")
                width, height = img.size
                
                # Scale by percentage
                new_width = int(width * (scale_percent / 100))
                new_height = int(height * (scale_percent / 100))
                img = img.resize((new_width, new_height), Image.LANCZOS) 
                
                bbox = img.getbbox() 
                if bbox:
                    img = img.crop(bbox) 
                    width, height = img.size
            
            base_filename = f"{prefix}_{width}x{height}".replace('__', '_')
            new_filename = f"{base_filename}.png"
            new_path = os.path.join(folder_path, new_filename)
            
            counter = 1
            while os.path.exists(new_path):
                new_filename = f"{base_filename}_{counter}.png"
                new_path = os.path.join(folder_path, new_filename)
                counter += 1
            
            img.save(new_path)  # Save resized and trimmed image
            print(f"Resized, renamed, and trimmed {filename} -> {new_filename}")

if __name__ == "__main__":
    folder_path = input("Enter the path to the folder with PNGs: ").strip('"')
    prefix = input("Enter the prefix for the new file names: ")
    try:
        scale_percent = float(input("Enter the scale percent (e.g., 50 for 50%): "))
    except ValueError:
        print("Invalid input for scale percent. Using default 100%.")
        scale_percent = 100.0

    resize_rename_trim_pngs(folder_path, prefix, scale_percent)
