import firebase_admin
from firebase_admin import credentials, messaging
import os

# Initialize Firebase Admin SDK
# This block runs when the module is imported.
try:
    # Check if the default Firebase app is already initialized.
    # firebase_admin._apps is a dictionary of initialized Firebase apps.
    # If it's empty, no app is initialized.
    if not firebase_admin._apps:
        SERVICE_ACCOUNT_KEY_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if SERVICE_ACCOUNT_KEY_PATH:
            # Attempt to initialize with the provided credentials
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(cred)
            print("INFO: Firebase Admin SDK initialized successfully by fcm.py.")
        else:
            # Credentials environment variable not set
            print("WARNING: GOOGLE_APPLICATION_CREDENTIALS environment variable not set. Firebase Admin SDK not initialized by fcm.py.")
    else:
        # An app (likely the default '[DEFAULT]') was already initialized.
        # This can happen if another part of the application initialized it first.
        # We assume it's correctly configured for FCM use.
        print("INFO: Firebase Admin SDK was already initialized. fcm.py will use the existing instance.")
except Exception as e:
    # This catches errors from credentials.Certificate(), firebase_admin.initialize_app(),
    # or if SERVICE_ACCOUNT_KEY_PATH is set but points to an invalid/inaccessible file.
    print(f"ERROR: Failed to initialize Firebase Admin SDK in fcm.py: {e}")
    # If initialization fails, firebase_admin._apps will reflect that (e.g., still be empty
    # or not contain the default app). The functions below, which check firebase_admin._apps,
    # will then correctly report that the SDK is not initialized and will not attempt to use it.

def send_fcm_message(registration_token, title, body, data=None):
    """
    Sends an FCM message to a specific device.

    Args:
        registration_token (str): The FCM registration token of the target device.
        title (str): The title of the notification.
        body (str): The body of the notification.
        data (dict, optional): A dictionary of data to send with the message.
    Returns:
        str: The message ID if successful, None otherwise.
    """
    if not firebase_admin._apps:
        print("Firebase Admin SDK not initialized. Cannot send FCM message.")
        return None

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        token=registration_token,
    )

    try:
        response = messaging.send(message)
        print('Successfully sent message:', response)
        return response
    except Exception as e:
        print('Error sending message:', e)
        return None

def send_fcm_multicast_message(registration_tokens, title, body, data=None):
    """
    Sends an FCM message to multiple devices.

    Args:
        registration_tokens (list): A list of FCM registration tokens.
        title (str): The title of the notification.
        body (str): The body of the notification.
        data (dict, optional): A dictionary of data to send with the message.
    Returns:
        messaging.BatchResponse: The response from sending the multicast message.
    """
    if not firebase_admin._apps:
        print("Firebase Admin SDK not initialized. Cannot send FCM message.")
        return None

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        tokens=registration_tokens,
    )

    try:
        response = messaging.send_multicast(message)
        print('Successfully sent multicast message:', response)
        return response
    except Exception as e:
        print('Error sending multicast message:', e)
        return None

def subscribe_to_topic(registration_tokens, topic_name):
    """
    Subscribes a list of devices to an FCM topic.

    Args:
        registration_tokens (list): A list of FCM registration tokens.
        topic_name (str): The name of the topic to subscribe to.
    Returns:
        messaging.TopicManagementResponse: The response from the topic subscription.
    """
    if not firebase_admin._apps:
        print("Firebase Admin SDK not initialized. Cannot subscribe to topic.")
        return None
    try:
        response = messaging.subscribe_to_topic(registration_tokens, topic_name)
        print('Successfully subscribed to topic:', response)
        return response
    except Exception as e:
        print('Error subscribing to topic:', e)
        return None

def unsubscribe_from_topic(registration_tokens, topic_name):
    """
    Unsubscribes a list of devices from an FCM topic.

    Args:
        registration_tokens (list): A list of FCM registration tokens.
        topic_name (str): The name of the topic to unsubscribe from.
    Returns:
        messaging.TopicManagementResponse: The response from the topic unsubscription.
    """
    if not firebase_admin._apps:
        print("Firebase Admin SDK not initialized. Cannot unsubscribe from topic.")
        return None
    try:
        response = messaging.unsubscribe_from_topic(registration_tokens, topic_name)
        print('Successfully unsubscribed from topic:', response)
        return response
    except Exception as e:
        print('Error unsubscribing from topic:', e)
        return None

def send_fcm_topic_message(topic_name, title, body, data=None):
    """
    Sends an FCM message to a specific topic.

    Args:
        topic_name (str): The name of the topic.
        title (str): The title of the notification.
        body (str): The body of the notification.
        data (dict, optional): A dictionary of data to send with the message.
    Returns:
        str: The message ID if successful, None otherwise.
    """
    if not firebase_admin._apps:
        print("Firebase Admin SDK not initialized. Cannot send FCM topic message.")
        return None

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        topic=topic_name,
    )

    try:
        response = messaging.send(message)
        print('Successfully sent topic message:', response)
        return response
    except Exception as e:
        print('Error sending topic message:', e)
        return None
