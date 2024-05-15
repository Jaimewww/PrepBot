class MensajeRta():
    mensaje = ""
    rta = True

class Utilitario(object):
    def validacionCedula(cedula):
        mensajeRta = MensajeRta
        #rta = True
        if len(cedula) == 10:
            provstr = str(cedula)
            prov = int(provstr[:2])
            prim_num = str(provstr[:9])
            ult_num = int(provstr[9])
            if prov > 0 & prov <= 24:
                arr = [2,1,2,1,2,1,2,1,2]
                sum = 0
                count = 0
                for n in prim_num:
                    producto = int(prim_num[count]) * arr[count]
                    producto_str = str(producto)
                    if producto >= 10:
                        sum += int(producto_str[0]) + int(producto_str[1])
                    else:
                        sum += producto
                    count = count+1 
                residuo = sum % 10
                resultado = 10 - residuo
                if resultado == ult_num:
                    #print("Correcto")
                    #rta =True
                    mensajeRta.mensaje = "Correcto"
                    mensajeRta.rta = True
                else:
                    #print("Incorrecto")
                    mensajeRta.mensaje = "Error al validar la cédula."
                    mensajeRta.rta = False
            else:
                #print("Error en los dos primeros dígitos")
                #rta =False
                mensajeRta.mensaje = "Error en los dos primeros dígitos"
                mensajeRta.rta = False
        else:
            #print("La cédula debe tener 10 dígitos")
            mensajeRta.mensaje = "La cédula debe tener 10 dígitos"
            mensajeRta.rta = False
        return mensajeRta