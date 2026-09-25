import os
import sys

# Ensure parent directory is in sys.path for Vercel
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from mcp.server.transport_security import TransportSecuritySettings
from mcp_server import app as mcp_instance

sec_settings = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
    allowed_hosts=["*"],
    allowed_origins=["*"]
)

# Stateless Streamable HTTP app for Vercel Serverless
mcp_starlette = mcp_instance.streamable_http_app(
    streamable_http_path="/mcp",
    stateless_http=True,
    transport_security=sec_settings
)

async def root_status(request):
    return JSONResponse({
        "status": "online",
        "service": "AhmedGeminiSparkBridge",
        "mcp_endpoint": "/mcp"
    })

# Main Vercel Entrypoint
app = Starlette(
    routes=[
        Route("/", endpoint=root_status),
        Mount("/", app=mcp_starlette)
    ]
)
