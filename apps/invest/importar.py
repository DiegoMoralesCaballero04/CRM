#encoding:utf-8
import csv

from invest.models import Provincia, Poblacion, Cliente, Responsable

def ImportarProvincias():
    nombre_fichero='fich_importaciones/pueblos.csv'
    with open(nombre_fichero,'r') as f:
        reader=csv.reader(f, delimiter =',')
        for row in reader:                
            print (row)            
            provs=Provincia.objects.filter(codigo=row[0])
            if not provs:
                Provincia.objects.create(
                        codigo=row[0],
                        nombre=row[1]
                    )
            prov=Provincia.objects.get(codigo=row[0])
            try:
                pueblos=Poblacion.objects.get(provincia=prov, nombre=row[2])
            except:
                Poblacion.objects.create(
                    provincia=prov,
                    nombre=row[2],
                    cp=row[3],
                    longitud=row[4],
                    latitud=row[5]
                )
    matriz=[
        ['Ã¡','á'],
        ['Ã','Á'],        
        ['Ã©','é'],
        ['Ã³','ó'],
        ['Ãº','ú'],
        ['Ã±','ñ'],
        ['Ã','í'],
        ]
    for elemento in matriz:
        for prov in Provincia.objects.filter(nombre__contains=elemento[0]):
            prov.nombre=prov.nombre.replace(elemento[0],elemento[1])
            prov.save()

    for elemento in matriz:        
        for pob in Poblacion.objects.filter(nombre__contains=elemento[0]):
            pob.nombre=pob.nombre.replace(elemento[0],elemento[1])
            pob.save()


def ImportarInversores():
    nombre_fichero='fich_importaciones/inversores.csv'

    responsable=Responsable.objects.filter(anulado_por=None).first()
    with open(nombre_fichero,'r', encoding='utf-8') as f:
        reader=csv.reader(f, delimiter =',')
        for row in reader:                
            print (row)            
            nombre=row[1]
            codigo=row[2]
            zona=row[3]
            emails=row[4].split(";")
            telf=row[5]
            email_1="";email_2="";email_3="";
            try:
                email_1=emails[0].strip()
                email_2=emails[1].strip()
                email_3=emails[2].strip()
            except:
                pass

            cliente=Cliente.objects.filter(nombre=nombre).first()
            if not cliente:
                Cliente.objects.create(
                    nombre=nombre,
                    codigo=codigo,
                    zona=zona,
                    telefono=telf,
                    correo=email_1,
                    correo_2=email_2,
                    correo_3=email_3,
                    responsable=responsable
                    )
