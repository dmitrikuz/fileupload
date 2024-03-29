import re

import charset_normalizer
import magic
import pytest
from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse

from main.exceptions import ProcessingException
from main.models import File
from main.tasks import process_file

TEST_DATA_DIR = settings.BASE_DIR / "main/test_data"
UUID_REGEX = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}\\..*$"


@pytest.mark.django_db
def test_files_list_endpoint(client: Client):
    url = reverse("list")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_upload_file_endpoint(client: Client):
    url = reverse("upload")
    test_filename = "text.txt"
    test_path = TEST_DATA_DIR / test_filename

    with open(test_path) as file:
        response = client.post(url, data={"file": file})

    File.objects.get(id=response.json()["id"]).file.delete()

    assert response.status_code == 201


@override_settings(CELERY_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_process_image_file_task():
    test_filename = "image.png"
    test_path = TEST_DATA_DIR / test_filename
    file = File.objects.create()

    with open(test_path, "rb") as test_file:
        file.file.save(test_filename, test_file)

    result = process_file.apply((file.pk, ))
    processed_file = File.objects.get(id=file.pk).file
    mime_type = magic.from_file(processed_file.path, mime=True)
    match = re.fullmatch(UUID_REGEX, processed_file.name)
    processed_file.delete()

    assert result.get() is True
    assert result.successful() is True
    assert match is not None
    assert mime_type == "image/jpeg"


@override_settings(CELERY_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_process_text_file_task():
    test_filename = "text.txt"
    test_path = TEST_DATA_DIR / test_filename
    file = File.objects.create()
    guess = None

    with open(test_path) as test_file:
        file.file.save(test_filename, test_file)

    result = process_file.apply((file.pk, ))
    processed_file = File.objects.get(id=file.pk).file

    match = re.fullmatch(UUID_REGEX, processed_file.name)

    with processed_file.open() as data:
        guess = charset_normalizer.detect(data.read(10000))
        guessed_encoding = guess["encoding"]

    processed_file.delete()

    assert result.get() is True
    assert result.successful() is True
    assert match is not None
    assert guessed_encoding.lower() == "utf-32"


@override_settings(CELERY_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_process_text_file_task_failure():
    test_filename = "text_bad.txt"
    test_path = TEST_DATA_DIR / test_filename
    file = File.objects.create()

    with open(test_path, "rb") as test_file:
        file.file.save(test_filename, test_file)

    result = process_file.apply((file.pk, ))
    processed_file = File.objects.get(id=file.pk).file
    processed_file.delete()

    assert isinstance(result.result, ProcessingException)
    assert result.successful() is False
