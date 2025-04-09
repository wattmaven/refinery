from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from refinery.logger import configure
from refinery.middleware.correlation import CorrelationMiddleware
from refinery.routers import refine
from refinery.settings import settings
from refinery.version import __version__

configure()

app = FastAPI(
    title="WattMaven Refinery",
    description="A service for refining documents.",
    version=__version__,
    servers=[
        server
        for server in [
            {"url": "http://localhost:8000", "description": "Local"}
            # If the python environment is not production, add the local server.
            if settings.python_env != "production"
            else None,
            {
                "url": f"https://{settings.refinery_domain}",
                "description": "Production",
            },
        ]
        if server is not None
    ],
    license_info={
        "name": "Apache 2.0",
        "identifier": "Apache-2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
    contact={
        "name": "WattMaven",
        "url": "https://www.wattmaven.com",
        "email": "info@wattmaven.com",
    },
)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok"}


app.include_router(refine.router)
