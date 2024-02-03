from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import File
from .serializers import FileSerializer, UploadFileSerializer


class FileViewSet(ModelViewSet):
    serializer_class = FileSerializer
    queryset = File.objects.all()

    def create(self, request: Request, *args, **kwargs):
        request_serializer = UploadFileSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        request_serializer.save()

        response_serializer = FileSerializer(request_serializer.instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.order_by("uploaded_at")
        return super().get_queryset()
