#!/usr/local/bin/python3

import pyimgur
import pickle
import upload_conf

hm_png = "2022 Honorable Mentions.png"
motyc_png = "2022 MOTYCs.png"
hm_bar = "2022 Honorable Mentions Bar Chart.gif"
motyc_bar = "2022 MOTYCs Bar Chart.gif"

#### Uncomment from here to get the initial auth tokens saved

#im = pyimgur.Imgur(upload_conf.CLIENT_ID, upload_conf.CLIENT_SECRET)

#auth_url = im.authorization_url('pin')
#print(f'Visit {auth_url}')
#pin = input("What is the pin? ") # Python 3x

#im.exchange_pin(pin)

#pickle.dump(im, open("imgur_obj.p", "wb"))

#### End of the initial auth credits bit

im = pickle.load( open("imgur_obj.p", "rb"))

hm_uploaded_image = im.upload_image(hm_png, title="2022 Honorable Mentions")
motyc_uploaded_image = im.upload_image(motyc_png, title="2022 MoTYCs")
hm_bar_uploaded_image = im.upload_image(hm_bar, title="2022 Honorable Mentions Bar Chart")
motyc_bar_uploaded_image = im.upload_image(motyc_bar, title="2022 MoTYCs Bar Chart")

print(hm_bar_uploaded_image.title)
print(hm_bar_uploaded_image.link)

print(motyc_bar_uploaded_image.title)
print(motyc_bar_uploaded_image.link)

print(hm_uploaded_image.title)
print(hm_uploaded_image.link)

print(motyc_uploaded_image.title)
print(motyc_uploaded_image.link)
print("\n")

print("[b]Charts[/b]\n")
print(f"[img]{motyc_bar_uploaded_image.link}[/img]\n")
print(f"[img]{hm_bar_uploaded_image.link}[/img]\n")
print(f"[img]{motyc_uploaded_image.link}[/img]\n")
print(f"[img]{hm_uploaded_image.link}[/img]\n")

