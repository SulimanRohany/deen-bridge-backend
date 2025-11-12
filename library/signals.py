"""
Signals for library app
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ResourceRating


@receiver(post_save, sender=ResourceRating)
def update_resource_rating_on_save(sender, instance, **kwargs):
    """Update resource average rating when a rating is saved"""
    instance.resource.update_rating()


@receiver(post_delete, sender=ResourceRating)
def update_resource_rating_on_delete(sender, instance, **kwargs):
    """Update resource average rating when a rating is deleted"""
    instance.resource.update_rating()

