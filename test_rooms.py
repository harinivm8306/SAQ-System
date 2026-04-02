import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

c = Client(HTTP_HOST='127.0.0.1')
try:
    user = User.objects.get(username='testbot')
    c.force_login(user)
    
    response = c.post('/rooms/create/', {'topic': 'Test Topic', 'mcq': 'on'})
    
    print(f"Status: {response.status_code}")
    if hasattr(response, 'url'):
        print(f"Redirect URL: {response.url}")
        
        # follow the redirect as if in browser:
        print("Following redirect...")
        res2 = c.get(response.url)
        print(f"Detail page status: {res2.status_code}")
        if res2.status_code == 500:
            print("Server error on detail page:")
            print(res2.content.decode()[:1000])
    else:
        print("No redirect. Response content:")
        # print(response.content.decode()[:500])
except Exception as e:
    print(f"Error: {e}")
