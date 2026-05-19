import jwt
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.utils.deprecation import MiddlewareMixin

class EdgeAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                
                email = payload.get('email')
                realm_access = payload.get('realm_access', {})
                roles = realm_access.get('roles', [])
                
                if email:
                    user, created = User.objects.get_or_create(
                        email=email, 
                        defaults={'username': payload.get('preferred_username', email)}
                    )
                    
                    if 'django_root' in roles:
                        user.is_superuser = True
                        user.is_staff = True
                    else:
                        user.is_superuser = False
                        user.is_staff = False
                    
                    user.save()
                    
                    if not request.user.is_authenticated or request.user.email != email:
                        login(request, user)
                        
            except Exception as e:
                pass