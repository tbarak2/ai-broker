from django.contrib.auth.models import User
from django.db import models


class TOTPSecret(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="totp_secret")
    secret = models.CharField(max_length=64)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "active" if self.is_active else "pending"
        return f"TOTP({self.user.username}, {status})"
