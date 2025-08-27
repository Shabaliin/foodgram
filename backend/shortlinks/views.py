from django.shortcuts import redirect, get_object_or_404
from recipes.models import RecipeShortLink


def short_redirect(request, code: str):
	link = get_object_or_404(RecipeShortLink, code=code)
	return redirect(f"/recipes/{link.recipe_id}")
