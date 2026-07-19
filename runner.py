import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'ats.settings'
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000', '--noreload'])
