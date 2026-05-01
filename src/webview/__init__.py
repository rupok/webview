"""WebView — turn your website into a real Android app.

URL in, signed APK/AAB out. Three paths picked automatically:

  - TWA via Bubblewrap          (recommended for PWAs)
  - Kotlin WebView project      (works for any site)
  - GitHub Actions workflow     (no local Android toolchain needed)
"""

from webview.config import AppConfig

__version__ = "2.0.0"
__all__ = ["AppConfig", "__version__"]
