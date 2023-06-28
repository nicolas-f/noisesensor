import qrcode
import base64
import numpy

def generate_qrcode(data):
    qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=2,
                    border=0,
                )
    qr.add_data(data)
    qr_matrix = numpy.array(qr.get_matrix())
    qr_bits = numpy.packbits(qr_matrix).tobytes()
    return (b"var qrcode = { width: %d, height : %d, buffer : atob(\"%s\") };" % (
        qr_matrix.shape[0], qr_matrix.shape[1],
        base64.b64encode(qr_bits))).decode('UTF-8')

links = ["https://tinyurl.com/2czt4sdp",
"https://tinyurl.com/2pv58j8r",
"https://tinyurl.com/2as7fmdd",
"https://tinyurl.com/bkhepu7n",
"https://tinyurl.com/3d944drf",
"https://tinyurl.com/urvjxuy9",
"https://tinyurl.com/44wy43yu",
"https://tinyurl.com/4hcvpens",
"https://tinyurl.com/mrys5v2n",
"https://tinyurl.com/mr4427aa",
"https://tinyurl.com/2aj4npk3",
"https://tinyurl.com/4tjkbc3v",
"https://tinyurl.com/2p8c7zn4",
"https://tinyurl.com/259bp47b",
"https://tinyurl.com/yc76fbvj"]
for link in links:
    print("var qrcode_url = \"%s\";" % (link.replace("https://", "")))
    print(generate_qrcode(link))
    print("")
