"""
Gateway local settings (example)

Copy this file to local_settings.py (same folder) and write the real secret in it.
local_settings.py is not in Git (see .gitignore). Never put the real secret in this example file.
"""

# Secret used to check the signature of the tokens (HS256), at least 32 characters.
# It must be THE SAME value as JWT_SECRET_KEY in the login service's local_settings.py.
JWT_SECRET_KEY = 'replace-me-with-a-secret-of-at-least-32-characters'
