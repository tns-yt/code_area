from django.urls import path

from . import views

app_name='judge'

urlpatterns = [
    path('signin/',views.signin,name='signin_url'),
    path('add_user/',views.add_user,name='add_user_url'),
    path('login_page/',views.login_page,name='login_page_url'),
    path("",views.home,name='home_url'),
    path("<int:id>",views.description,name='description_url'),
    path('logout/',views.logout_user,name='logout_url'),
    path("<int:id>/verdict",views.verdict,name='verdict_url')
]