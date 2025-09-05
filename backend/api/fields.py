from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
	def to_internal_value(self, data):
		from django.core.files.base import ContentFile
		import base64
		import uuid
		if isinstance(data, str) and data.startswith('data:image'):
			header, b64data = data.split(';base64,')
			file_ext = header.split('/')[-1]
			decoded = base64.b64decode(b64data)
			file_name = f"{uuid.uuid4().hex}.{file_ext}"
			return ContentFile(decoded, name=file_name)
		return super().to_internal_value(data)
