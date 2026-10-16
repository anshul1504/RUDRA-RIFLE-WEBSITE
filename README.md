# Rudra Sports Rifle Shooting Society - Website

Django website for Rudra Sports Rifle Shooting Society, Indore, Madhya Pradesh.
Server-rendered Django templates, Bootstrap 5, vanilla JavaScript, SQLite locally / PostgreSQL in production.

Content source: `Rudra_Sports_Rifle_Shooting_Society_WWW.docx`. Brand asset: `Rudra_Logo-02.pdf`
(converted, uncropped artwork, to `static/images/rudra-logo.svg`; only the empty page margin was trimmed).

## Quick start (Windows PowerShell or any shell)

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
# edit .env: set DJANGO_SECRET_KEY, and DJANGO_DEBUG=True for local work
python manage.py migrate
python manage.py create_staff_groups
python manage.py createsuperuser
python manage.py runserver
```

- Website: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

`migrate` also seeds the four programs (incl. **Pay and Play**), the seven facilities, the About/values/why-choose/focus lists, four gallery categories and DRAFT privacy/terms pages from the supplied document.

## Admin panel (django-jazzmin, branded indigo/gold)

The admin uses the [django-jazzmin](https://github.com/farridav/django-jazzmin) theme (AdminLTE based): grouped sidebar with icons, top menu, quick-search boxes, tabbed edit forms, a custom dashboard (pending bookings, new enquiries, today's slots, quick actions), CSV export actions and a branded login screen. Branding lives in `static/css/admin-brand.css`; menu/icon settings in `JAZZMIN_SETTINGS` in `config/settings.py`.

Compatibility note: Jazzmin 3.0's templates use the `length_is` filter that Django 5.1 removed; `apps/core/templatetags/compat.py` (loaded as a template builtin) provides it, so the admin works on Django 5.2.

## Slot booking (Pay and Play)

1. **Weekly slot schedule**: add a row per weekday/time (e.g. Monday 06:00-07:00, capacity 6), then select the rows and run **Generate slots for the next 14/30 days**. Existing slots are never duplicated.
2. **Slots**: add or edit individual dated slots (capacity, optional price note, notes), close/open them, or see who booked.
3. Visitors use **/book/** to choose a slot and send a booking request (name, mobile, number of shooters). Seats are checked under a database lock so a slot can never be overbooked; cancelled bookings free their seats.
4. **Slot bookings**: bulk **Confirm / Cancel / Mark attended**, export CSV. Each booking gets a reference like `RSB-1A2B3C`.
5. No payment is taken online. Put payment instructions in *Site settings > Slot booking > payment note* and a fee in a slot's *price note* if you want them shown.

## Homepage carousel

Admin > **Homepage carousel**: add, edit, reorder or hide slides (eyebrow, headline + gold part, text, image, two buttons with a link such as `/book/` or `https://...`). Autoplay pauses on hover/focus, has a pause button, prev/next arrows and progress indicators, and does not autoplay for visitors who prefer reduced motion. If no slide is published, the plain hero from *Site settings* is shown.

## Email addresses

Site settings > Contact holds the `info@rudrasports.com` address. **The mailbox must be created with your email host; the website only displays it.** Set `DEFAULT_FROM_EMAIL` and `ENQUIRY_NOTIFY_EMAILS` in `.env` to a real mailbox to receive enquiry notifications.

## Images

All placeholder images (stock photos and illustrations) have been removed. Until the academy's own photographs are uploaded, the site shows its designed fallbacks: the branded target-ring background with the logo plate on the homepage carousel, and ring/icon tiles on program cards. Use `python manage.py load_original_photos` (below) or Admin to add real photographs.

## Environment variables (`.env.example`)

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | **Required.** Never commit it. |
| `DJANGO_DEBUG` | `True` locally, `False` in production (default `False`). |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | e.g. `https://rudrasports.com` |
| `SITE_URL` | Public URL, used for canonical links, sitemap, Open Graph. |
| `DB_ENGINE` | `sqlite` (default) or `postgres` (+ `DB_NAME/USER/PASSWORD/HOST/PORT`; install `psycopg[binary]`). |
| `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_HSTS_SECONDS`, `DJANGO_BEHIND_PROXY` | HTTPS hardening (active when DEBUG is off). |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `ENQUIRY_NOTIFY_EMAILS` | Optional email alerts for new enquiries. |

## Managing content (no code editing)

Log in at `/admin/`. Everything below is edited there.

| Admin section | Controls |
|---|---|
| **Site settings & homepage text** (tabs) | Contact details, hero image + headline + buttons, intro/about/vision/mission/safety/CTA/footer text, slot-booking text, map, social links (a social icon appears only if its URL is filled in). |
| **About / values / safety lists** | Mission points, core values, Why Choose Us items, achievements focus areas (add, edit, reorder, hide). |
| **Slots, Weekly slot schedule, Slot bookings** | See *Slot booking* above. |
| **Programs** | Text, photo, "what's included" bullets. Fees / timings / eligibility / duration are **hidden until you fill them in**. |
| **Facilities** | The facility cards (icon, text, order). |
| **Gallery > Categories / Gallery images** | Upload, categorise, reorder (edit the *Order* column in the list), publish/unpublish, delete. Alt text is required. |
| **Achievements** | Add only verified achievements. They are unpublished by default. |
| **Events** | Dates, location, photos, registration link. Upcoming/past is automatic. |
| **Admission enquiries / Contact messages** | View submissions, set status (New / Contacted / Closed), add private notes. |
| **Legal pages** | Privacy Policy and Terms (draft text, plain text with `## heading` and `- bullet`). Set *Last reviewed* once approved; the draft banner then disappears. |

