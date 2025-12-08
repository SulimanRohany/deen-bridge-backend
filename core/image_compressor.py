"""
Image compression utility for Django.
Provides configurable image compression with smart format detection,
resizing, and error handling.
"""
import logging
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings

logger = logging.getLogger(__name__)


def compress_image_file(
    image_file,
    quality=None,
    max_width=None,
    max_height=None,
    format='AUTO',
    preserve_transparency=True
):
    """
    Compress and optimize an image file.
    
    Args:
        image_file: Django uploaded file or file-like object
        quality: JPEG/WebP quality (1-100). Defaults to settings.IMAGE_COMPRESSION_QUALITY
        max_width: Maximum width in pixels. Defaults to settings.IMAGE_COMPRESSION_MAX_WIDTH
        max_height: Maximum height in pixels. Defaults to settings.IMAGE_COMPRESSION_MAX_HEIGHT
        format: Output format ('AUTO', 'JPEG', 'PNG', 'WEBP'). Defaults to 'AUTO'
        preserve_transparency: Whether to preserve transparency. Defaults to True
    
    Returns:
        ContentFile: Compressed image as Django ContentFile
    
    Raises:
        ValueError: If image cannot be processed
    """
    try:
        # Get default values from settings if not provided
        quality = quality or getattr(settings, 'IMAGE_COMPRESSION_QUALITY', 75)
        max_width = max_width or getattr(settings, 'IMAGE_COMPRESSION_MAX_WIDTH', 1920)
        max_height = max_height or getattr(settings, 'IMAGE_COMPRESSION_MAX_HEIGHT', 1920)
        format = format or getattr(settings, 'IMAGE_COMPRESSION_FORMAT', 'AUTO')
        preserve_transparency = preserve_transparency if preserve_transparency is not None else getattr(
            settings, 'IMAGE_COMPRESSION_PRESERVE_TRANSPARENCY', True
        )
        
        # Open and process image
        img = Image.open(image_file)
        
        # Handle EXIF orientation
        try:
            img = ImageOps.exif_transpose(img)
        except (AttributeError, TypeError, KeyError):
            # EXIF data may not exist or be invalid, continue without rotation
            pass
        
        # Get original dimensions
        original_width, original_height = img.size
        original_format = img.format or 'JPEG'
        original_mode = img.mode
        
        # Determine if image has transparency
        has_transparency = original_mode in ('RGBA', 'LA', 'P') and preserve_transparency
        
        # Determine output format
        output_format = _determine_output_format(
            format, original_format, has_transparency, preserve_transparency
        )
        
        # Resize if necessary
        if original_width > max_width or original_height > max_height:
            img = _resize_image(img, max_width, max_height)
            logger.info(
                f"Image resized from {original_width}x{original_height} to {img.size[0]}x{img.size[1]}"
            )
        
        # Convert color mode if necessary
        img = _convert_color_mode(img, output_format, has_transparency)
        
        # Get quality settings based on format
        quality_settings = _get_quality_settings(output_format, quality)
        
        # Compress and save
        buffer = BytesIO()
        save_kwargs = {
            'format': output_format,
            'optimize': True,
            **quality_settings
        }
        
        img.save(buffer, **save_kwargs)
        
        # Generate output filename
        output_filename = _generate_filename(image_file.name, output_format)
        
        # Create ContentFile
        compressed_file = ContentFile(buffer.getvalue(), name=output_filename)
        
        logger.info(
            f"Image compressed: {original_format} -> {output_format}, "
            f"Size: {original_width}x{original_height}, Quality: {quality}"
        )
        
        return compressed_file
        
    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}", exc_info=True)
        # Fallback: return original file if compression fails
        # Reset file pointer if it's a file-like object
        if hasattr(image_file, 'seek'):
            try:
                image_file.seek(0)
            except (AttributeError, IOError):
                pass
        return image_file


def _determine_output_format(format_preference, original_format, has_transparency, preserve_transparency):
    """
    Determine the best output format based on preferences and image characteristics.
    
    Args:
        format_preference: User preference ('AUTO', 'JPEG', 'PNG', 'WEBP')
        original_format: Original image format
        has_transparency: Whether image has transparency
        preserve_transparency: Whether to preserve transparency
    
    Returns:
        str: Output format ('JPEG', 'PNG', 'WEBP')
    """
    if format_preference != 'AUTO':
        # User specified format
        if format_preference.upper() == 'JPEG':
            return 'JPEG'
        elif format_preference.upper() == 'PNG':
            return 'PNG'
        elif format_preference.upper() == 'WEBP':
            return 'WEBP'
    
    # Auto-detect best format
    if has_transparency and preserve_transparency:
        # Preserve transparency with PNG or WebP
        try:
            # Test if WebP is supported
            test_img = Image.new('RGBA', (1, 1))
            test_buffer = BytesIO()
            test_img.save(test_buffer, format='WEBP')
            return 'WEBP'  # WebP supports transparency and is smaller
        except Exception:
            return 'PNG'  # Fallback to PNG
    
    # For images without transparency, prefer WebP if available, else JPEG
    try:
        test_img = Image.new('RGB', (1, 1))
        test_buffer = BytesIO()
        test_img.save(test_buffer, format='WEBP')
        return 'WEBP'
    except Exception:
        return 'JPEG'


