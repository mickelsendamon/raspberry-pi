# from twilio.rest import Client
# from config import settings

# todo text message notifications
# todo modify schedules to handle multiple tasks (i.e. cleaning surfaces every night)
# todo show next in queue tasks on `home.html`
# todo test scheduled tasks:
#   - overdue tasks
#   - notifications
# todo mark chores incomplete
#   todo penalty for accumulating incomplete chores
# todo Not Found: /apple-touch-icon-precomposed.png
# todo Not Found: /favicon.ico
# todo Not Found: /apple-touch-icon.png
# todo Chore Swaps


# Notifications / Messages
def send_text_message(phone_number, body):
    """
    Sends the provided body as a text message to the provided number
    """
    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    # message = client.messages.create(
    #     to = phone_number,
    #     from_ = settings.TWILIO_PHONE_NUMBER,
    #     body = body
    # print(f"""
    #     to=f'{phone_number}',
    #     from_=f'{settings.TWILIO_PHONE_NUMBER}',
    print(body)
    # """
    # )


def chore_overdue_notification_message(chore_title, due_date, user_first_name):
    return f"Hi {user_first_name},\n\nyour chore {chore_title} was due on {due_date.strftime("%b %-d, %Y")} and is now overdue.\nPlease ensure this chore gets completed in the next 24 hours.\nThank you."


def chore_upcoming_notification_message(chore_title, due_date):
    return f"Reminder: {chore_title} is due soon: {due_date.strftime("%b %-d, %Y")}\n\nThank you."


def chore_assigned_notification_message(chore_title, due_date, user_first_name):
    return f"{user_first_name}, you have been assigned {chore_title}. Please complete this by the due date, {due_date.strftime("%b %-d, %Y")}."
