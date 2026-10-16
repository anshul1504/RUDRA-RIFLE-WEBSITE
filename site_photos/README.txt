The academy's photographs live here (18 JPEGs, named as listed in apps/core/management/commands/load_site_photos.py).
They are NOT stored in git because several show school children. Copy them onto the server (SFTP / cPanel File Manager)
into this folder, then run:  python manage.py load_site_photos
