from elk.celery import app as celery
from market.models import Subscription
from market.signals import subscription_passed_more_one_week
from notifications.models import Notification


@celery.task
def notify_passed_more_one_week():
    subscribes = Subscription.objects.notify_passed_more_n_week(weeks=1)
    notifications = [
        Notification(
            receiver=subscribe.customer,
            type_notify=Notification.EVENT_TYPE_PASSED_MORE_ONE_WEEK,
            data={'subscription_id': subscribe.id}
        ) for subscribe in subscribes
    ]
    Notification.objects.bulk_create(notifications)

    for notification in Notification.objects.passed_more_one_week():
        subscribe = Subscription.objects.get(id=notification.data['subscription_id'])
        notification.inc_count_attempts()
        subscription_passed_more_one_week.send(sender=notification, instance=subscribe, notification=notification)
