try:
    from mcp_local.server.fastmcp import FastMCP

    print("FastMCP imported successfully")
    methods = [method for method in dir(FastMCP) if not method.startswith("_")]
    print("FastMCP methods:", methods)

    # Check specifically for the streamable_http_app method
    if "streamable_http_app" in methods:
        print("streamable_http_app method is available")
    else:
        print("streamable_http_app method is NOT available")

    # Check for other mounting methods
    mount_methods = [
        method for method in methods if "mount" in method.lower() or "http" in method.lower()
    ]
    print("Potential mount/HTTP methods:", mount_methods)

except ImportError as e:
    print("Import error:", e)

    # Try to import the local implementation
    try:
        from mcp_local.raptor_mcp_server import RaptorMCPService

        print("Local RaptorMCPService imported successfully")
        methods = [method for method in dir(RaptorMCPService) if not method.startswith("_")]
        print("RaptorMCPService methods:", methods)
    except ImportError as e2:
        print("Local implementation import error:", e2)
