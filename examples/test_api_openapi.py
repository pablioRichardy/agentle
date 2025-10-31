"""
Test OpenAPI spec loading with function name validation.

This example demonstrates loading an API from an OpenAPI spec
and verifying that all generated function names are valid.
"""

import asyncio
import re

from agentle.agents.apis.api import API

# Pattern from Google's adapter - function names must match this
FUNCTION_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_\.\-]*$")


async def test_openapi_function_names():
    """Test that OpenAPI spec loading generates valid function names."""
    print("\n🧪 Testing OpenAPI Spec Function Name Generation")
    print("=" * 70)

    try:
        # Load PetStore API spec
        print("\n📥 Loading PetStore OpenAPI spec...")
        api = await API.from_openapi_spec(
            "https://petstore3.swagger.io/api/v3/openapi.json",
            name="PetStore",
        )

        print(f"✅ Loaded API: {api.name}")
        print(f"   Base URL: {api.base_url}")
        print(f"   Total Endpoints: {len(api.endpoints)}")

        # Validate all endpoint names
        print("\n🔍 Validating function names...")
        invalid_names = []
        
        for endpoint in api.endpoints:
            if not FUNCTION_NAME_PATTERN.match(endpoint.name):
                invalid_names.append(endpoint.name)
                print(f"   ❌ INVALID: {endpoint.name}")
            else:
                print(f"   ✓ {endpoint.name}")

        if invalid_names:
            print(f"\n❌ Found {len(invalid_names)} invalid function names!")
            print("Invalid names:", invalid_names)
            return False
        else:
            print(f"\n✅ All {len(api.endpoints)} function names are valid!")
            return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_edge_case_paths():
    """Test OpenAPI spec with edge case paths."""
    print("\n🧪 Testing Edge Case Path Patterns")
    print("=" * 70)

    # Create a mock OpenAPI spec with edge cases
    mock_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Edge Case API", "version": "1.0.0"},
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/123-resource": {
                "get": {
                    "operationId": None,  # Force auto-generation
                    "summary": "Get resource starting with number",
                }
            },
            "/api/v2/users": {
                "get": {
                    "operationId": None,
                    "summary": "Get users",
                }
            },
            "/user-profile": {
                "get": {
                    "operationId": None,
                    "summary": "Get user profile",
                }
            },
            "/": {
                "get": {
                    "operationId": None,
                    "summary": "Root endpoint",
                }
            },
        },
    }

    # Remove None operationIds (they should be missing, not None)
    for path_item in mock_spec["paths"].values():
        for operation in path_item.values():
            if "operationId" in operation and operation["operationId"] is None:
                del operation["operationId"]

    try:
        api = await API.from_openapi_spec(mock_spec, name="EdgeCaseAPI")

        print(f)
o.run(main()
    asyncimain__":me__ == "__
if __na70)

=" * rint("
    p")s failed!sttet("❌ Some   prin         else:
assed!")
 tests p"✅ All    print(t2:
     resullt1 and     if resu"=" * 70)
\n" +    print("
 aths()
se_ptest_edge_cait  = awat2esul
    rEdge cases: Test 2# )

    mes(_napi_functiont_openait tes1 = awasult  re  c
API speal Openst 1: Re
    # Te0)
"=" * 7print(s")
     Testtionme Valida Na Functionint("API)
    pr" * 70"=("\n" +  print."""
   estsl t""Run al
    " def main():


asyncturn False        rec()
_ex.printtraceback       back
 race import t     {e}")
   Error: rint(f"\n❌
        p:s e at Exception
    excepll_valid
 return a      )

 d!"aliinvn names are functio Some \n❌ print(f"    
           else:
    !")validn names are se functioAll edge ca"\n✅    print(f        d:
 _vali if all   se

    = Fald l_vali         al      alid:
  if not is_v        me}")
   int.na} -> {endpondpoint.path {e  {status}f" nt(         pri"
   else "❌if is_valid  = "✓" ustat       se)
     nt.namatch(endpoiPATTERN.m_NAME_NCTION_valid = FU          ispoints:
   api.endpoint in end      for True
  lid =ll_va      aames
   all nte# Valida      

  )}")endpointslen(api.ndpoints: {(f"   Eprint       )
 .name}"api: {APIded "✅ Loa