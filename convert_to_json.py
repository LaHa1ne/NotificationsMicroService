def notifications_to_json(notifications):
    notification_list=[]
    for notification in notifications:
        notification_list.append({'id_notification':notification.id_notification,'header':notification.header,'text':notification.text})
    return notification_list
