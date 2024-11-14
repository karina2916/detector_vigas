from django.shortcuts import render
from django.http import HttpResponse
import cv2
import time
import os
from .forms import DatosVigaForm, CargarImagenForm
import matplotlib.pyplot as plt
from django.shortcuts import render, redirect
import numpy as np
from django.http import JsonResponse
import os
import io
import base64
from django.template import loader
from django.conf import settings
from .forms import CargarImagenForm

# Directorio donde se guardan las capturas (dentro de la carpeta static)
DIRECTORIO_VIGAS = os.path.join(settings.BASE_DIR, "static", "vigas_datos")
os.makedirs(DIRECTORIO_VIGAS, exist_ok=True)

# Función para capturar imagen
def capturar_imagen(request):
    if request.method == 'POST':
        form = CargarImagenForm(request.POST, request.FILES)
        if form.is_valid():
            imagen = form.cleaned_data['imagen']
            filepath = os.path.join(DIRECTORIO_VIGAS, imagen.name)
            
            # Guardar la imagen
            with open(filepath, 'wb+') as destination:
                for chunk in imagen.chunks():
                    destination.write(chunk)

            # Almacenar solo el nombre de la imagen en la sesión
            request.session['ruta_imagen'] = imagen.name
                    
            # Redirigir a la vista de ingreso de datos
            return redirect('ingresar_datos')
    else:
        form = CargarImagenForm()
    return render(request, "capturar_imagen.html", {'form': form})

USOS_SOBRECARGAS = {
    "biblioteca": {"sala de lectura": 300, "sala de almacenaje": 750},
    "escuelas": {"aulas y laboratorios": 300, "talleres": 300},
    "hospitales": {"cuartos": 200, "sala de operacion y laboratorios": 300},
    "oficinas": {"ambientes comunes": 250, "sala de archivos": 300},
    "viviendas": {"corredores y escaleras": 400, "incluye corredores y escaleras": 200, "azoteas planas": 100}
}

PESO_UNITARIO_ALIGERADO = {
    0.17: 280,  # 17 cm
    0.20: 300,  # 20 cm
    0.25: 350,  # 25 cm
    0.30: 420,  # 30 cm
    0.35: 475   # 35 cm
}


def cargar_imagen(request):
    if request.method == 'POST':
        form = CargarImagenForm(request.POST, request.FILES)
        if form.is_valid():
            imagen = form.cleaned_data['imagen']
            filepath = os.path.join(DIRECTORIO_VIGAS, imagen.name)
            
            # Guardar la imagen
            with open(filepath, 'wb+') as destination:
                for chunk in imagen.chunks():
                    destination.write(chunk)

            # Almacenar la ruta en la sesión
            request.session['ruta_imagen'] = filepath
                    
            # Redirigir a la vista de ingreso de datos
            return redirect('ingresar_datos')
    else:
        form = CargarImagenForm()
    return render(request, "cargar_imagen.html", {'form': form})



# Vista para obtener tipos de uso específicos según el uso seleccionado
def obtener_tipos_uso(request):
    uso = request.GET.get('uso')
    tipos = USOS_SOBRECARGAS.get(uso, {})
    opciones = [{'value': tipo, 'label': tipo} for tipo in tipos.keys()]
    return JsonResponse(opciones, safe=False)