def _resize_image(img, max_width, max_height):
    """
    Resize image maintaining aspect ratio.
    
    Args:
        img: PIL Image object
        max_width: Maximum width
        max_height: Maximum height
    
    Returns:
        PIL Image: Resized image
    """
    original_width, original_height = img.size
    
    # Calculate new dimensions maintaining aspect ratio
    ratio = min(max_width / original_width, max_height / original_height)
    
    # Only resize if image is larger than max dimensions
    if ratio < 1.0:
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        # Use high-quality resampling
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return img


def _convert_color_mode(img, output_format, has_transparency):
    """
    Convert image color mode based on output format.
    
    Args:
        img: PIL Image object
        output_format: Target format ('JPEG', 'PNG', 'WEBP')
        has_transparency: Whether original image has transparency
    
    Returns:
        PIL Image: Converted image
    """
    current_mode = img.mode
    
    if output_format == 'JPEG':
        # JPEG doesn't support transparency, convert to RGB
        if current_mode in ('RGBA', 'LA', 'P'):
            # Convert palette or grayscale with alpha to RGB
            if current_mode == 'P':
                img = img.convert('RGBA')
            # Create white background for transparency
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                else:
                    background.paste(img, mask=img.split()[1])  # Use alpha channel as mask
                img = background
            else:
                img = img.convert('RGB')
        elif current_mode not in ('RGB', 'L'):
            img = img.convert('RGB')
    
    elif output_format in ('PNG', 'WEBP'):
        # PNG and WebP support transparency
        if current_mode == 'P' and has_transparency:
            # Convert palette with transparency to RGBA
            img = img.convert('RGBA')
        elif current_mode == 'LA':
            # Convert grayscale with alpha to RGBA
            img = img.convert('RGBA')
        elif current_mode not in ('RGB', 'RGBA', 'L'):
            # Convert other modes appropriately
            if has_transparency:
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
    
    return img


def _get_quality_settings(output_format, quality):
    """
    Get quality settings dictionary for image save operation.
    
    Args:
        output_format: Output format ('JPEG', 'PNG', 'WEBP')
        quality: Base quality value (1-100)
    
    Returns:
        dict: Quality settings for PIL save operation
    """
    settings_dict = {}
    
    if output_format == 'JPEG':
        # JPEG quality (1-100, higher is better)
        quality_jpeg = getattr(settings, 'IMAGE_COMPRESSION_QUALITY', quality)
        settings_dict['quality'] = max(1, min(100, quality_jpeg))
    
    elif output_format == 'PNG':
        # PNG compression level (0-9, higher is more compressed)
        # Convert quality (1-100) to compression level (0-9)
        quality_png = getattr(settings, 'IMAGE_COMPRESSION_QUALITY_PNG', quality)
        compression_level = int(9 - (quality_png / 100) * 9)
        settings_dict['compress_level'] = max(0, min(9, compression_level))
        # PNG optimize flag
        settings_dict['optimize'] = True
    
    elif output_format == 'WEBP':
        # WebP quality (0-100, higher is better)
        quality_webp = getattr(settings, 'IMAGE_COMPRESSION_QUALITY_WEBP', quality)
        settings_dict['quality'] = max(1, min(100, quality_webp))
        settings_dict['method'] = 6  # Higher method = better compression but slower
    
    return settings_dict


def _generate_filename(original_filename, output_format):
    """
    Generate output filename based on original filename and output format.
    
    Args:
        original_filename: Original filename
        output_format: Output format ('JPEG', 'PNG', 'WEBP')
    
    Returns:
        str: New filename with appropriate extension
    """
    # Get extension for format
    format_extensions = {
        'JPEG': '.jpg',
        'PNG': '.png',
        'WEBP': '.webp'
    }
    
    extension = format_extensions.get(output_format, '.jpg')
    
    # Remove original extension and add new one
    if '.' in original_filename:
        name = original_filename.rsplit('.', 1)[0]
    else:
        name = original_filename
    
    return f"{name}{extension}"
