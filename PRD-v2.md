CONTEXT & MISSION:
We are deploying this Flask + SQLite boutique manager app to PythonAnywhere (Free Tier). 
Because PythonAnywhere Free Tier has a strict outbound internet allowlist and wipes temporary folders, we must use a specific architectural stack to keep it 100% free and prevent data loss:
1. DATABASE: Keep SQLite. It must run on PythonAnywhere's local persistent storage using absolute paths. (Do not switch to Turso or Postgres).
2. IMAGES: Must be hosted on ImageKit.io (which is allowlisted by PythonAnywhere). Product image files uploaded by the user must be read as memory bytes and streamed directly to ImageKit via their Python SDK. We CANNOT save files to a local `static/uploads/` folder.
3. SECURITY: Since the app will be live on a public URL, we need a session-based login page instantly injected to secure the dashboard.

YOUR TASKS:

1. UPDATE REQUIREMENTS.txt:
Add `imagekitio==1.0.x` to the dependencies.

2. REFACTOR DATABASE INIT (app.py):
Ensure the SQLite URI uses absolute path mapping so it works seamlessly on PythonAnywhere's server path structure:
```python
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'shop.db')}"
```

3. INTEGRATE IMAGEKIT SDK & REFACTOR CHANNELS:

- Initialize the ImageKit client using environment variables: `IMAGEKIT_PRIVATE_KEY`, `IMAGEKIT_PUBLIC_KEY`, and `IMAGEKIT_URL_ENDPOINT`.
- Update the Product database model: change the image column from a file path to `image_url = db.Column(db.String(500))` to hold the external CDN link directly.
- Rewrite the product upload route: Instead of saving the image locally using `.save()`, use `.read()` to fetch the byte buffer and upload it directly to ImageKit using `imagekit.files.upload()`. Save the returned `.url` to the database.
- Docs: https://imagekit.io/docs/integration/python

4. REFACTOR HTML TEMPLATES:
Scan all HTML templates (like index, dashboard, products). Find where local images are rendered (e.g., `url_for('static', filename='uploads/' + product.image)`) and change them to cleanly print the cloud URL directly: `<img src="{{ product.image_url }}">`.

5. ADD LOGIN GATEWAY:
- Create a secure User model with a hashed password field (`password_hash`).
- Add a Flask `@app.before_request` hook that intercepts all traffic and redirects unauthenticated users to a secure `/login` route, unless they are accessing static assets or the login page itself.
- Build a basic, clean `login.html` form template utilizing standard Bootstrap.

6. PROMPT SEED SCRIPT:
Create a temporary execution script or initialization function that sets up the database (`db.create_all()`) and seeds a default admin user with a securely hashed password using `werkzeug.security.generate_password_hash`.

Execute these refactoring steps now so the codebase is completely ready for a zero-cost PythonAnywhere migration.
