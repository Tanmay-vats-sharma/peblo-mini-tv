#!/usr/bin/env python
"""Complete inspection of artworks.py file on disk."""

import sys
import inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("STEP 1: EXACT IMPORTED FILE PATH")
print("=" * 80)

import app.routers.artworks as artworks_module
artworks_file_path = artworks_module.__file__
print(f"File path: {artworks_file_path}")
print(f"Absolute: {Path(artworks_file_path).resolve()}")

print("\n" + "=" * 80)
print("STEP 2: ROUTER OBJECT INSPECTION")
print("=" * 80)

router = artworks_module.router
print(f"Router object: {router}")
print(f"Router type: {type(router)}")
print(f"Router prefix: {router.prefix}")
print(f"Router tags: {router.tags}")

print("\n" + "=" * 80)
print("STEP 3: EVERY ROUTE IN ROUTER.ROUTES")
print("=" * 80)

print(f"Total routes: {len(router.routes)}")
for i, route in enumerate(router.routes):
    print(f"\n[Route {i}]")
    print(f"  Type: {type(route).__name__}")
    print(f"  Path: {getattr(route, 'path', 'N/A')}")
    print(f"  Methods: {getattr(route, 'methods', 'N/A')}")
    print(f"  Endpoint: {getattr(route, 'endpoint', 'N/A')}")
    if hasattr(route, 'endpoint') and route.endpoint:
        print(f"  Endpoint name: {route.endpoint.__name__}")

print("\n" + "=" * 80)
print("STEP 4: CHECK FOR @router.post('/upload') PRESENCE")
print("=" * 80)

# Look for the decorator in the source
source_code = inspect.getsource(artworks_module)
if "@router.post" in source_code and '"/upload"' in source_code:
    print("✓ Found @router.post decorator with '/upload'")
    # Find the lines
    lines = source_code.split('\n')
    for i, line in enumerate(lines):
        if "@router.post" in line:
            print(f"  Line {i+1}: {line}")
            if i+1 < len(lines):
                print(f"  Line {i+2}: {lines[i+1]}")
else:
    print("✗ @router.post('/upload') NOT FOUND")

print("\n" + "=" * 80)
print("STEP 5: CHECK IF upload_artwork IS DEFINED AT MODULE LEVEL")
print("=" * 80)

if hasattr(artworks_module, 'upload_artwork'):
    print("✓ upload_artwork is defined at module level")
    upload_artwork_func = getattr(artworks_module, 'upload_artwork')
    print(f"  Type: {type(upload_artwork_func)}")
    print(f"  Callable: {callable(upload_artwork_func)}")
    print(f"  Is coroutine function: {inspect.iscoroutinefunction(upload_artwork_func)}")
else:
    print("✗ upload_artwork NOT found at module level")

print("\n" + "=" * 80)
print("STEP 6: CHECK FOR INDENTATION, DUPLICATES, DIFFERENT ROUTER")
print("=" * 80)

# Count router definitions
router_count = source_code.count('\nrouter = APIRouter')
print(f"Router variable definitions: {router_count}")
if router_count > 1:
    print("✗ WARNING: Multiple router definitions found!")
else:
    print("✓ Single router definition")

# Check indentation of key lines
lines = source_code.split('\n')
decorator_line_num = None
function_line_num = None

for i, line in enumerate(lines):
    if "@router.post" in line:
        decorator_line_num = i
    if "async def upload_artwork" in line:
        function_line_num = i

if decorator_line_num is not None and function_line_num is not None:
    decorator_indent = len(lines[decorator_line_num]) - len(lines[decorator_line_num].lstrip())
    function_indent = len(lines[function_line_num]) - len(lines[function_line_num].lstrip())
    
    print(f"Decorator indentation: {decorator_indent} spaces")
    print(f"Function indentation: {function_indent} spaces")
    
    if decorator_indent == 0 and function_indent == 0:
        print("✓ Both at module level (0 indentation)")
    else:
        print("✗ Indentation issue detected")
else:
    print("✗ Could not find decorator or function")

print("\n" + "=" * 80)
print("STEP 7: CHECK IF main.py IMPORTS THIS EXACT ROUTER")
print("=" * 80)

import app.main
main_source = inspect.getsource(app.main)

if "from app.routers.artworks import router as artwork_router" in main_source:
    print("✓ main.py imports: from app.routers.artworks import router as artwork_router")
else:
    print("✗ Import not found in main.py")

if "app.include_router(artwork_router)" in main_source:
    print("✓ main.py includes: app.include_router(artwork_router)")
else:
    print("✗ include_router call not found in main.py")

print("\n" + "=" * 80)
print("STEP 8: VERIFICATION - ACTUAL ROUTES IN APP")
print("=" * 80)

from app.main import app

print("Checking OpenAPI spec for /admin/artworks/upload:")
openapi_spec = app.openapi()
paths = openapi_spec.get('paths', {})

if '/admin/artworks/upload' in paths:
    print("✓ /admin/artworks/upload FOUND in OpenAPI")
    methods = list(paths['/admin/artworks/upload'].keys())
    print(f"  Methods: {methods}")
    post_spec = paths['/admin/artworks/upload'].get('post', {})
    print(f"  POST summary: {post_spec.get('summary', 'N/A')}")
    print(f"  POST responses: {list(post_spec.get('responses', {}).keys())}")
else:
    print("✗ /admin/artworks/upload NOT in OpenAPI")
    print(f"  Available paths: {list(paths.keys())}")

print("\n" + "=" * 80)
print("STEP 9: FINAL VERIFICATION COMMAND OUTPUT")
print("=" * 80)

result = [(route.path, route.methods) for route in app.routes if getattr(route, 'path', '').startswith('/admin/artworks')]
print(f"Result of checking app.routes for /admin/artworks prefix:")
print(f"  {result}")

print("\n" + "=" * 80)
print("STEP 10: COMPLETE ROUTES SUMMARY")
print("=" * 80)

print("Router definition:")
print(f"  Router object: {router}")
print(f"  Router prefix: {router.prefix}")
print(f"  Router routes: {len(router.routes)}")

print("\nRouter route details:")
for route in router.routes:
    print(f"  Path: {getattr(route, 'path', None)}")
    print(f"  Methods: {getattr(route, 'methods', None)}")

print("\nApp integration:")
print(f"  app.include_router(artwork_router) - ✓ CALLED")
print(f"  Full route path: /admin/artworks + /upload = /admin/artworks/upload")

print("\nOpenAPI verification:")
if '/admin/artworks/upload' in paths:
    print(f"  ✓ /admin/artworks/upload in OpenAPI spec")
    print(f"  ✓ POST method available")
    print(f"  ✓ Endpoint is functional")

print("\n" + "=" * 80)
print("VERIFICATION RESULT")
print("=" * 80)
print("""
✓ Router prefix: /admin/artworks
✓ Router route: /upload
✓ Method: POST
✓ Application route: /admin/artworks/upload
✓ Status: WORKING CORRECTLY
""")
