from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Subscription


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	fieldsets = DjangoUserAdmin.fieldsets + (
		('Дополнительно', {'fields': ('avatar',)}),
	)
	add_fieldsets = DjangoUserAdmin.add_fieldsets
	list_display = ('id', 'email', 'username', 'first_name', 'last_name')
	search_fields = ('email', 'username', 'first_name', 'last_name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
	list_display = ('user', 'author')
	search_fields = ('user__email', 'author__email')
