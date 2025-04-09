import click
import uvicorn


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to run the server on")
@click.option("--port", default=8000, help="Port to run the server on")
@click.option("--reload", is_flag=False, help="Reload the server on code changes")
def main(host: str, port: int, reload: bool):
    """Entry point for the application script."""
    uvicorn.run(
        "fastapi_template.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
