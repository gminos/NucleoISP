from base.dashboard import metricas_inquilino, metricas_maestro


def dashboard_callback(request, context):
    tenant = getattr(request, "tenant", None)
    if tenant is not None and tenant.schema_name == "public":
        context.update(metricas_maestro())
    else:
        context.update(metricas_inquilino())
    return context
