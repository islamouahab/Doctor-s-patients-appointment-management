from django.contrib import admin
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.home , name = 'home'),
    path('doctor_login/', views.doc_login , name = 'doc_login'),
    path('lab_login', views.lab_login, name='lab_login'),
    path('doctor_register',views.doc_register, name='doc_register'),
    path('doctor_logout',views.doc_logout, name='doc_logout'),
    path('lab_register',views.lab_register,name='lab_register'),
    path('lab_logout',views.lab_logout,name="lab_logout"),
    path('doctor_dashboard',views.doc_dashboard,name='doc_dashboard'),
    path('doc_sch_time',views.doc_sch_time,name ='doc_sch_time'),
    path('lab_dashboard',views.lab_dashboard, name='lab_dashboard'),
    path('lab_sch_time',views.lab_sch, name='lab_sch_time'),
    path('lab_send_analysis',views.lab_send_analysis,name='lab_send_analysis'),
    path('lab_send_analysis/upload_result/', views.UploadResultView.as_view(), name='upload_result'),
    path('doctor-schedule-timings',views.doc_sch_time, name='doc_sch_time'),
    path('tests',views.tests,name='tests')
    
]