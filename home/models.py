from django.db import models

class SignGesture(models.Model):
    CATEGORY_CHOICES = [
        ('Daktil', 'Daktil Alifbosi'),
        ('Raqamlar', 'Raqamlar'),
        ('Salomlashish', 'Salomlashish & Odob'),
        ('Tasdiq / Inkor', 'Tasdiqlash & Inkor'),
        ('Savollar', 'Savollar'),
        ('His-tuyg\'ular', 'His-tuyg\'ular'),
        ('Zaruratlar', 'Zaruratlar & Taom'),
        ('Buyruqlar', 'Harakatlar & Buyruqlar'),
        ('Favqulodda SOS', 'Favqulodda SOS'),
        ('Oila & Insonlar', 'Oila & Insonlar'),
        ('Vaqt & Kunlar', 'Vaqt & Kunlar'),
        ('Joylar & Transport', 'Joylar & Transport'),
        ('Taomlar & Mevalar', 'Taomlar & Mevalar'),
        ('Kundalik Muloqot', 'Kundalik Muloqot & Suhbat'),
        ('Tabiat & Ob-havo', 'Tabiat & Ob-havo'),
        ('Sifatlar & Holatlar', 'Sifatlar & Holatlar'),
    ]

    slug = models.SlugField(max_length=64, unique=True, verbose_name="Ishora kodi")
    name = models.CharField(max_length=128, verbose_name="Ishora nomi")
    category = models.CharField(max_length=64, choices=CATEGORY_CHOICES, verbose_name="Toifasi")
    hand_type = models.CharField(max_length=32, default="1 Qo'l", verbose_name="Qo'l turi")
    icon = models.CharField(max_length=16, default="✋", verbose_name="Qo'l belgisi / Ikonka")
    spoken_text = models.CharField(max_length=256, verbose_name="Ovozli matn")
    description = models.TextField(verbose_name="Qo'l harakati tavsifi")
    audio_key = models.CharField(max_length=64, blank=True, null=True, verbose_name="Audio fayl kodi")
    
    # Fazoviy geometrik barmoq imzosi (Pattern / Finger Signature: masalan 1,1,1,1,1)
    finger_pattern = models.CharField(
        max_length=64, 
        blank=True, 
        default="", 
        verbose_name="Barmoq holati imzosi (T,I,M,R,P)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Imo-ishora"
        verbose_name_plural = "Imo-ishoralar bazasi"
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.category})"

