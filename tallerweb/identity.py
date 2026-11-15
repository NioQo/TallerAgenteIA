"""Single source of truth for the workshop identity (web and PDF).

To change any detail, or to replace the text logo with a real file, edit only
this module.
"""

NAME = "FT MOTORS"
TAGLINE = "Tu vehículo en manos expertas"
PHONE = "+54 9 11 5429 6017"
ADDRESS = "Av. Dardo Rocha 1891 (Ruta 25), Pilar, Buenos Aires"

# Text logo used while no real file exists. To use a real logo, set
# LOGO_STATIC_PATH to a path under static/ (SVG or transparent PNG), e.g.
# "tallerweb/logo-ft-motors.svg"; the web then shows it instead of the text.
LOGO_TEXT = NAME
LOGO_STATIC_PATH = ""

IDENTITY = {
    "name": NAME,
    "tagline": TAGLINE,
    "phone": PHONE,
    "address": ADDRESS,
    "logo_text": LOGO_TEXT,
    "logo_static_path": LOGO_STATIC_PATH,
}


def identity(request=None):
    """Template context processor exposing the identity as ``workshop``."""
    return {"workshop": IDENTITY}
