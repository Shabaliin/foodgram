from django.urls import path, include

urlpatterns = [
    # domain apps (custom routes first to avoid shadowing by djoser)
    path('', include('users.urls')),
    path('', include('recipes.urls')),
    # Djoser users endpoints at root: /users/, /users/me/, /users/set_password/, /users/reset_password/
    path('', include('djoser.urls')),
    # Auth token endpoints: /auth/token/login/, /auth/token/logout/
    path('auth/', include('djoser.urls.authtoken')),
]
