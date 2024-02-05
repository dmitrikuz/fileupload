from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from .models import File
from .tasks import process_file


class FileSerializer(ModelSerializer):
    class Meta:
        model = File
        fields = ("id", "file", "uploaded_at", "processed")


class UploadFileSerializer(ModelSerializer):
    file = serializers.FileField(max_length=100, allow_empty_file=False)

    class Meta:
        model = File
        fields = ("file", )

    def save(self, **kwargs):
        super().save(**kwargs)
        result = process_file.delay(self.instance.pk)
        result.forget()

    def validate_file(self, value):
        if value.size > 100 * 1024 * 1024:
            raise ValidationError(
                detail="File is too large",
                code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        return value
