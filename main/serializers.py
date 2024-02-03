from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import File
from .tasks import process_file


class FileSerializer(ModelSerializer):
    class Meta:
        model = File
        fields = ("id", "file", "uploaded_at", "processed")


class UploadFileSerializer(ModelSerializer):
    file = serializers.FileField(max_length=30, allow_empty_file=False)

    class Meta:
        model = File
        fields = ("file", )

    def save(self, **kwargs):
        super().save(**kwargs)
        result = process_file.delay(self.instance.pk)
        result.forget()
