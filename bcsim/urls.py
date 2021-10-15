from django.urls import path

from . import views

app_name = 'bcsim'
urlpatterns = [
    path('', views.home_view, name='home'),
    path('create_view/', views.create_view, name='create'),
    path('mine/', views.mine_view, name='mine'),
    path('logout/', views.logout_view, name='logout'),
]
