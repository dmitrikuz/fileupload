import io
import os
from uuid import uuid4

import magic
from django.core.files.base import ContentFile
from PIL import Image

from celery import shared_task

from .models import File


@shared_task
def process_file(id) -> bool:

    file = File.objects.get(id=id)
    readable_file = file.file

    root, format = os.path.splitext(readable_file.path)
    old_filename = root + format

    mime_type = magic.from_file(old_filename, mime=True)

    with readable_file.open() as f:
        buffer = io.BytesIO(f.read())

    if mime_type.split("/")[0] == "image":
        with Image.open(old_filename) as img:
            img = img.convert("RGB")
            buffer.truncate(0)
            img.save(buffer, format="JPEG")
            format = ".jpg"

    elif mime_type.split("/")[0] == "text":
        with readable_file.open() as f:
            string = f.read().decode("utf-8")
            buffer.truncate(0)
            buffer.write(string.encode("utf-32"))

    new_filename = str(uuid4()) + format

    with readable_file.open() as rf:
        rf.delete()
        rf.save(new_filename, ContentFile(buffer.getvalue()))
        file.processed = True

    buffer.close()
    file.save()
    return file.processed
