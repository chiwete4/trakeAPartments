# Trake Apartments by Orleans

A Django booking website with a blue, white and gold interface, a combined manager/reception dashboard, and an owner reporting dashboard. Booking/payment patterns were reviewed against Five Homes; this smaller app has its own allocation and approval rules.

## Included

- Home, explore, apartment detail, booking, private booking summary.
- Four editable categories: 1 Bed Classic NGN 90,000; 1 Bed Large NGN 105,000; 1 Bed Grand NGN 120,000; 2 Bed Apartment NGN 175,000 per night.
- One **placeholder physical apartment per category**. Add the real units before real bookings. Apartment photos are supplied by the property and lightly polished. Category names, capacities and rates remain provisional.
- Twenty-minute payment holds; automatic confirmation after verified payment when a physical unit is free.
- Conflicting requests enter management review before payment. Approvals recheck availability and cannot overbook. Add available inventory in Django admin or agree alternate dates with the guest and create a new request. Editing stay dates and guest self-service cancellation are outside this first demo.
- Paystack hosted checkout, server verification, signed webhook validation, amount/currency/email/environment checks, fee pass-through support and idempotent fulfilment.
- Late payments that clash go to a paid review state and create an alert. Paid reviews cannot be declined without resolving the payment/refund manually. Automated refunds are not included.
- Owner: verified room sales this month, current occupancy, category sales, current/upcoming stays, alerts.
- Manager: booking search/filter, conflict review and notifications. Owner role can access both dashboards.
- Dashboard alerts persist in the database. Email is optional; console backend is the development default. SMTP configuration is required for actual email delivery. Push/SMS are not included.
- Explicitly labelled simulated checkout for demonstrations without Paystack keys. Never enter card details in this app.

## Windows quick start

Install Python 3.12 or newer, then open PowerShell in this directory:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DEMO_PAYMENTS="true"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Visit http://127.0.0.1:8000. Log in through `/staff/login/` with your superuser to access both dashboards. `/admin/` manages apartment categories, unit inventory and user groups. Give an ordinary staff account the `Owner` or `Manager` group; only admin users need Django's `is_staff` flag. No password is included in this source package.

`.env.example` documents environment variables. This app reads the process environment; it does **not** automatically load a `.env` file. Set variables through PowerShell, your service manager, or the host's environment settings.

## Run tests

```powershell
.\.venv\Scripts\python.exe manage.py collectstatic --no-input
.\.venv\Scripts\python.exe manage.py test
```

Fourteen tests cover date/capacity validation, overlapping and adjacent stays, immutable rate capture, role boundaries, expired holds, mismatched and duplicate payments, provider fees and late payment conflicts. SQLite is for local development. Allocation uses category row locks; use PostgreSQL when hosting. Multi-process PostgreSQL concurrency has not been tested in this environment.

## Hosted demo on Render

1. Upload these source files to `chiwete4/trakeAPartments` (the repository root must contain `manage.py`, `requirements.txt` and `render.yaml`).
2. In Render, create a Blueprint from the repository. `render.yaml` declares a Django web service and PostgreSQL database. Review the host's current plan terms before deploying.
3. Provide `DEMO_OWNER_USERNAME` and a unique `DEMO_OWNER_PASSWORD` of at least 12 characters. The seed command creates that ordinary Owner account once; it does not reset existing passwords. Remove the password environment variable after initial setup if desired.
4. The blueprint enables simulated payments and generates a Django secret. The Render hostname is automatically allowed.
5. Use the assigned HTTPS URL to demo the website and `/staff/login/` for the dashboards.

Hosting is prepared, not deployed by this source package. A Render account connected to the repository is required. Do not rely on ephemeral SQLite on a hosted web service.

## Paystack test integration

Disable `DEMO_PAYMENTS` (`false`), set `PAYSTACK_ENVIRONMENT=test` and add your **test** secret in the host's environment settings as `PAYSTACK_SECRET_KEY`. Do not commit keys or reuse Five Homes credentials. Configure the Paystack test webhook URL to `https://YOUR-HOST/payments/webhook/`. Callback and webhook paths both verify server-side before confirming a booking.

Paystack requests are implemented and covered with local data assertions, but no real provider transaction has been executed without the property's credentials. SMTP delivery is likewise unverified until configured.

## Before live operation

Replace demo inventory/assets/rates, confirm guest capacities and property policies, use PostgreSQL, configure/test Paystack and email, provision real staff accounts, set the domain/allowed hosts and trusted origins, validate concurrent checkout, and agree cancellation/refund handling. Simulated payment records must be cleared from a dedicated demo database before collecting real payments. Public rate limiting and automated refunds are not included in this initial demo.

## October photography and catalogue update

After pulling this update, run `python manage.py migrate` and `python manage.py collectstatic --no-input`. The data migration refreshes the four public categories/rates and photo galleries. Earlier two-bedroom demo categories are retired from new sales rather than deleting their booking history. Existing bookings retain their rate/total snapshots. Unbooked legacy demo units are deactivated; reserved legacy units remain intact.

The main home image is the two-bedroom lounge; the outdoor compound photo has its own arrival section. The extra generically labelled one-bedroom bedroom/lounge photos are displayed only in the overall property section until their precise category is confirmed. Original uploads remain unchanged.

Photo edit brief: modest exposure/shadow and colour correction, restrained clarity/sharpness, preserve the real room layout, furnishings, fixtures and materials. Built-in image editing was used; no virtual staging was requested. WebP versions under `static/images/apartments/` and `static/images/property/` are optimized site assets.

The outdoor compound photo is the homepage hero. Earlier comparison query parameters no longer change the image.
