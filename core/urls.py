"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main_app import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # আপনার আগের সব পাথ...
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
     path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.professor_dashboard, name='professor_dashboard'),
    path('professor/<int:pk>/', views.professor_detail, name='professor_detail'),
    path('bookmark/<int:prof_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('donate/checkout/', views.create_checkout_session, name='checkout_session'),
    path('donate/success/', views.payment_success, name='payment_success'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# urlpatterns এর একদম শেষে এটি যোগ করুন
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
