from opentelemetry import metrics

meter = metrics.get_meter_provider().get_meter("demoapp.instrumentation")

created_messages_counter = meter.create_counter(
    name="demoapp.created_messages",
    description="How many messages created and sent to Service Bus",
    unit="message")

processed_messages_counter = meter.create_counter(
    name="demoapp.processed_messages",
    description="How many messages successfully processed: saved to DB and Storage",
    unit="message")
