from django.urls import path

from . import views

app_name = 'designs'

urlpatterns = [
    path('', views.DesignListView.as_view(), name='list'),
    path('add/', views.DesignCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.DesignUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.DesignDeleteView.as_view(), name='delete'),
]