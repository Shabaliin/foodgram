from django.urls import path, include
from .views import router, list_tags, get_tag, list_ingredients, get_ingredient

urlpatterns = [
    path('', include(router.urls)),  # /recipes/, /recipes/{id}/...
    path('tags/', list_tags, name='tags-list'),  # /tags/
    path('tags/<int:id>/', get_tag, name='tag-detail'),  # /tags/{id}/
    path('ingredients/', list_ingredients, name='ingredients-list'),  # /ingredients/
    path('ingredients/<int:id>/', get_ingredient, name='ingredient-detail'),  # /ingredients/{id}/
]
