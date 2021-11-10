from django.contrib.postgres.fields import JSONField
from django.db import models


class NotificationManager(models.Manager):
    def passed_more_one_week(self):
        """
        Receive unsent notifications with type EVENT_TYPE_PASSED_MORE_ONE_WEEK.
        """
        return self.get_queryset().filter(
            is_sent=False,
            type_notify=Notification.EVENT_TYPE_PASSED_MORE_ONE_WEEK,
            count_attempts__lt=Notification.MAX_ATTEMPTS,
            data__subscription_id__isnull=False
        )


class Notification(models.Model):
    """
    Represents notification.

    The date field stores extended notification data.
    In the future, this will make it easy to create notifications for different objects.
    Now implemented notifications for students who have subscribed and have not taken classes for more than 1 week.

    Tasks for send notifications in notifications.tasks
    """
    MAX_ATTEMPTS = 3
    EVENT_TYPE_PASSED_MORE_ONE_WEEK = 0
    EVENT_TYPES = (
        (EVENT_TYPE_PASSED_MORE_ONE_WEEK, 'More than a week has passed since the last lesson'),
    )
    objects = NotificationManager()
    receiver = models.ForeignKey('crm.Customer', verbose_name='Receiver', related_name='notifications', db_index=True)
    type_notify = models.PositiveIntegerField('Type of notification', choices=EVENT_TYPES)
    is_sent = models.BooleanField('Is sent', default=False)
    data = JSONField('Data', default=dict)
    count_attempts = models.PositiveIntegerField('Count of attempts', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f'{self.id}__{self.receiver}'

    def mark_as_sent(self):
        """
        Mark notification as sent.
        """
        self.is_sent = True
        self.save()

    def inc_count_attempts(self):
        """
        Increase the counter of attempts to send a notification
        """
        self.count_attempts += 1
        self.save()
