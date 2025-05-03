import asyncio
import json
import os

from curl_cffi import AsyncSession

def load_images_from_file(file_path, images):
  if not os.path.exists(file_path):
    return

  with open(file_path, "r") as f:
    lines = f.readlines()

  for line in lines:
    line = line.strip()
    if not line:
      continue
    image_path, image_url = line.split("@", 1)
    images.append((image_path, image_url))

async def download_images():
  image_tasks = []
  load_images_from_file("data/iherb/images.txt", image_tasks)
  load_images_from_file("data/hnm/images.txt", image_tasks)
  load_images_from_file("data/asos/images.txt", image_tasks)
  load_images_from_file("data/footlocker/images.txt", image_tasks)
  load_images_from_file("data/macys/images.txt", image_tasks)
  
  if not image_tasks:
    print("No images to download")
    return
  
  if not os.path.exists("data/images"):
    os.makedirs("data/images")

  async with AsyncSession() as client:
    download_tasks = []
    skipped = 0
    success = 0
    failed = 0
    for image_path, image_url in image_tasks:
      full_image_path = gen_image_path(image_url, image_path)
      if os.path.exists(full_image_path):
        skipped += 1
        continue
      image_folder = os.path.dirname(full_image_path)
      if not os.path.exists(image_folder):
        os.makedirs(image_folder)
      download_tasks.append(
        download_task(client, image_url, image_path, full_image_path)
      )

    results = await asyncio.gather(*download_tasks)
    for result in results:
      if result:
        success += 1
      else:
        failed += 1

    print(f"Downloaded {success} images")
    print(f"Skipped {skipped} images")
    print(f"Failed {failed} images")


async def download_task(client, image_url, image_path, full_image_path):
  resp = await client.get(image_url, impersonate="chrome")
  if resp.status_code == 200:
    with open(full_image_path, "wb") as f:
      f.write(resp.content)
    print(f"Downloaded {image_path} at {image_url}")
    return True
  else:
    print(f"Failed to download {image_path} at {image_url}: {resp.status_code}")
    return False


def gen_image_path(image_url, image_path):
  full_image_path = (
    os.path.join("data/images", image_path) + "." + image_url.rpartition(".")[-1]
  )
  return full_image_path


if __name__ == "__main__":
  asyncio.run(download_images())
