from PIL import Image, ImageDraw, ImageFilter

def create_feather_mask(width, height, output_path, blur_radius=15):
    """
    Creates an elliptical soft feathered alpha mask for studio privacy blur.
    """
    mask = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        [(blur_radius, blur_radius), (width - blur_radius, height - blur_radius)],
        fill=(255, 255, 255, 255)
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    mask.save(output_path)
    return output_path

if __name__ == '__main__':
    create_feather_mask(240, 230, '/tmp/feather_mask_sample.png')
    print("Feather mask script ready.")
