import io
import os
from uuid import uuid4

import magic
from django.core.files.base import ContentFile
from PIL import Image

from celery import shared_task

from .exceptions import ProcessingException
from .models import File


@shared_task
def process_file(id: int) -> bool:

    file = File.objects.get(id=id)
    original_file = file.file
    processed_file = original_file

    root, format = os.path.splitext(original_file.path)
    old_filename = root + format

    try:
        buffer = io.BytesIO()
        mime_type = magic.from_file(old_filename, mime=True)

        if mime_type.split("/")[0] == "image":
            with Image.open(old_filename) as img:
                img = img.convert("RGB")
                img.save(buffer, format="JPEG")
                format = ".jpg"

        elif mime_type.split("/")[0] == "text":
            with original_file.open() as f:
                string = f.read().decode("utf-8")
                buffer.write(string.encode("utf-32"))

        if content := buffer.getvalue():
            processed_file = ContentFile(content)
            original_file.delete()

        new_filename = str(uuid4()) + format

        original_file.save(new_filename, processed_file)

        file.processed = True
        buffer.close()

    except Exception as e:
        raise ProcessingException(e)

    file.save()
    return file.processed
