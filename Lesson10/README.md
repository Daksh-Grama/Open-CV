# Raspberry Pi Image Receiver

This app accepts JPEG or PNG uploads from a Raspberry Pi on the same local
network. Open its mobile-friendly gallery on your iPhone in Safari.

## Run the receiver

On the computer that will receive the images, open PowerShell in this folder
and run:

```powershell
python App.py
```

Find the receiver computer's IPv4 address with `ipconfig`. Connect the iPhone
to the same Wi-Fi network, open Safari, and visit
`http://<computer-ip>:8000/` (replace `<computer-ip>` with that IPv4 address).
In Safari, use **Share > Add to Home Screen** to add a home-screen shortcut.
Keep the receiver running on the computer; refresh the gallery on the iPhone
to see new photos. Allow Python through Windows Firewall on your private
network if prompted.

Uploads are stored in `motion_captures`. The receiver accepts JPEG and PNG
images up to 10 MB. Keep it on a trusted local network; do not expose this
server directly to the internet.

To require a shared token, set it before starting the receiver:

```powershell
$env:PI_UPLOAD_TOKEN = "replace-with-a-private-token"
python App.py
```

## Send an image from the Raspberry Pi

Replace the IP address below with the receiver computer's IPv4 address. Run
this Python code on the Pi, passing the path of a JPEG or PNG image. The Pi
uploads directly to the computer; the iPhone only needs to open the gallery:

```python
import mimetypes
import os
import sys
import urllib.request

image_path = sys.argv[1]
receiver_url = "http://192.168.1.25:8000/upload"
content_type = mimetypes.guess_type(image_path)[0]
if content_type not in ("image/jpeg", "image/png"):
    raise ValueError("Choose a JPEG or PNG image")

with open(image_path, "rb") as image_file:
    request = urllib.request.Request(
        receiver_url,
        data=image_file.read(),
        headers={"Content-Type": content_type},
        method="POST",
    )
token = os.environ.get("PI_UPLOAD_TOKEN")
if token:
    request.add_header("X-Upload-Token", token)

with urllib.request.urlopen(request, timeout=15) as response:
    print(response.status, response.read().decode("utf-8"))
```

Save that as `send_image.py`, then run `python3 send_image.py /path/to/photo.jpg`.
If a token is enabled on the receiver, set the same `PI_UPLOAD_TOKEN` environment
variable on the Pi before running the script.
