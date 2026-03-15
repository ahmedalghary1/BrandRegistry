from django.urls import path

from . import views

app_name = 'trademarks'

urlpatterns = [
    path('', views.TrademarkListView.as_view(), name='list'),
    path('add/', views.TrademarkCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.TrademarkUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.TrademarkDeleteView.as_view(), name='delete'),
]