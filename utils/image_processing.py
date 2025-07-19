import os
from PIL import Image

def process_image(image_path: str, output_dir: str = "downloads") -> str:
    try:
        os.makedirs(output_dir, exist_ok=True)
        with Image.open(image_path) as img:
            img.load()
        resized_img = img.resize((1280, 720))
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        if resized_img.mode != 'RGB':
            resized_img = resized_img.convert('RGB')
        new_image_path = os.path.join(f"{base_name}.jpg")
        resized_img.save(new_image_path, format="JPEG")
        return new_image_path
    except Exception as e:
        print(f"Error processing image: {e}")
        return ""
    
process_image1 = process_image("utils/const1.png")