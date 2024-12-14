from pymongo import MongoClient
import os
import datetime
import smtplib
import json

def get_env_from_ssm():
    # You'll need to store these in AWS Systems Manager Parameter Store
    return {
        'my_email': os.environ['MY_EMAIL'],
        'my_password': os.environ['MY_PASSWORD'],
        'to_addrs': os.environ['TO_ADDRS'],
        'connection_string': os.environ['MONGODB_CONNECTION_STRING']
    }

def get_today_content(connection_string):
    client = MongoClient(connection_string)
    db = client["learning"]
    collection = db["daily_learnings"]
    
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    
    learning_content = collection.find_one(
        {"learning_date": today},
        {"content_url": 1, "followup_questions": 1, "_id": 0}
    )
    
    if learning_content:
        content_url = learning_content.get("content_url", "")
        followup_questions = learning_content.get("followup_questions", [])
        return content_url, followup_questions
    else:
        return None, None

def send_email(subject, body, env_vars):
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            connection.login(user=env_vars['my_email'], password=env_vars['my_password'])
            connection.sendmail(
                from_addr=env_vars['my_email'],
                to_addrs=env_vars['to_addrs'],
                msg=f"Subject: {subject}\n\n{body}"
            )
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def lambda_handler(event, context):
    env_vars = get_env_from_ssm()
    content_url, followup_questions = get_today_content(env_vars['connection_string'])
    
    response_data = {
        'event_received': event,
        'content_url_found': bool(content_url),
        'followup_questions_found': bool(followup_questions),
        'email_sent': False,
        'message': ''
    }
    
    event_type = event.get('detail-type', '')
    
    if event_type == 'morning_content':
        if content_url:
            subject = "Daily Learning Content"
            body = f"Today's Learning Content URL: {content_url}"
            success = send_email(subject, body, env_vars)
            response_data.update({
                'email_sent': success,
                'message': 'Morning content email sent successfully' if success else 'Failed to send morning content email',
                'content_url': content_url
            })
        else:
            response_data['message'] = 'No content URL found for today'
    
    elif event_type == 'evening_questions':
        if followup_questions:
            subject = "Daily Learning Follow-up Questions"
            body = "Today's Follow-up Questions:\n"
            for i, q in enumerate(followup_questions, 1):
                body += f"{i}. {q['question']}\n"
            success = send_email(subject, body, env_vars)
            response_data.update({
                'email_sent': success,
                'message': 'Evening questions email sent successfully' if success else 'Failed to send evening questions email',
                'questions_count': len(followup_questions)
            })
        else:
            response_data['message'] = 'No follow-up questions found for today'
    else:
        response_data['message'] = f'Unknown event type: {event_type}'
    
    return {
        'statusCode': 200 if response_data['email_sent'] else 500,
        'body': json.dumps(response_data, default=str)
    }
