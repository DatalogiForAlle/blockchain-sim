from django.urls import path

from . import views

app_name = 'bcsim'
urlpatterns = [
    path('', views.home_view, name='home'),
    path('deltagere/', views.participants_view, name='participants'),
    path('inviter/', views.invite_view, name='invite'),
    path('buy_token/', views.buy_token_view, name='buy_token'),
    path('minedrift/', views.mine_view, name='mine'),
    path('markedsplads/', views.market_view, name='market'),
    path('toggle_pause/', views.toggle_pause_view, name='toggle_pause'),
    path('logout/', views.logout_view, name='logout'),
    path('block-list/', views.block_list_view_htmx, name="block_list"),
]
