from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import sys

def get_dominant_colors(image_path, k=5):
    try:
        img = Image.open(image_path)
        img = img.resize((150, 150)) # Resize for speed
        img = img.convert('RGBA')
        
        # Remove transparent background if exists
        data = np.array(img)
        r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
        mask = a > 0
        pixels = np.vstack([r[mask], g[mask], b[mask]]).T
        
        if len(pixels) == 0:
            print("Image is fully transparent.")
            return []

        kmeans = KMeans(n_clusters=k, n_init=10)
        kmeans.fit(pixels)
        
        colors = kmeans.cluster_centers_
        hex_colors = []
        for color in colors:
            hex_colors.append('#{:02x}{:02x}{:02x}'.format(int(color[0]), int(color[1]), int(color[2])))
            
        return hex_colors
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    image_path = sys.argv[1]
    colors = get_dominant_colors(image_path)
    print("Dominant Colors:", colors)
