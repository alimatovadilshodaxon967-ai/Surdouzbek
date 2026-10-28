from django.contrib import admin
from .models import SignGesture

@admin.register(SignGesture)
class SignGestureAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'hand_type', 'icon', 'spoken_text', 'finger_pattern', 'is_active')
    list_filter = ('category', 'hand_type', 'is_active')
    search_fields = ('name', 'spoken_text', 'description', 'slug')
    ordering = ('id',)


