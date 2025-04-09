from fastapi import FastAPI

from fastapi_template.settings import settings

app = FastAPI(
    title="FastAPI Template",
    description="A template for a FastAPI project.",
    version="0.0.0",
    servers=[
        server
        for server in [
            {"url": "http://localhost:8000", "description": "Local"}
            # If the python environment is not production, add the local server.
            if settings.python_env != "production"
            else None,
            {
                "url": f"https://{settings.fastapi_template_domain}",
                "description": "Production",
            },
        ]
        if server is not None
    ],
    license_info={
        "name": "MIT",
        "identifier": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    contact={
        "name": "WattMaven",
        "url": "https://www.wattmaven.com",
        "email": "info@wattmaven.com",
    },
)


@app.get("/")
async def root():
    return {"status": "ok"}
