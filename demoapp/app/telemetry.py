from azure.core.settings import settings
from opentelemetry.trace import Span
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry import baggage, context

settings.tracing_implementation = "opentelemetry"

class AppAttributes:
    APP_MESSAGE_ID = "app.message_id"
    APP_STATUS_MESSAGE_ID = "app.status_message_id"
    APP_MESSAGE_DTO = "app.message_dto"
    APP_STATUS_VALUE = "app.status_value"


class SpanEnrichingProcessor(SpanProcessor):
    attrs_list: list[str] = [AppAttributes.APP_MESSAGE_ID, SpanAttributes.ENDUSER_ID]

    def on_start(self, span: Span, parent_context: context.Context | None = None) -> None:
        super().on_start(span, parent_context)

        for k,v in baggage.get_all().items():
            if k in self.attrs_list:
                span.set_attribute(k, str(v))
