from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


def compress_image_file(image_file, quality=30):
    img = Image.open(image_file)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    buffer = BytesIO()
    img.save(buffer, format='JPEG', optimize=True, quality=quality)
    name = image_file.name.rsplit('.', 1)[0] + '.jpg'
    return ContentFile(buffer.getvalue(), name=name)