def ingresar_datos_manualmente(request):
    ruta_imagen = request.session.get('ruta_imagen', None)
    
    if request.method == 'POST':
        form = DatosVigaForm(request.POST)
        
        # Obtener opciones dinámicamente para el tipo de uso específico
        uso_seleccionado = request.POST.get('uso')
        if uso_seleccionado:
            tipo_uso_opciones = [(tipo, tipo) for tipo in USOS_SOBRECARGAS.get(uso_seleccionado, {})]
            form.fields['tipo_uso'].choices = tipo_uso_opciones

        if form.is_valid():
            datos = form.cleaned_data
            uso = datos['uso']
            tipo_uso = datos['tipo_uso']
            sobrecarga = USOS_SOBRECARGAS[uso][tipo_uso]
            datos['sobrecarga'] = sobrecarga

            tipo_viga = datos['tipo_viga']
            
            # Seleccionar la función de cálculo en función del tipo de viga
            if tipo_viga == 'medio':
                # Cálculo para viga en medio; utiliza ambos campos de longitud perpendicular
                if 'longitud_viga_perpendicular_1' in datos and 'longitud_viga_perpendicular_2' in datos:
                    carga_muerta_total, carga_viva, carga_total = calcular_cargas(datos)
                else:
                    # Maneja el caso de campos faltantes
                    form.add_error(None, "Por favor, proporciona ambas longitudes de viga perpendicular para una viga en medio.")
                    return render(request, 'ingresar_datos.html', {'form': form, 'ruta_imagen': ruta_imagen})
                
                print("Cálculo medio realizado correctamente.")
            elif tipo_viga == 'extremo':
                # Cálculo para viga de extremo; utiliza solo un campo de longitud perpendicular
                if 'longitud_viga_perpendicular_1' in datos:
                    carga_muerta_total, carga_viva, carga_total = calcular_cargas_uno(datos)
                else:
                    # Maneja el caso de campo faltante
                    form.add_error(None, "Por favor, proporciona la longitud de viga perpendicular para una viga de extremo.")
                    return render(request, 'ingresar_datos.html', {'form': form, 'ruta_imagen': ruta_imagen})
                
                print("Cálculo extremo realizado correctamente.")
            else:
                form.add_error(None, "Tipo de viga no válido.")
                return render(request, 'ingresar_datos.html', {'form': form, 'ruta_imagen': ruta_imagen})
            
            posiciones, dfc, dmf, vdmf = calcular_dfc_dmf(carga_total, datos['longitud'])

            # Verificar imágenes generadas
            dfc_image = generar_imagen_dfc(posiciones, dfc)
            dmf_image = generar_imagen_dmf(posiciones, dmf, vdmf)

            print("Imágenes generadas correctamente.")
            viga_image = dibujar_viga(datos['longitud'], datos['base'], carga_total)
            
            context = {
            'form': form,
            'carga_muerta_total': carga_muerta_total,
            'carga_viva': carga_viva,
            'carga_total': carga_total,
            'dfc_image': dfc_image,
            'dmf_image': dmf_image,
            'viga_image': viga_image,  # Nueva imagen de la viga
            'ruta_imagen': ruta_imagen,
            }   

            return render(request, 'resultados.html', context)
        else:
            print("Errores en el formulario:", form.errors)
    else:
        form = DatosVigaForm()
    
    return render(request, 'ingresar_datos.html', {'form': form, 'ruta_imagen': ruta_imagen})






def calcular_cargas(datos):
    # Diccionario de pesos unitarios de aligerado
    PESO_UNITARIO_ALIGERADO = {
        0.17: 280,  # 17 cm
        0.20: 300,  # 20 cm
        0.25: 350,  # 25 cm
        0.30: 420,  # 30 cm
        0.35: 475   # 35 cm
    }

    # Parámetros de entrada
    base = datos['base']  # Base de la viga en metros
    peralte = datos['peralte']  # Altura de la viga en metros
    peso_unitario_concreto = 2400  # Peso unitario del concreto en kg/m³
    peso_aligerado_clave = datos['peso_aligerado']  # Peso del aligerado en kg/m²
    longitud_viga_perpendicular_1 = datos['longitud_viga_perpendicular_1']  # Longitud de la primera viga perpendicular en metros
    longitud_viga_perpendicular_2 = datos['longitud_viga_perpendicular_2']  # Longitud de la segunda viga perpendicular en metros

    # Obtener el peso del aligerado
    peso_aligerado = PESO_UNITARIO_ALIGERADO.get(peso_aligerado_clave)
    if peso_aligerado is None:
        raise ValueError(f"No se encontró el valor de peso aligerado para el espesor {peso_aligerado_clave} m.")

    # Cálculo de la carga muerta
    peso_propio = base * peralte * peso_unitario_concreto  # kg
    peso_aligerado_total = (longitud_viga_perpendicular_1 / 2 + longitud_viga_perpendicular_2 / 2) * peso_aligerado  # kg
    peso_piso_terminado = (longitud_viga_perpendicular_1 / 2 + longitud_viga_perpendicular_2 / 2 + base) * 100  # kg
    carga_muerta_total = peso_propio + peso_aligerado_total + peso_piso_terminado  # kg

    # Cálculo de la carga viva
    carga_viva = (longitud_viga_perpendicular_1 / 2 + longitud_viga_perpendicular_2 / 2 + base) * datos['sobrecarga']  # kg

    # Carga total
    carga_total = carga_muerta_total + carga_viva  # kg
    return carga_muerta_total, carga_viva, carga_total

