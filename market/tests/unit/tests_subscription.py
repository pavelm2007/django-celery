from datetime import timedelta
from unittest.mock import patch

from freezegun import freeze_time
from mixer.backend.django import mixer

from elk.utils.testing import TestCase, create_customer, create_teacher
from lessons import models as lessons
from market.models import Subscription
from products.models import Product1
from timeline.models import Entry as TimelineEntry


@freeze_time('2032-12-01 12:00')
class TestSubscriptionUnit(TestCase):
    fixtures = ('products', 'lessons')

    @classmethod
    def setUpTestData(cls):
        cls.product = Product1.objects.get(pk=1)
        cls.product.duration = timedelta(days=5)
        cls.product.save()

        cls.customer = create_customer()

    def setUp(self):
        self.s = Subscription(
            customer=self.customer,
            product=self.product,
            buy_price=150
        )
        self.s.save()

    @patch('market.models.signals.class_scheduled.send')
    def _schedule(self, c, date, *args):
        c.timeline = mixer.blend(
            'timeline.Entry',
            lesson_type=c.lesson_type,
            teacher=create_teacher(),
            start=date,
        )
        c.save()

    def test_is_due(self):
        self.s.first_lesson_date = self.tzdatetime(2032, 12, 2, 12, 0)
        self.s.save()
        self.assertFalse(self.s.is_due())
        with freeze_time('2032-12-10 12:00'):  # move 9 days forward
            self.assertTrue(self.s.is_due())

    def test_is_due_for_subscription_without_any_completed_class(self):
        """
        For subscription without classes is_due should be based on their buy_date
        """
        self.assertFalse(self.s.is_due())
        with freeze_time('2032-12-10 12:00'):  # move 9 days forward
            self.assertTrue(self.s.is_due())

    def test_update_first_lesson_date(self):
        first_class = self.s.classes.first()

        self._schedule(first_class, self.tzdatetime(2032, 12, 5, 13, 33))

        self.s.first_lesson_date = None  # set to None in case of first_class has set it up manualy — we check the subscription, not the class logic

        self.s.update_first_lesson_date()
        self.s.refresh_from_db()
        self.assertEqual(self.s.first_lesson_date, self.tzdatetime(2032, 12, 5, 13, 33))

    def test_update_first_lesson_uses_only_first_lesson(self):
        classes = self.s.classes.all()
        self._schedule(classes[0], self.tzdatetime(2032, 12, 5, 13, 33))
        self._schedule(classes[1], self.tzdatetime(2033, 12, 5, 13, 33))

        self.s.update_first_lesson_date()
        self.s.refresh_from_db()
        self.assertEqual(self.s.first_lesson_date, self.tzdatetime(2032, 12, 5, 13, 33))  # should be taken from the first class, not from the second


@freeze_time('2032-12-01 12:00')
class TestSubscriptionNotificationUnit(TestCase):
    fixtures = ('products', 'lessons')

    @classmethod
    def setUpTestData(cls):
        cls.product = Product1.objects.get(pk=1)
        cls.product.duration = timedelta(days=7 * 6)
        cls.product.save()

        cls.customer = create_customer()
        cls.teacher1 = create_teacher(works_24x7=True)

    def setUp(self):
        with freeze_time('2032-12-01 12:00'):
            self.s1 = Subscription(
                customer=self.customer,
                product=self.product,
            )
            self.s1.save()

        c = self.s1.classes.first()
        lesson = mixer.blend(lessons.OrdinaryLesson)
        entry = mixer.blend(TimelineEntry, lesson=lesson, teacher=self.teacher1,
                            start=self.tzdatetime(2032, 12, 2, 12, 0), stop=self.tzdatetime(2032, 12, 2, 14, 0),
                            is_finished=True)
        c.timeline = entry
        c.save()

    def test_subscription_one(self):
        # week has passed, get one entry
        with freeze_time('2032-12-10 12:00'):
            ss = Subscription.objects.notify_passed_more_n_week(weeks=1)
            self.assertEqual(ss.count(), 1)

    def test_subscription_less_one_week(self):
        # less than a week has passed, we do not receive a record
        with freeze_time('2032-12-8 17:00'):
            ss = Subscription.objects.notify_passed_more_n_week(weeks=1)
            self.assertEqual(ss.count(), 0)

    def test_subscription_more_duration(self):
        # subscription expired, no entries received
        with freeze_time('2033-2-9 17:00'):
            ss = Subscription.objects.notify_passed_more_n_week(weeks=1)
            self.assertEqual(ss.count(), 0)
