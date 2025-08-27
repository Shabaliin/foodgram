from django.urls import path, include
from .views import router, list_tags, get_tag, list_ingredients, get_ingredient

urlpatterns = [
    path('', include(router.urls)),
    path('tags/', list_tags, name='tags-list'),
    path('tags/<int:id>/', get_tag, name='tag-detail'),
    path('ingredients/', list_ingredients, name='ingredients-list'),
    path('ingredients/<int:id>/', get_ingredient, name='ingredient-detail'),
]
