import contextvars

request_id_ctx = contextvars.ContextVar("request_id", default="")
consent_trace_id_ctx = contextvars.ContextVar("consent_trace_id", default="")

def set_trace_context(request_id: str, consent_trace_id: str):
    request_id_ctx.set(request_id)
    consent_trace_id_ctx.set(consent_trace_id)

def clear_trace_context():
    request_id_ctx.set("")
    consent_trace_id_ctx.set("")

def get_request_id():
    return request_id_ctx.get()

def get_consent_trace_id():
    return consent_trace_id_ctx.get()
