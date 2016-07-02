from django.db import models

from djmoney.models.fields import MoneyField

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from crm.models import Customer

from timeline.models import Entry as TimelineEntry
from hub.exceptions import CannotBeScheduled, CannotBeUnscheduled


class ActiveSubscription(models.Model):
    """
    Represent a single bought subscription
    """
    ENABLED = (
        (0, 'Inactive'),
        (1, 'Active'),
    )
    customer = models.ForeignKey(Customer)

    buy_time = models.DateTimeField(auto_now_add=True)
    buy_price = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')

    active = models.SmallIntegerField(choices=ENABLED, default=1)

    product_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    product_id = models.PositiveIntegerField()
    product = GenericForeignKey('product_type', 'product_id')

    def save(self, *args, **kwargs):
        is_new = True
        if self.pk:
            is_new = False

        if not is_new:  # check, if we should enable\disable lessons
            self.__update_classes()

        super(ActiveSubscription, self).save(*args, **kwargs)

        if is_new:
            self.__add_lessons_to_user()

    def __add_lessons_to_user(self):
        """
        When creating new subscription, we should make included lessons
        available for the customer.
        """
        for lesson_type in self.product.LESSONS:
            for lesson in getattr(self.product, lesson_type).all():
                bought_lesson = Class(
                    lesson=lesson,
                    subscription=self,
                    customer=self.customer,
                    buy_price=self.buy_price
                )
                bought_lesson.save()

    def __update_classes(self):
        """
        When the subscription is disabled for any reasons, all lessons
        assosciated to it, should be disabled too.
        """
        orig = ActiveSubscription.objects.get(pk=self.pk)
        if orig.active != self.active:
            for lesson in self.classes.all():
                lesson.active = self.active
                lesson.save()


class Class(models.Model):
    BUY_SOURCES = (
        (0, 'Single'),
        (1, 'Subscription')
    )
    ENABLED = (
        (0, 'Inactive'),
        (1, 'Active'),
    )

    customer = models.ForeignKey(Customer)

    buy_time = models.DateTimeField(auto_now_add=True)
    buy_price = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    buy_source = models.SmallIntegerField(choices=BUY_SOURCES, default=0)

    active = models.SmallIntegerField(choices=ENABLED, default=1)

    lesson_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    lesson_id = models.PositiveIntegerField()
    lesson = GenericForeignKey('lesson_type', 'lesson_id')

    timeline_entry = models.ForeignKey(TimelineEntry, null=True, blank=True, related_name='classes')

    subscription = models.ForeignKey(ActiveSubscription, on_delete=models.CASCADE, null=True, related_name='classes')

    def __str__(self):
        if self.subscription:
            return "#%d %s by %s for %s" % (self.pk, self.lesson, self.subscription.product, self.customer)
        return "#%d %s for %s" % (self.pk, self.lesson, self.customer)

    def schedule(self, entry):
        """
        Schedule a lesson — assign a timeline entry.
        """
        if not self.can_be_scheduled(entry):
            raise CannotBeScheduled('%s %s' % (self, entry))

        entry.customers.add(self.customer)
        entry.save()

        self.timeline_entry = entry

    def unschedule(self):
        """
        Unschedule previously scheduled lesson
        """
        if not self.timeline_entry:
            raise CannotBeUnscheduled('%s' % self)

        # TODO — check if entry is not completed
        self.timeline_entry.customers.remove(self.customer)
        self.timeline_entry.save()
        self.timeline_entry = None

    @property
    def is_scheduled(self):
        """
        Check if class is scheduled — has an assigned timeline entry and other
        """
        if self.timeline_entry:
            return True

        return False

    def can_be_scheduled(self, entry):
        """
        Check if timeline entry can be scheduled
        """
        if self.is_scheduled:
            return False

        if not entry.is_free:
            return False

        if entry.event_type is not None and self.lesson_type != entry.event_type:
            return False

        return True
