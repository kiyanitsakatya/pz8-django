from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
def healthz(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("healthz/", healthz),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('accounts.urls')),
    path("dashboard/", include("dashboard.urls")),
    path("tickets/", include("tickets.urls")),
]



