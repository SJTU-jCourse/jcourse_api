from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from qiniu import Auth, put_data, BucketManager

from jcourse import settings


@deconstructible
class QiniuStorage(Storage):

    def __init__(self, child_name):
        super().__init__()
        self.access_key = settings.QINIU_ACCESS_KEY
        self.secret_key = settings.QINIU_SECRET_KEY
        # 要上传的空间
        self.bucket_name = settings.QINIU_BUCKET_NAME
        self.base_url = settings.QINIU_BASE_URL
        # 构建鉴权对象
        self.auth = Auth(self.access_key, self.secret_key)
        self.child_name = child_name

    def _open(self, name, mode="rb"):
        pass

    def _save(self, name, content):
        token = self.auth.upload_token(self.bucket_name)
        file_data = content.file

        ret, info = put_data(token, self.new_name(name, self.child_name),
                             file_data if isinstance(file_data, bytes) else file_data.read())

        if info.status_code == 200:
            return f"{self.base_url}/{ret.get('key')}"
        else:
            raise Exception("Upload Qiniu Error")

    def exists(self, name):
        return False

    def url(self, name):
        return self.auth.private_download_url(name)

    def delete(self, name):
        bucket = BucketManager(self.auth)
        ret, info = bucket.delete(self.bucket_name, name)
        if ret == {} and info.status_code == 200:
            return True
        else:
            raise Exception(f"Delete {name} Error")

    @staticmethod
    def new_name(name, child_name):
        return f"{child_name}/{name}"
