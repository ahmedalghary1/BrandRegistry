from django.urls import include, path

from . import views

app_name = 'registry'

urlpatterns = [
    path('healthz/', views.healthcheck_view, name='healthz'),
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('settings/', views.SettingsView.as_view(), name='settings'),

    path('trademarks/', include('registry.urls_trademarks', namespace='trademarks')),
    path('designs/', include('registry.urls_designs', namespace='designs')),
]
