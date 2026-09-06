#!/usr/bin/env python
"""Diagnostic script to check artwork router registration."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("DIAGNOSTIC: Step 1 - Check imports")
print("=" * 80)

try:
    import app.main
    print(f"✓ app.main imported from: {app.main.__file__}")
except Exception as e:
    print(f"✗ Error importing app.main: {e}")
    sys.exit(1)

try:
    import app.routers.artworks as artworks_module
    print(f"✓ app.routers.artworks imported from: {artworks_module.__file__}")
except Exception as e:
    print(f"✗ Error importing app.routers.artworks: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("DIAGNOSTIC: Step 2 - Check router object")
print("=" * 80)

from app.routers.artworks import router as artwork_router
print(f"Router object: {artwork_router}")
print(f"Router prefix: {artwork_router.prefix}")
print(f"Router routes count: {len(artwork_router.routes)}")
print("\nArtwork Router Routes:")
for i, route in enumerate(artwork_router.routes):
    path = getattr(route, 'path', None)
    methods = getattr(route, 'methods', None)
    print(f"  [{i}] path={path}, methods={methods}")

print("\n" + "=" * 80)
print("DIAGNOSTIC: Step 3 - Check FastAPI app routes")
print("=" * 80)

from app.main import app
print(f"App object: {app}")
print(f"Total routes in app: {len(app.routes)}")
print("\nAll App Routes:")
for i, route in enumerate(app.routes):
    path = getattr(route, 'path', None)
    methods = getattr(route, 'methods', None)
    route_type = type(route).__name__
    print(f"  [{i}] type={route_type}, path={path}, methods={methods}")

print("\n" + "=" * 80)
print("DIAGNOSTIC: Step 4 - Check for /admin/artworks routes")
print("=" * 80)

admin_artworks_routes = [
    (getattr(route, 'path', None), getattr(route, 'methods', None))
    for route in app.routes
    if getattr(route, 'path', '').startswith('/admin/artworks')
]

print(f"Routes starting with /admin/artworks: {admin_artworks_routes}")
if not admin_artworks_routes:
    print("✗ NO ROUTES FOUND with /admin/artworks prefix")
else:
    print(f"✓ Found {len(admin_artworks_routes)} route(s)")

print("\n" + "=" * 80)
print("DIAGNOSTIC: Step 5 - Check /storage mount")
print("=" * 80)

storage_routes = [
    (getattr(route, 'path', None), type(route).__name__)
    for route in app.routes
    if getattr(route, 'path', '').startswith('/storage')
]

print(f"Routes starting with /storage: {storage_routes}")

print("\n" + "=" * 80)
print("DIAGNOSTIC: Step 6 - Check artwork models")
print("=" * 80)

from app.models import Artwork, ArtworkType
print(f"ArtworkType enum values: {[e.value for e in ArtworkType]}")
print(f"Artwork model: {Artwork}")
print(f"Artwork.__tablename__: {Artwork.__tablename__}")
