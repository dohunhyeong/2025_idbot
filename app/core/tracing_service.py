import os
from langfuse import Langfuse


class TracingService:
    def __init__(self):
        self._client = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )

    def start_trace(self, *, trace_id: str, name: str, input: str):
        return self._client.trace(id=trace_id, name=name, input=input)

    def end_trace(self, trace, *, output: str, metadata: dict) -> None:
        trace.update(output=output, metadata=metadata)

    def start_span(self, trace, *, name: str, input) -> object:
        return trace.span(name=name, input=input)

    def end_span(self, span, *, output, metadata: dict | None = None) -> None:
        kwargs = {"output": output}
        if metadata:
            kwargs["metadata"] = metadata
        span.end(**kwargs)

    def log_event(self, span, *, name: str, body: dict) -> None:
        span.event(name=name, metadata=body)

    def flush(self) -> None:
        self._client.flush()