Uploads must be JPG, PNG or WebP, max 5 MB; the file is checked to be a real image and downscaled to 2000 px.

### Staff roles
`python manage.py create_staff_groups` creates:
- **Content Editors** - programs, gallery, achievements, events, facilities, page text lists, slots and schedules, legal pages, site settings.
- **Enquiry Managers** - view/update admission enquiries, contact messages and slot bookings (no add/delete).

Create a user in Admin > Users, tick *Staff status*, assign a group.

## Static and media files

- Bootstrap 5.3 and Bootstrap Icons are vendored in `static/vendor/` (no CDN dependency). Poppins loads from Google Fonts with a system-font fallback.
- Production: `python manage.py collectstatic` -> `staticfiles/`, served by WhiteNoise (already in middleware).
- Media (`media/`) is user uploads. Django serves it only when `DEBUG=True`; in production serve `MEDIA_URL=/media/` from the web server (nginx `location /media/ { alias /path/to/media/; }`) or switch to object storage.

## Tests

```bash
python manage.py test
python manage.py check
DJANGO_DEBUG=False DJANGO_ALLOWED_HOSTS=example.com python manage.py check --deploy
```

73 tests cover routes, slot booking (capacity, overbooking, duplicates, schedule generation, admin actions), database-driven page text, seeded content, models/slugs, uploads, forms (validation, duplicates, honeypot, throttling, CSRF), notifications, empty states, 404, sitemap/robots and admin permissions.

## Production checklist

- [ ] `DJANGO_DEBUG=False`, a strong unique `DJANGO_SECRET_KEY`, correct `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`, `SITE_URL`.
- [ ] PostgreSQL configured (`DB_ENGINE=postgres`), `psycopg` installed, `migrate` run, regular DB backups.
- [ ] HTTPS enabled; `DJANGO_BEHIND_PROXY=True` only if the proxy sets `X-Forwarded-Proto`.
- [ ] `collectstatic` run; media path served and backed up.
- [ ] Run with gunicorn (`gunicorn config.wsgi`) behind nginx/Apache.
- [ ] Replace the in-memory cache with Redis/Memcached so form throttling is shared across workers.
- [ ] Configure email (`EMAIL_*`, `ENQUIRY_NOTIFY_EMAILS`) and send a test enquiry.
- [ ] Rename or restrict the `/admin/` URL if desired; use strong staff passwords.
- [ ] Legal review of Privacy Policy and Terms.
- [ ] Upload real photos and fill in the items listed below.

## Information still needed from the academy

