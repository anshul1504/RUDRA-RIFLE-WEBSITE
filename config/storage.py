from whitenoise.storage import CompressedManifestStaticFilesStorage


class RelaxedManifestStorage(CompressedManifestStaticFilesStorage):
    """Hashed static files, but tolerate references the manifest cannot resolve.

    django-jazzmin's base template asks for the *directory* ``vendor/bootswatch`` via ``{% static %}``;
    the strict manifest storage raises ValueError for that and the whole admin returns HTTP 500.
    """

    manifest_strict = False
