from django.db import models

class Medicine(models.Model):
    uid = models.CharField(max_length=255, unique=True, help_text="Unique Identifier from QR/Barcode")
    name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200)
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    manufacture_date = models.DateField()

    def __str__(self):
        return f"{self.name} (Batch: {self.batch_number})"

    class Meta:
        verbose_name = "Medicine"
        verbose_name_plural = "Medicines"
