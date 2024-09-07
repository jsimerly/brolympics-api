# custom_storage.py

import os
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.conf import settings
from firebase_admin import storage
from django.utils.crypto import get_random_string
from urllib.parse import urljoin
from django.conf import settings

@deconstructible
class FirebaseStorage(Storage):
    def __init__(self):
        self.bucket = storage.bucket(settings.FIREBASE_STORAGE_BUCKET)

    def _save(self, name, content):
        name = self.get_valid_name(name)
        blob = self.bucket.blob(name)
        blob.upload_from_file(content, content_type=content.content_type)
        blob.make_public()  
        return name

    def _open(self, name, mode='rb'):
        blob = self.bucket.blob(name)
        return blob.download_as_bytes()

    def delete(self, name):
        self.bucket.blob(name).delete()

    def exists(self, name):
        return self.bucket.blob(name).exists()

    def url(self, name):
        blob = self.bucket.blob(name)
        return blob.public_url

    def get_valid_name(self, name):
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        random_string = get_random_string(7)
        new_name = f"{file_root}_{random_string}{file_ext}"
        return os.path.join(dir_name, new_name)

    def size(self, name):
        return self.bucket.blob(name).size

    def get_modified_time(self, name):
        return self.bucket.blob(name).updated

    def get_available_name(self, name, max_length=None):
        return self.get_valid_name(name)

    def path(self, name):
        return name 