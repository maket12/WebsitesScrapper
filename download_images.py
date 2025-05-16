import asyncio
import os
import mimetypes

from curl_cffi import AsyncSession

IMAGE_SOURCES = [
  "data/iherb/images.txt",
  "data/hnm/images.txt",
  "data/asos/images.txt",
  "data/footlocker/images.txt",
  "data/macys/images.txt",
]
IMAGES_DIR = "data/images"
BATCH_SIZE = 20

# Manual mapping for common types not handled by mimetypes
EXT_MAP = {
  "image/webp": ".webp",
  "image/jpg": ".jpg",
  "image/jpeg": ".jpg",
  "image/png": ".png",
  "image/gif": ".gif",
  "image/bmp": ".bmp",
  "image/svg+xml": ".svg",
  "image/x-icon": ".ico",
  "image/tiff": ".tiff",
}


def load_images_from_files(file_paths):
  images = []
  for file_path in file_paths:
    if not os.path.exists(file_path):
      continue
    with open(file_path, "r") as f:
      for line in f:
        line = line.strip()
        if not line:
          continue
        image_path, image_url = line.split("@", 1)
        images.append((image_path, image_url))
  return images


def ensure_dir_exists(path):
  if not os.path.exists(path):
    os.makedirs(path)


def get_extension_from_url_or_content_type(image_url, content_type=None):
  # Try content_type first
  if content_type:
    ct = content_type.split(";")[0].strip()
    ext = EXT_MAP.get(ct)
    if not ext:
      ext = mimetypes.guess_extension(ct)
    if ext:
      return ext.lstrip(".")
  # Fallback to URL
  ext = image_url.rpartition(".")[-1].split("?")[0].split("#")[0]
  if ext and len(ext) <= 5:
    return ext
  return "jpg"  # default


def gen_image_path(image_path, ext):
  return os.path.join(IMAGES_DIR, f"{image_path}.{ext}")


async def download_task(client, image_url, image_path):
  try:
    resp = await client.get(image_url, impersonate="chrome")
    if resp.status_code == 200:
      ext = get_extension_from_url_or_content_type(
        image_url, resp.headers.get("content-type")
      )
      full_image_path = gen_image_path(image_path, ext)
      ensure_dir_exists(os.path.dirname(full_image_path))
      with open(full_image_path, "wb") as f:
        f.write(resp.content)
      print(f"Downloaded {image_path} at {image_url}")
      return True
    else:
      print(f"Failed to download {image_path} at {image_url}: {resp.status_code}")
      return False
  except Exception as e:
    print(f"Error downloading {image_path} at {image_url}: {e}")
    return False


async def download_images():
  image_tasks = load_images_from_files(IMAGE_SOURCES)
  if not image_tasks:
    print("No images to download")
    return

  ensure_dir_exists(IMAGES_DIR)
  skipped = 0
  success = 0
  failed = 0

  # Filter out already existing images
  download_queue = []
  for image_path, image_url in image_tasks:
    # Use URL extension as a placeholder, will be corrected on download
    ext = get_extension_from_url_or_content_type(image_url)
    full_image_path = gen_image_path(image_path, ext)
    if os.path.exists(full_image_path):
      skipped += 1
      continue
    download_queue.append((image_url, image_path))

  # Batch download with max concurrency
  for i in range(0, len(download_queue), BATCH_SIZE):
    async with AsyncSession(impersonate="chrome") as client:
      batch = download_queue[i : i + BATCH_SIZE]
      tasks = [
        download_task(client, image_url, image_path) for image_url, image_path in batch
      ]
      results = await asyncio.gather(*tasks)
      for result in results:
        if result:
          success += 1
        else:
          failed += 1

  print(f"Downloaded {success} images")
  print(f"Skipped {skipped} images")
  print(f"Failed {failed} images")


if __name__ == "__main__":
  asyncio.run(download_images())
