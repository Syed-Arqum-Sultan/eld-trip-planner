# filepath: e:\eld-trip-planner\eld_backend\eldtrip\urls.py
from django.urls import path
from .views import GeocodeView, CalculateRouteView, GenerateEldLogsView

urlpatterns = [
    # path('', index, name='index'),
    path('geocode/', GeocodeView.as_view(), name='geocode'),
    path('calculate-route/', CalculateRouteView.as_view(), name='calculate_route'),
    path('generate-eld-logs/', GenerateEldLogsView.as_view(), name='generate_eld_logs'),
]