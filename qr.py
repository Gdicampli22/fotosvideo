import qrcode

# La URL real de tu aplicación de invitados
url = "https://invitados70hilda.streamlit.app/"

# Configuración del QR
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)

qr.add_data(url)
qr.make(fit=True)

# Crear la imagen (fondo blanco, código negro para máximo contraste)
img = qr.make_image(fill_color="black", back_color="white")

# Guardar la imagen en tu carpeta
img.save("qr_hilda_real.png")
print("¡QR generado con éxito! Buscá el archivo qr_hilda_real.png")