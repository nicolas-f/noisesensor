import qrcode
import base64
import numpy

qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=2,
                border=0,
            )
qr.add_data("https://surveys.ifsttar.fr/limesurvey/index.php/594853")
qr_matrix = numpy.array(qr.get_matrix())
qr_bits = numpy.packbits(qr_matrix).tobytes()
pixljs_image = b"var qrcode = { width: %d, height : %d, buffer : atob(\"%s\") };" % (
    qr_matrix.shape[0], qr_matrix.shape[1],
    base64.b64encode(qr_bits))

print(pixljs_image.decode('UTF-8'))
