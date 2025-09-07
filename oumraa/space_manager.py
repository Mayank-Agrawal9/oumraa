import uuid
from io import BytesIO
from PIL import Image, ImageOps

import boto3

from oumraa import settings


class DigitalOceanSpacesManager:
    """Digital Ocean Spaces image management with CDN"""

    def __init__(self):
        # DigitalOcean Spaces uses S3-compatible API
        self.client = boto3.client(
            's3',
            endpoint_url=settings.DO_SPACES_ENDPOINT_URL,  # https://fra1.digitaloceanspaces.com
            aws_access_key_id=settings.DO_SPACES_KEY,
            aws_secret_access_key=settings.DO_SPACES_SECRET,
            region_name=settings.DO_SPACES_REGION
        )
        self.bucket_name = settings.DO_SPACES_BUCKET
        self.cdn_url = settings.DO_SPACES_CDN_URL  # https://your-space.fra1.cdn.digitaloceanspaces.com

    def process_and_upload_image(self, image_file, folder="products"):
        """Process image and upload multiple sizes to DO Spaces"""
        try:
            # Open and process image
            img = Image.open(image_file)
            img = ImageOps.exif_transpose(img)  # Fix rotation issues

            # Convert to RGB if needed (for JPEG)
            if img.mode in ('RGBA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            file_id = str(uuid.uuid4())
            base_path = f"{folder}/{file_id}"

            sizes = {
                'thumbnail': (300, 300, 75),    # Small thumbnails - lower quality
                'medium': (600, 600, 85),       # Product cards - good quality
                'large': (1200, 1200, 90),     # Product detail - high quality
                'original': (*img.size, 95)     # Full size - highest quality
            }

            upload_results = {}
            original_size = img.size

            for size_name, (width, height, quality) in sizes.items():
                if size_name == 'original':
                    processed_img = img.copy()
                else:
                    processed_img = img.copy()
                    processed_img.thumbnail((width, height), Image.Resampling.LANCZOS)

                img_bytes = BytesIO()
                processed_img.save(
                    img_bytes,
                    format='JPEG',
                    quality=quality,
                    optimize=True,
                    progressive=True
                )
                img_bytes.seek(0)

                spaces_key = f"{base_path}_{size_name}.jpg"

                self.client.upload_fileobj(
                    img_bytes,
                    self.bucket_name,
                    spaces_key,
                    ExtraArgs={
                        'ACL': 'public-read',
                        'ContentType': 'image/jpeg',
                        'CacheControl': 'max-age=31536000, public',
                        'Metadata': {
                            'original-name': image_file.name,
                            'size-variant': size_name,
                            'width': str(processed_img.width),
                            'height': str(processed_img.height),
                            'file-id': file_id
                        }
                    }
                )

                # Generate URLs
                upload_results[f'{size_name}_key'] = spaces_key
                upload_results[f'{size_name}_url'] = f"{self.cdn_url}/{spaces_key}"
                upload_results[f'{size_name}_size'] = processed_img.size

            return {
                'success': True,
                'file_id': file_id,
                'original_filename': image_file.name,
                'original_size': original_size,
                'results': upload_results
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Upload failed: {str(e)}"
            }

    def delete_image_variants(self, keys_list):
        """Delete all size variants of an image"""
        try:
            if not keys_list:
                return True

            # Delete objects in batch
            delete_objects = [{'Key': key} for key in keys_list if key]

            if delete_objects:
                self.client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': delete_objects}
                )
            return True

        except Exception as e:
            print(f"Error deleting from DO Spaces: {e}")
            return False

    def get_signed_upload_url(self, key, expires_in=3600):
        """Generate signed URL for direct uploads (advanced feature)"""
        try:
            url = self.client.generate_presigned_url(
                'put_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            return None