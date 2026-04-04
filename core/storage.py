"""
Storage abstraction layer.

Supports three modes selected automatically from environment variables:
  - Local disk (dev)  : USE_S3=False  → reads/writes to local filesystem
  - AWS S3            : S3_BUCKET_NAME set, STORAGE_ENDPOINT_URL blank
  - Cloudflare R2     : S3_BUCKET_NAME + STORAGE_ENDPOINT_URL + STORAGE_PUBLIC_URL set
                        (R2 is S3-compatible; boto3 just needs an endpoint_url)
"""
import os
import io

import config

_s3_client = None


def _client():
    global _s3_client
    if _s3_client is None:
        import boto3
        kwargs = dict(
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION,
        )
        if config.STORAGE_ENDPOINT_URL:
            # Cloudflare R2 (or any S3-compatible provider)
            kwargs['endpoint_url'] = config.STORAGE_ENDPOINT_URL
        _s3_client = boto3.client('s3', **kwargs)
    return _s3_client


def get_url(s3_key: str) -> str:
    """Return the public URL for a stored object (no API call)."""
    if not config.USE_S3:
        return '/' + s3_key
    if config.STORAGE_PUBLIC_URL:
        # R2 public bucket URL or custom domain
        return f'{config.STORAGE_PUBLIC_URL}/{s3_key}'
    # Default AWS S3 URL
    return f'https://{config.S3_BUCKET_NAME}.s3.{config.AWS_REGION}.amazonaws.com/{s3_key}'


def _extra_args():
    """ACL is not supported by R2; only pass it for plain AWS S3."""
    if config.STORAGE_ENDPOINT_URL:
        return {}
    return {'ACL': 'public-read'}


def upload_file(local_path: str, s3_key: str) -> str:
    """Upload a file from disk. Returns the public URL."""
    if not config.USE_S3:
        dest = os.path.join(config.BASE_DIR, s3_key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        import shutil
        shutil.copy2(local_path, dest)
        return get_url(s3_key)
    extra = _extra_args()
    _client().upload_file(local_path, config.S3_BUCKET_NAME, s3_key,
                          ExtraArgs=extra if extra else None)
    return get_url(s3_key)


def upload_bytes(data: bytes, s3_key: str, content_type: str = 'application/octet-stream') -> str:
    """Upload raw bytes. Returns the public URL."""
    if not config.USE_S3:
        dest = os.path.join(config.BASE_DIR, s3_key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(data)
        return get_url(s3_key)
    kwargs = dict(Bucket=config.S3_BUCKET_NAME, Key=s3_key, Body=data, ContentType=content_type)
    kwargs.update(_extra_args())
    _client().put_object(**kwargs)
    return get_url(s3_key)


def get_bytes(s3_key: str) -> bytes:
    """Download an S3 object and return its contents as bytes."""
    if not config.USE_S3:
        local_path = os.path.join(config.BASE_DIR, s3_key)
        with open(local_path, 'rb') as f:
            return f.read()
    resp = _client().get_object(Bucket=config.S3_BUCKET_NAME, Key=s3_key)
    return resp['Body'].read()


def list_files(prefix: str) -> list:
    """
    Return [{'filename': str, 'url': str}, ...] for all image objects under prefix.
    prefix should end with '/' e.g. 'backgrounds/'.
    """
    if not config.USE_S3:
        local_dir = os.path.join(config.BASE_DIR, prefix.rstrip('/'))
        if not os.path.isdir(local_dir):
            return []
        results = []
        for fname in os.listdir(local_dir):
            ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
            if ext in config.ALLOWED_IMAGE_EXTENSIONS:
                results.append({'filename': fname, 'url': get_url(prefix + fname)})
        return results

    paginator = _client().get_paginator('list_objects_v2')
    results = []
    for page in paginator.paginate(Bucket=config.S3_BUCKET_NAME, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            fname = key[len(prefix):]
            if not fname:
                continue
            ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
            if ext in config.ALLOWED_IMAGE_EXTENSIONS:
                results.append({'filename': fname, 'url': get_url(key)})
    return results


def delete_file(s3_key: str) -> None:
    """Delete an object from S3 (or local disk in dev mode)."""
    if not config.USE_S3:
        local_path = os.path.join(config.BASE_DIR, s3_key)
        if os.path.exists(local_path):
            os.remove(local_path)
        return
    _client().delete_object(Bucket=config.S3_BUCKET_NAME, Key=s3_key)
