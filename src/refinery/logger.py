import logging
from contextvars import ContextVar
from typing import Any, Generic, TypeVar

import structlog
from structlog.typing import EventDict

from refinery.settings import settings

RendererType = TypeVar("RendererType")


Logger = structlog.stdlib.BoundLogger

# Context variable for correlation ID
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def add_correlation_id(_, __, event_dict: EventDict) -> EventDict:
    """Add correlation ID to log entries."""
    event_dict["correlation_id"] = correlation_id.get()
    return event_dict


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


class Logging(Generic[RendererType]):
    """Customized implementation inspired by the following documentation:

    https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging
    """

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_correlation_id,
        drop_color_message_key,
        timestamper,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.StackInfoRenderer(),
    ]

    @classmethod
    def get_processors(cls) -> list[Any]:
        if settings.python_env == "production":
            cls.shared_processors.append(structlog.processors.format_exc_info)

        return cls.shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter
        ]

    @classmethod
    def get_renderer(cls) -> RendererType:
        raise NotImplementedError()

    @classmethod
    def configure_stdlib(
        cls,
    ) -> None:
        if settings.python_env == "production":
            cls.shared_processors.append(structlog.processors.format_exc_info)

        # Set the log level from settings, defaulting to `logging.INFO`
        log_level = getattr(settings, "log_level", logging.INFO)
        # Set the log level for the root logger
        logging.basicConfig(level=log_level)
        # Set the log level for structlog
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(log_level)
        )

    @classmethod
    def configure_structlog(cls) -> None:
        structlog.configure(
            processors=cls.get_processors(),
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    @classmethod
    def configure(cls) -> None:
        cls.configure_stdlib()
        cls.configure_structlog()


class Development(Logging[structlog.dev.ConsoleRenderer]):
    @classmethod
    def get_renderer(cls) -> structlog.dev.ConsoleRenderer:
        return structlog.dev.ConsoleRenderer(colors=True)


class Production(Logging[structlog.processors.JSONRenderer]):
    @classmethod
    def get_renderer(cls) -> structlog.processors.JSONRenderer:
        return structlog.processors.JSONRenderer()


def configure() -> None:
    match settings.python_env:
        case "development":
            Development.configure()
        case _:
            Production.configure()


logger: Logger = structlog.get_logger()


# Helper function to set correlation ID from headers
def set_correlation_id(corr_id: str) -> None:
    """Set the correlation ID from headers."""
    correlation_id.set(corr_id)
