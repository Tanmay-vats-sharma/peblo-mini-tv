#!/usr/bin/env python
"""Deep diagnostic of _IncludedRouter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.main import app

print("=" * 80)
print("DIAGNOSTIC: Inspect _IncludedRouter")
print("=" * 80)

for i, route in enumerate(app.routes):
    if type(route).__name__ == '_IncludedRouter':
        print(f"\n_IncludedRouter found at index {i}")
        print(f"  Object: {route}")
        print(f"  Dir attributes:")
        for attr in dir(route):
            if not attr.startswith('_'):
                try:
                    val = getattr(route, attr)
                    if not callable(val):
                        print(f"    {attr}: {val}")
                except:
                    pass
        
        # Try to access routes if available
        if hasattr(route, 'routes'):
            print(f"\n  Routes in _IncludedRouter:")
            for j, subroute in enumerate(route.routes):
                path = getattr(subroute, 'path', None)
                methods = getattr(subroute, 'methods', None)
                print(f"    [{j}] path={path}, methods={methods}")

print("\n" + "=" * 80)
print("DIAGNOSTIC: Try to get OpenAPI spec")
print("=" * 80)

# The OpenAPI spec should show all routes
openapi_spec = app.openapi()
if openapi_spec:
    print(f"OpenAPI spec has paths:")
    for path in openapi_spec.get('paths', {}):
        methods = list(openapi_spec['paths'][path].keys())
        print(f"  {path}: {methods}")
else:
    print("No OpenAPI spec")

print("\n" + "=" * 80)
print("DIAGNOSTIC: Try the actual endpoint URL")
print("=" * 80)

from fastapi.testclient import TestClient

client = TestClient(app)

try:
    # Try to POST to the endpoint
    response = client.post(
        "/admin/artworks/upload",
        data={"show_id": "1", "artwork_type": "poster"},
        files={"file": ("test.png", b"fake png data")}
    )
    print(f"POST /admin/artworks/upload: Status={response.status_code}")
    if response.status_code != 404:
        print("✓ Endpoint is registered!")
    else:
        print("✗ Endpoint returned 404 - not found")
except Exception as e:
    print(f"✗ Error testing endpoint: {e}")
