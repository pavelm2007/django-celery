from datetime import timedelta

from django.core import mail
from django.db.models import Q
from freezegun import freeze_time
from mixer.backend.django import mixer

from elk.utils.testing import TestCase, create_customer, create_teacher
from market.models import Subscription
from notifications.models import Notification
from notifications.tasks import notify_passed_more_one_week
from products.models import Product1
from lessons import models as lessons
from timeline.models import Entry as TimelineEntry


@freeze_time('2032-12-01 12:00')
class TestNotificationUnit(TestCase):
    fixtures = ('products', 'lessons')

    @classmethod
    def setUpTestData(cls):
        cls.product = Product1.objects.get(pk=1)
        cls.product.duration = timedelta(days=7*6)
        cls.product.save()

        cls.customer1 = create_customer()
        cls.customer2 = create_customer()

    def setUp(self):
        self.teacher1 = create_teacher(works_24x7=True)
        self.s1 = Subscription(
            customer=self.customer1,
            product=self.product,
            buy_price=150
        )
        self.s1.save()

        c = self.s1.classes.first()
        lesson = mixer.blend(lessons.OrdinaryLesson)
        entry = mixer.blend(TimelineEntry, lesson=lesson, teacher=self.teacher1,
                            start=self.tzdatetime(2032, 12, 2, 12, 0), stop=self.tzdatetime(2032, 12, 2, 14, 0),
                            is_finished=True)
        c.timeline = entry
        c.save()

        self.s2 = Subscription(
            customer=self.customer2,
            product=self.product,
            buy_price=150
        )
        self.s2.save()

        c = self.s2.classes.first()
        entry = mixer.blend(TimelineEntry, lesson=lesson, teacher=self.teacher1,
                            start=self.tzdatetime(2032, 12, 7, 12, 0), stop=self.tzdatetime(2032, 12, 7, 14, 0),
                            is_finished=True)
        c.timeline = entry
        c.save()

    def test_notification_sent(self):
        with freeze_time('2032-12-10 12:00'):
            notify_passed_more_one_week()
            notifications = Notification.objects.filter(data__subscription_id=self.s1.id)
            notification = notifications.first()
            self.assertEqual(notification.data['subscription_id'], self.s1.id)

            email = mail.outbox[0]
            self.assertEqual(email.to, [self.s1.customer.email])

    def test_notification_sent_only_actual(self):
        # week has passed, can send a notification
        with freeze_time('2032-12-10 14:01'):
            notify_passed_more_one_week()

            notifications = Notification.objects.all()
            self.assertEqual(notifications.count(), 1)
            notifications = Notification.objects.filter(data__subscription_id=self.s1.id)
            self.assertEqual(notifications.count(), 1)

        # time elapsed notification resubmitted for the first subscription and for the first time for the second
        with freeze_time('2032-12-17 14:01'):
            notify_passed_more_one_week()
            notifications = Notification.objects.filter(data__subscription_id=self.s1.id)
            self.assertEqual(notifications.count(), 2)

            notifications = Notification.objects.filter(data__subscription_id=self.s2.id)
            self.assertEqual(notifications.count(), 1)

            notification = Notification.objects.filter(data__subscription_id=self.s2.id).first()
            self.assertEqual(notification.data['subscription_id'], self.s2.id)
            self.assertTrue(notification.is_sent)

            notifications = Notification.objects.all()
            self.assertEqual(notifications.count(), 3)

    def test_notification_not_send(self):
        # not enough time has passed, notifications cannot be sent
        with freeze_time('2032-12-05 14:01'):
            notify_passed_more_one_week()
            notifications = Notification.objects.filter(Q(receiver=self.customer1) | Q(receiver=self.customer2))
            self.assertEqual(notifications.count(), 0)
