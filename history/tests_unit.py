from elk.utils.testing import TestCase, create_customer, mock_request
from history.models import PaymentEvent
from lessons.models import OrdinaryLesson
from market.models import Class, Subscription
from products.models import Product1 as product


class TestEvent(TestCase):
    fixtures = ('crm', 'products', 'lessons')
    TEST_PRODUCT_ID = 1

    def test_storing_request(self):
        """
        Unit test for populating log entry model with request.
        """
        mocked_request = mock_request()
        ev = PaymentEvent()
        ev._HistoryEvent__store_request(mocked_request)

        # Assertions are based on fixtures, generated by elk.utils.testing.mock_request
        self.assertEqual(ev.is_mobile, mocked_request.user_agent.is_mobile)
        self.assertEqual(ev.is_tablet, mocked_request.user_agent.is_tablet)
        self.assertEqual(ev.is_pc, mocked_request.user_agent.is_pc)

        self.assertEqual(ev.browser_family, 'Mobile Safari')
        self.assertEqual(ev.browser_version, '5.2')
        self.assertEqual(ev.os_family, 'WinXP')
        self.assertEqual(ev.os_version, '5.3')
        self.assertEqual(ev.device, 'iPhone')

        self.assertEqual(ev.raw_useragent, 'WinXP; U/16')
        self.assertEqual(ev.ip, '127.0.0.5')

    def test_single_lesson_log_entry_creation(self):
        """
        Buy a single lesson and find a respective log entry for it
        """
        customer = create_customer()
        self.assertEqual(customer.payment_events.count(), 0)

        c = Class(
            customer=customer,
            lesson=OrdinaryLesson.get_default(),
            buy_price=10,
            buy_source='single',
        )
        c.request = mock_request()
        c.save()

        self.assertEqual(customer.payment_events.count(), 1)
        self.assertEqual(customer.payment_events.all()[0].product, c)

    def test_subscription_log_entry_creation(self):
        """
        Buy a subscription and find a respective log entry for it
        """
        customer = create_customer()
        self.assertEqual(customer.payment_events.count(), 0)

        s = Subscription(
            customer=customer,
            product=product.objects.get(pk=self.TEST_PRODUCT_ID),
            buy_price=150,
        )
        s.request = mock_request(customer=customer)
        s.save()

        self.assertEqual(customer.payment_events.count(), 1, 'Check if only one log record appeared: for the subscription, not for classes')
        self.assertEqual(customer.payment_events.all()[0].product, s)
