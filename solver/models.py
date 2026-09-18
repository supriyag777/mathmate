from django.db import models

class MathQuery(models.Model):
    problem = models.CharField(max_length=255)
    formula = models.TextField(blank=True, null=True)
    solution = models.TextField(blank=True, null=True)
    answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.problem} = {self.answer}"