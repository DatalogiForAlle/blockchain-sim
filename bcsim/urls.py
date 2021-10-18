from django.urls import path

from . import views

app_name = 'bcsim'
urlpatterns = [
    path('', views.home_view, name='home'),
    path('minedrift/', views.mine_view, name='mine'),
    path('logout/', views.logout_view, name='logout'),
    path('block-list/', views.block_list_view_htmx, name="block_list")
]
