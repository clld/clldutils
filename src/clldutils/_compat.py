import re
import sys
import datetime

if (sys.version_info.major, sys.version_info.minor) >= (3, 11):  # pragma: no cover
    fromisoformat = datetime.datetime.fromisoformat
else:
    def fromisoformat(s: str) -> datetime.datetime:  # pragma: no cover
        s = s.replace('Z', '+00:00')
        s = re.sub(r'\.[0-9]+', '', s)
        return datetime.datetime.fromisoformat(s)