def calcular_cargas_uno(datos):
    # Imprimir todos los datos recibidos para diagnóstico
    print("Datos recibidos:", datos)  # Este print ayudará a ver todos los datos

    # Extrae los valores necesarios y verifica que no sean None
    base = datos.get('base')
    peralte = datos.get('peralte')
    peso_aligerado_clave = datos.get('peso_aligerado')
    longitud_viga_perpendicular_1 = datos.get('longitud_viga_perpendicular_1')
    
    # Verifica que todos los valores importantes no sean None
    if base is None or peralte is None or peso_aligerado_clave is None or longitud_viga_perpendicular_1 is None:
        raise ValueError("Uno o más valores requeridos están faltando en los datos.")

    peso_unitario_concreto = 2400
    
    # Diccionario de pesos unitarios de aligerado
    PESO_UNITARIO_ALIGERADO = {
        0.17: 280,  # 17 cm
        0.20: 300,  # 20 cm
        0.25: 350,  # 25 cm
        0.30: 420,  # 30 cm
        0.35: 475   # 35 cm
    }
    
    # Obtener el peso del aligerado
    peso_aligerado = PESO_UNITARIO_ALIGERADO.get(peso_aligerado_clave)
    if peso_aligerado is None:
        raise ValueError(f"No se encontró el valor de peso aligerado para el espesor {peso_aligerado_clave} m.")
    
    # Cálculo del peso propio de la viga (carga muerta del concreto)
    peso_propio = base * peralte * peso_unitario_concreto  # kg

    # Cálculo del peso del aligerado
    peso_aligerado_total = (longitud_viga_perpendicular_1 / 2) * peso_aligerado  # kg

    # Cálculo del peso del piso terminado
    peso_piso_terminado = (longitud_viga_perpendicular_1 / 2 + base) * 100  # kg

    carga_muerta_total = peso_propio + peso_aligerado_total + peso_piso_terminado  # kg

    # Cálculo de la carga viva
    carga_viva = (longitud_viga_perpendicular_1 / 2 + base) * peso_aligerado  # kg

    # Carga total
    carga_total = carga_muerta_total + carga_viva  # kg

    return carga_muerta_total, carga_viva, carga_total

def calcular_dfc_dmf(carga_total, longitud):
    carga_distribuida = carga_total / longitud
    posiciones = np.linspace(0, longitud, 100)
    
    # Diagrama de fuerzas cortantes (V) - variación lineal
    dfc = [carga_total * (longitud / 2 - x) for x in posiciones]  # Fuerza cortante decrece linealmente

    vdmf = [carga_total * (pow(longitud,2)) / 8]
    # Diagrama de momentos flectores (M) - variación parabólica
    dmf = [carga_total * x * (longitud - x) / 2 for x in posiciones]  # Momento flector es parabólico
    
    return posiciones, dfc, dmf, vdmf


