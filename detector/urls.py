# urls.py en la app 'calculos_vigas'
from django.urls import path
from . import views

urlpatterns = [
    path('', views.capturar_imagen, name='capturar_imagen'),
    path('ingresar-datos/', views.ingresar_datos_manualmente, name='ingresar_datos'),
    path('obtener-tipos-uso/', views.obtener_tipos_uso, name='obtener_tipos_uso'),
    
    path('capturar-imagen/', views.capturar_imagen, name='capturar_imagen'),
    
]