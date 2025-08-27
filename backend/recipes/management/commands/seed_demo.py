import io
import random
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient


class Command(BaseCommand):
    help = 'Create demo users and at least one recipe per user'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding demo data...'))
        User = get_user_model()

        # Ensure tags
        tags = [
            ('Завтрак', 'breakfast'),
            ('Обед', 'lunch'),
            ('Ужин', 'dinner'),
        ]
        for name, slug in tags:
            Tag.objects.get_or_create(name=name, slug=slug)

        # Ensure ingredients (if empty)
        if Ingredient.objects.count() == 0:
            seed_ingredients = [
                ('Яйца', 'шт'),
                ('Молоко', 'мл'),
                ('Мука', 'г'),
                ('Сахар', 'г'),
                ('Соль', 'г'),
                ('Масло сливочное', 'г'),
                ('Курица', 'г'),
                ('Рис', 'г'),
                ('Помидоры', 'шт'),
                ('Огурцы', 'шт'),
            ]
            for name, mu in seed_ingredients:
                Ingredient.objects.get_or_create(
                    name=name, measurement_unit=mu
                )
            self.stdout.write(self.style.SUCCESS(
                f'Created {len(seed_ingredients)} sample ingredients')
            )

        # Create users
        users_data = [
            (
                'admin@foodgram.local', 'admin', 'Админ', 'Локальный',
                'Admin12345', True, True,
            ),
            (
                'manager@foodgram.local', 'manager', 'Менеджер', 'Тестовый',
                'Manager12345', True, False,
            ),
            (
                'alice@foodgram.local', 'alice', 'Алиса', 'Авторы',
                'Pass12345!', False, False,
            ),
            (
                'bob@foodgram.local', 'bob', 'Боб', 'Авторы',
                'Pass12345!', False, False,
            ),
            (
                'carol@foodgram.local', 'carol', 'Кэрол', 'Авторы',
                'Pass12345!', False, False,
            ),
        ]

        created_users = []
        for (
            email,
            username,
            first_name,
            last_name,
            password,
            is_staff,
            is_superuser,
        ) in users_data:
            user, created = User.objects.get_or_create(email=email, defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
            })
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Created user {email} / {password}')
                )
            else:
                self.stdout.write(f'User exists: {email}')
            # Ensure avatar
            if not user.avatar:
                img = self._generate_image(
                    (300, 300), 
                    text=username[:1].upper()
                )
                user.avatar.save(
                    f'{username}_avatar.png', ContentFile(img.getvalue()), save=True
                )
            created_users.append((user, password))

        # Create at least one recipe for each non-admin
        all_ingredients = list(Ingredient.objects.all())
        all_tags = list(Tag.objects.all())

        for user, _ in created_users:
            if user.is_superuser:
                continue
            if Recipe.objects.filter(author=user).exists():
                self.stdout.write(f'{user.email} already has recipes, skipping')
                continue
            recipe_name = f'Рецепт от {user.first_name or user.username}'
            recipe_text = 'Описание шага 1. Описание шага 2. Приятного аппетита!'
            cooking_time = random.randint(10, 60)
            recipe = Recipe(author=user, name=recipe_name, text=recipe_text, cooking_time=cooking_time)
            img = self._generate_image((800, 600), text=user.username.title())
            recipe.image.save(f'{user.username}_recipe.png', ContentFile(img.getvalue()), save=False)
            recipe.save()
            # Tags
            recipe.tags.set(random.sample(all_tags, k=min(2, len(all_tags))))
            # Ingredients
            for ing in random.sample(all_ingredients, k=min(3, len(all_ingredients))):
                RecipeIngredient.objects.create(recipe=recipe, ingredient=ing, amount=random.randint(1, 5) * 50)
            self.stdout.write(self.style.SUCCESS(f'Created recipe "{recipe.name}" for {user.email}'))

        self.stdout.write(self.style.SUCCESS('Demo data seeding complete.'))

    def _generate_image(self, size=(400, 300), text='Foodgram') -> io.BytesIO:
        # Generate a simple PNG with background color and centered text
        img = Image.new('RGB', size, color=(random.randint(80, 200), random.randint(80, 200), random.randint(80, 200)))
        draw = ImageDraw.Draw(img)
        # Try to load a default font; fall back to basic
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        text = text[:12]
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (size[0] - w) // 2
        y = (size[1] - h) // 2
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf

