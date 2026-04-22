from django.urls import include, path

from . import views

app_name = 'registry'

urlpatterns = [
    path('healthz/', views.healthcheck_view, name='healthz'),
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/backup/create/', views.DatabaseBackupCreateView.as_view(), name='backup_create'),
    path('settings/backup/restore/', views.DatabaseBackupRestoreView.as_view(), name='backup_restore'),
    path('settings/backup/download/<str:backup_name>/', views.DatabaseBackupDownloadView.as_view(), name='backup_download'),
    path('desktop/backup/create/', views.DesktopBackupCreateView.as_view(), name='desktop_backup_create'),
    path('desktop/backup-before-exit/', views.DesktopBackupBeforeExitView.as_view(), name='desktop_backup_before_exit'),

    path('trademarks/', include('registry.urls_trademarks', namespace='trademarks')),
    path('designs/', include('registry.urls_designs', namespace='designs')),
]
