from django.contrib import admin

from .models import (
	Tag,
	Ingredient,
	Recipe,
	RecipeIngredient,
	Favorite,
	ShoppingCart,
	RecipeShortLink,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    search_fields = (
        'name',
        'author__username', 'author__email',
        'author__first_name', 'author__last_name',
    )
    list_filter = ('tags',)
    inlines = [RecipeIngredientInline]
    readonly_fields = ('favorites_total',)

    fieldsets = (
        (None, {'fields': (
            'author', 'name', 'image', 'text', 'cooking_time', 'tags'
        )}),
        ('Служебное', {'fields': ('favorites_total',)}),
    )

	@admin.display(description='В избранном (кол-во)')
	def favorites_total(self, obj: Recipe) -> int:
		return Favorite.objects.filter(recipe=obj).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')


@admin.register(RecipeShortLink)
class RecipeShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'code', 'created_at')
    search_fields = ('recipe__name', 'code')
