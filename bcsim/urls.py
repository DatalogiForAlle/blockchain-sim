from django.urls import path

from . import views

app_name = 'bcsim'
urlpatterns = [
    path('', views.home_view, name='home'),
    #path('join_market/', views.join_market, name='join_market'),
]