- **Real photographs** (carousel, programs, gallery, facilities, about) to replace the illustrations.
- Creation of the `info@rudrasports.com` mailbox with your email host.
- Program **fees, batch timings, eligibility, duration** (hidden until supplied), and the real **Pay and Play** rules/rates (the description is minimal placeholder wording; edit it in Admin).
- The weekly **slot timings and capacity**.
- **Verified achievements** (the page currently shows only the document's general statements).
- **Events** (none are listed).
- Exact **Google Maps embed/link** (a search link from the address is used until then).
- WhatsApp number confirmation (currently the same as the phone number; can be changed or blanked).
- Social media URLs, opening hours (hidden until supplied).
- Confirmation that "Certified Coaches" / facility statements may be published, and the final **Privacy Policy and Terms** text.
- The logo: only `Rudra_Logo-02.pdf` was supplied. The artwork has dark-indigo lettering, so on dark backgrounds (footer) it sits on a white plate rather than being recoloured.

## Features and limitations

Implemented: all required routes (home, about, programs + detail, facilities, gallery with filters and lightbox, achievements + detail, events + detail, admission, contact, privacy, terms), custom 404/500, sitemap, robots.txt, canonical/Open Graph tags, accurate Organisation/Event JSON-LD, admin with search/filters/actions, validated forms with honeypot, duplicate and rate limiting, optional email notification.

Limitations: no payment system (not requested); gallery images are not converted to multiple responsive sizes (they are downscaled to 2000 px and lazy-loaded); throttling uses the local cache; the 500 page is static HTML; the Facebook/Instagram etc. links are intentionally absent.

## Using the academy's own photographs

Copy the photos into `original_photos/` (see `original_photos/README.txt` for the file names, e.g. `slide-1.jpg`, `about.jpg`, `beginner.jpg`, `gallery-training-1.jpg`) and run `python manage.py load_original_photos`. They are attached to the carousel, About page, programs and gallery. Alt text/captions can then be refined in Admin.

## Motion and hover effects

Scroll-reveal with stagger, card image zoom, button shine/lift, icon reactions, carousel entrance animation, slow-turning target rings, scroll-progress bar, back-to-top button and a WhatsApp pulse. Everything is switched off automatically for visitors with "reduce motion" enabled, and the site works without JavaScript.

## More admin-managed extras

- **Announcement bar** (Admin > Announcement bar): a gold strip above the header, e.g. "Admissions open", dismissible by the visitor.
- **Testimonials**: nothing is shown until you add real quotes and tick *Published* (off by default).
- **FAQs**: shown on the homepage and the admission page once you add them.
- **Acknowledgement emails**: visitors who give an email address get a short "Namaste ... we received your enquiry/message/booking" email from `DEFAULT_FROM_EMAIL`.

## Photos

The site uses the academy's own photographs (from the shared Drive folder "Rudra Sports Images"), stored processed in `site_photos/`. `python manage.py load_site_photos` puts them in place: an 18-photo gallery (each a different moment; near-duplicates were left out), the homepage carousel, About image, Contact banner and the four program cards. It is safe to re-run (`--refresh` re-saves the files). Titles, captions and alt text can be edited in Admin. The old stock-photo credits page and loader were removed.

## Page switches, pagination and enquiries (latest changes)

- **Page switches** (Admin > Site settings > *Page switches*): turn Achievements, Events, Gallery and Slot booking on or off. A switched-off page returns Not Found; its menu/footer links, homepage section and sitemap entry disappear. Achievements stays on by default; switch it on only when real achievements are ready.
- **Pagination**: Gallery (12 per page, category filter via `?category=`), Events (6 per list; upcoming and past paginate independently), Achievements (9), Programs (6) and Slot booking (7 dates per page).
- **Facilities**: 12 cards (the five added beyond the document's seven come from its training items: safety protocols, aiming and trigger control, mental focus, performance analysis, competition guidance). Edit or hide any in Admin.
- **Contact**: one email (`info@`), banner photo (Site settings > Contact > *Contact image*), call / WhatsApp / email buttons, visit card, directions and map.
- **Admin enquiries**: list shows applicant, guardian, click-to-call/WhatsApp/email, status badge and a date-range filter; the detail page has a Quick contact bar, tabs (Enquiry / Follow-up / Consent) and Contacted / Closed / Reopen actions. The dashboard shows how many enquiries, messages and bookings are new/pending.

## Developer credit

"Designed & Developed by The Webfix" links to https://thewebfix.in. It is fixed in code (`DEVELOPER_CREDIT` in `config/settings.py`, plus `static/js/admin-credit.js` and `JAZZMIN_SETTINGS`) and is deliberately **not** editable from the admin panel. It appears in the website footer, the 500 page, the admin login screen, the admin footer and the admin user menu.

## Client change requests (round 2)

- **Instagram reels**: Admin > Instagram reels. Add the exact reel link (`https://www.instagram.com/reel/XXXXXXXXXXX/`, profile links are rejected) and its cover image. Published reels appear as clickable thumbnails on the Gallery page only (not the homepage), opening that exact reel in a new tab. Nothing is fetched from Instagram, so no tokens or API access are needed; with no published reels the section is hidden.
- **Map**: defaults to the academy location 22.7558407, 75.7659442 (embed + "Open in Google Maps" link, editable in Site settings > Map & social).
- **Program order**: set by each program's *Order* number in Admin (Beginner 0, Junior 1, Advanced Competitive Training 2, Pay and Play 3).
- **Scrolling**: one throttled scroll handler, cached WebP thumbnails for cards/grids (`thumb` template filter, stored under `media/thumbs/`), only the hero rings animate continuously, smooth anchor scrolling only without reduced-motion.
- **Footer colour**: `--footer-bg: #030b17` in `static/css/main.css` covers the whole footer including the copyright strip.
- **Slot booking**: new required fields *Previous Shooting Experience* and *Type of Shooting* (validated server-side, shown in the admin list/detail, filters and CSV export; older bookings keep blank values).
- **Header menu visibility**: Admin > Header menu. Tick/untick each item; hiding never removes a page or its URL. Achievements is hidden by default (also in the footer links and homepage section) and can be switched back on there. Separate from *Site settings > Page switches*, which turn a page off completely (404).

## Deploying on cPanel (Python app)

1. cPanel > *Setup Python App*: create an app (Python 3.10+; this project is tested on 3.11+), app root e.g. `rudra-app`, domain/subdomain as needed, startup file `passenger_wsgi.py`, entry point `application`.
2. Get the code: `git clone https://github.com/anshul1504/RUDRA-RIFLE-WEBSITE.git` into the app root, then `pip install -r requirements.txt` inside the app's virtualenv.
3. Create `.env` in the app root from `.env.example`: a new `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `SITE_URL`, and `MEDIA_ROOT` pointing at a folder inside the site's document root (so Apache serves `/media/` directly).
4. `python manage.py migrate`, `python manage.py collectstatic --noinput`, `python manage.py createsuperuser`, `python manage.py create_staff_groups`.
5. Copy the photos into `site_photos/` and run `python manage.py load_site_photos`.
6. Restart the app (Setup Python App > Restart, or `touch tmp/restart.txt`).
