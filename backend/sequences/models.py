from django.db.models import CharField, Model, PositiveIntegerField


# Create your models here.
class Sequence(Model):
    sequence = CharField(max_length=255, unique=True)
    order = PositiveIntegerField()
