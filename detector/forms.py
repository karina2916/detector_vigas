from django import forms

USO_CHOICES = [
    ('biblioteca', 'Biblioteca'),
    ('escuelas', 'Escuelas'),
    ('hospitales', 'Hospitales'),
    ('oficinas', 'Oficinas'),
    ('viviendas', 'Viviendas'),
]

TIPO_VIGA_CHOICES = [
    ('medio', 'Viga en medio'),
    ('extremo', 'Viga de extremo')
]

class DatosVigaForm(forms.Form):
    # Campos de selección de uso y tipo de viga
    uso = forms.ChoiceField(choices=USO_CHOICES, label="Uso de la viga")
    tipo_uso = forms.ChoiceField(choices=[], label="Tipo de uso específico", required=True)
    tipo_viga = forms.ChoiceField(choices=TIPO_VIGA_CHOICES, label="Tipo de Viga", required=True)
    
    # Campos comunes para ambas opciones de viga
    longitud = forms.FloatField(label='Longitud de la viga (m)')
    base = forms.FloatField(label='Base de la viga (m)')
    peralte = forms.FloatField(label='Altura de la viga (Peralte) (m)')
    peso_aligerado = forms.FloatField(label='Espesor del aligerado (m)')

    # Campos adicionales para las longitudes de vigas perpendiculares
    longitud_viga_perpendicular_1 = forms.FloatField(label="Longitud de la primera viga perpendicular (m)", required=False)
    longitud_viga_perpendicular_2 = forms.FloatField(label="Longitud de la segunda viga perpendicular (m)", required=False)

class CargarImagenForm(forms.Form):
    imagen = forms.ImageField(label="Selecciona una imagen desde tu computadora")