def dibujar_viga(longitud, base, carga_total):
    # Crear la figura y los ejes
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Dibujar la viga como un rectángulo gris claro con borde
    ax.add_patch(plt.Rectangle((0, 0), longitud, base, edgecolor='black', facecolor='#D3D3D3', linewidth=2, label='Viga'))
    
    # Dibujar la carga distribuida con flechas azules hacia abajo
    num_flechas = 10  # Número de flechas distribuidas a lo largo de la viga
    for i in range(num_flechas):
        x_pos = i * (longitud / (num_flechas - 1))
        ax.arrow(x_pos, base + 0.3, 0, -0.3, head_width=0.15, head_length=0.2, fc='royalblue', ec='royalblue', linewidth=1.5)
    
    # Etiqueta de la carga distribuida mostrando la carga total en negrita
    ax.text(longitud / 2, base + 0.6, f'Carga total: {carga_total} kg', ha='center', color='black', fontsize=14, weight='bold')
    
    # Flechas indicando la longitud de la viga, con un estilo más destacado
    ax.annotate('', xy=(0, -0.2), xytext=(longitud, -0.2), arrowprops=dict(arrowstyle='<->', lw=2, color='black'))
    ax.text(longitud / 2, -0.3, f'Longitud: {longitud} m', ha='center', fontsize=12, style='italic', weight='bold')
    
    # Soporte fijo en el extremo izquierdo con triángulo y un efecto sombreado
    soporte_fijo_x = [-0.5, 0, 0.5]
    soporte_fijo_y = [-0.3, 0, -0.3]
    ax.fill(soporte_fijo_x, soporte_fijo_y, 'black')
    
    # Soporte móvil en el extremo derecho con triángulo y círculos mejor alineados
    soporte_movil_x = [longitud - 0.5, longitud, longitud + 0.5]
    soporte_movil_y = [-0.3, 0, -0.3]
    ax.fill(soporte_movil_x, soporte_movil_y, 'black')
    ax.plot(longitud - 0.2, -0.4, marker='o', markersize=8, color='black')  # Primer círculo del soporte móvil
    ax.plot(longitud + 0.2, -0.4, marker='o', markersize=8, color='black')  # Segundo círculo del soporte móvil
    
    # Configuración de límites y ocultar los ejes
    ax.set_xlim(-1, longitud + 1)
    ax.set_ylim(-1, 2)
    ax.axis('off')  # Desactivar ejes
    
    # Guardar la figura en un buffer para codificarla en base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)
    graphic = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return graphic

def generar_imagen_dfc(posiciones, dfc):
    plt.figure(figsize=(6, 4))
    plt.plot(posiciones, dfc, color='green', linewidth=2, label='Shear Force')
    plt.fill_between(posiciones, dfc, color='lightgreen', alpha=0.5)
    plt.xlabel('Distance (m)', fontsize=10)
    plt.ylabel('Shear Force (Kg)', fontsize=10)
    plt.axhline(0, color='black', linewidth=1)
    plt.grid(True)

    # Anotar valores en los extremos
    plt.text(posiciones[0], dfc[0], f"{dfc[0]:.2f} Kg", ha='center', va='bottom', color='green', fontsize=8, weight='bold')
    plt.text(posiciones[-1], dfc[-1], f"{dfc[-1]:.2f} Kg", ha='center', va='bottom', color='green', fontsize=8, weight='bold')
    
    # Guardar la figura en un buffer para codificarla en base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    graphic = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return graphic

def generar_imagen_dmf(posiciones, dmf, vdmf):
    plt.figure(figsize=(6, 4))
    plt.plot(posiciones, dmf, color='red', linewidth=2, label='Bending Moment')
    plt.fill_between(posiciones, dmf, color='lightcoral', alpha=0.5)
    plt.xlabel('Distance (m)', fontsize=10)
    plt.ylabel('Bending Moment (Kg·m)', fontsize=10)
    plt.axhline(0, color='black', linewidth=1)
    plt.grid(True)

    # Encontrar el valor máximo del momento flector
    max_momento = max(vdmf)
    # Posicionar el texto en el centro del gráfico
    centro_posicion = posiciones[len(posiciones) // 2]  # Usamos el punto central de posiciones
    plt.text(centro_posicion, max_momento, f"{max_momento:.2f} Kg·m", ha='center', va='bottom', color='red', fontsize=8, weight='bold', bbox=dict(facecolor='white', alpha=0.6))

    # Guardar la figura en un buffer para codificarla en base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    graphic = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return graphic

