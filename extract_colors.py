
from PIL import Image
from collections import Counter

def get_dominant_colors(image_path, num_colors=10):
    try:
        image = Image.open(image_path)
        image = image.convert('RGBA') # Keep Alpha
        image = image.resize((100, 100)) # Better resolution
        
        pixels = []
        for r, g, b, a in image.getdata():
            if a > 0: # Ignore fully transparent
                 pixels.append((r, g, b))

        counts = Counter(pixels)
        dominant = counts.most_common(num_colors)
        
        print(f"Dominant colors for {image_path}:")
        for color, count in dominant:
            hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
            if hex_color not in ['#000000', '#ffffff']: # Filter blacks/whites if needed, but risky
                print(f"Color: {color}, Hex: {hex_color}, Count: {count}")
            
    except Exception as e:
        print(f"Error: {e}")

get_dominant_colors('backend/assets/logo.png')
