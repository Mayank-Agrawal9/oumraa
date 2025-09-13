import datetime

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from account.helpers import send_templated_mail
from account.models import NewsletterCampaign, NewsletterSubscriber
from oumraa import settings


@shared_task
def send_contact_email_task(name, email, phone_number, subject, message):
    send_templated_mail(
        subject="Thanks for contacting us!",
        template_name="emails/contact_user.html",
        context={"name": name, "phone_number": phone_number, "subject": subject, "message": message},
        to_email=email,
    )

    send_templated_mail(
        subject=f"New Contact Request from {name}",
        template_name="emails/contact_admin.html",
        context={"name": name, "email": email, "phone_number": phone_number, "subject": subject, "message": message},
        to_email=settings.ADMIN_EMAIL,
    )


@shared_task
def send_instant_email(subject, email_to, template, context):
    send_templated_mail(
        subject=subject, template_name=template, context=context, to_email=email_to,
    )


@shared_task
def send_newsletter_joining_mail(email):
    send_templated_mail(
        subject="Thank you for subscribing Oumraa newsletter!",
        template_name="emails/joining_newsletter.html",
        context={"email": email}, to_email=email,
    )


@shared_task
def send_newsletter_schedular_mail():
    campaigns = NewsletterCampaign.objects.filter(sent=False, scheduled_at__lte=datetime.datetime.now())

    for campaign in campaigns:
        subscribers = NewsletterSubscriber.objects.filter(is_active=True)

        for subscriber in subscribers:
            context = {"name": "Subscriber", "body": campaign.body, "subject": campaign.subject}
            html_content = render_to_string("emails/newsletter.html", context)

            msg = EmailMultiAlternatives(
                subject=campaign.subject, body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL, to=[subscriber.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        campaign.sent = True
        campaign.save()