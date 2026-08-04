from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from main_app import views

urlpatterns = [
    path('secret-control-panel-2026/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('verify-email/', views.verify_otp, name='verify_otp'), # নতুন যুক্ত করা হলো
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.professor_dashboard, name='professor_dashboard'),
    path('professor/<int:pk>/', views.professor_detail, name='professor_detail'),
    path('bookmark/<int:prof_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('donate/checkout/', views.create_checkout_session, name='checkout_session'),
    path('donate/success/', views.payment_success, name='payment_success'),
    path('deadlines/', views.university_deadlines, name='university_deadlines'),
    path('professor/<int:prof_id>/report/', views.report_professor, name='report_professor'),
    path('update-status/<int:bookmark_id>/', views.update_application_status, name='update_status'),


    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), 
         name='password_reset'),
         
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), 
         name='password_reset_done'),
         
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), 
         name='password_reset_confirm'),
         
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), 
         name='password_reset_complete'),

     # নতুন স্ট্যাটিক পেজগুলোর URL
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms/', views.terms_view, name='terms'),
    path('university/<int:pk>/deadlines/', views.university_deadline_detail, name='university_deadline_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)