"""

=============================================================================================

Name: bluesky_auth.py
Description: Module for handling Bluesky authentication and token management.  
Author: Josué Soto
Date: April 2026 
Version: 1.0

=============================================================================================

"""


from atproto import Client





client = Client()
client.login('onesocial.bsky.social', 'kzu7-nq4a-awd4-7dt2')

post = client.send_post('Hello world! I posted this via the Python SDK with an app password c:.')

print(post)



"""
with open('my_cat.jpg', 'rb') as f:
    img_data = f.read()

client.send_image(text='I love my cat', image=img_data, image_alt='My cat mittens')
"""