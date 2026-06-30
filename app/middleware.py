import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app import metrics


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        route = request.scope.get("route")
        route_label = route.path if route else request.url.path
        metrics.record_http_request(route_label, response.status_code, duration)
        return response
