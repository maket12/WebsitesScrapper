import mimetypes

mimetypes.add_type('image/jpg', '.jpg')
mimetypes.add_type('image/jpeg', '.jpg')
mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/gif', '.gif')
mimetypes.add_type('image/avif', '.avif')
mimetypes.add_type('image/webp', '.webp')
mimetypes.add_type('image/bmp', '.bmp')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('image/x-icon', '.ico')
mimetypes.add_type('image/tiff', '.tiff')


def get_extension_from_mimetype(response):
    content_type = response.headers.get("Content-Type", "")
    ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
    return ext or ".bin"
