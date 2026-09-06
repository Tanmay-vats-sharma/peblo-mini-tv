#!/usr/bin/env python
"""Deep diagnostic of _IncludedRouter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.main import app

print("=" * 80)
print("DIAGNOSTIC: Inspect _IncludedRouter in detail")
print("=" * 80)

for i, route in enumerate(app.routes):
    if type(route).__name__ == '_IncludedRouter':
        print(f"\n_IncludedRouter found at index {i}")
        print(f"  Object: {route}")
        
        # Try to access routes if available
        if hasattr(route, 'routes'):
            print(f"  Has 'routes' attribute with {len(route.routes)} route(s):")
            for j, subroute in enumerate(route.routes):
                path = getattr(subroute, 'path', None)
                methods = getattr(subroute, 'methods', None)
                print(f"    [{j}] path={path}, methods={methods}")
        
        if hasattr(route, 'path_regex'):
            print(f"  Has 'path_regex': {route.path_regex}")
        
        if hasattr(route, 'app'):
            print(f"  Has 'app': {route.app}")
            # Try to get routes from the app
            if hasattr(route.app, 'routes'):
                print(f"    app.routes has {len(route.app.routes)} route(s):")
                for j, subroute in enumerate(route.app.routes):
                    path = getattr(subroute, 'path', None)
                    methods = getattr(subroute, 'methods', None)
                    print(f"      [{j}] path={path}, methods={methods}")

print("\n" + "=" * 80)
print("DIAGNOSTIC: OpenAPI paths")
print("=" * 80)

openapi_spec = app.openapi()
if openapi_spec:
    print(f"OpenAPI has {len(openapi_spec.get('paths', {}))} paths:")
    for path in sorted(openapi_spec.get('paths', {})):
        methods = list(openapi_spec['paths'][path].keys())
        print(f"  {path}: {methods}")
else:
    print("No OpenAPI spec generated")

print("\n" + "=" * 80)
print("DIAGNOSTIC: Check if /admin/artworks/upload exists")
print("=" * 80)

paths = openapi_spec.get('paths', {}) if openapi_spec else {}
target_path = '/admin/artworks/upload'
if target_path in paths:
    print(f"✓ {target_path} FOUND in OpenAPI spec")
    print(f"  Methods: {list(paths[target_path].keys())}")
else:
    print(f"✗ {target_path} NOT FOUND in OpenAPI spec")
    print(f"  Available /admin paths:")
    for p in paths:
        if p.startswith('/admin'):
            print(f"    {p}")
