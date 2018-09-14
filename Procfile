web: source bin/guni.sh
sb: python3 soundboardsite/manage.py soundboard
celery: celery worker -l DEBUG --app=soundboardsite.control.cogs.reminder.app