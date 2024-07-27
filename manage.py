#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from company.CompanyShow import *

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stock_beacon.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    # 初始化开市时间列表
    start_date = dt.strptime('1997-12-01', '%Y-%m-%d').date()
    index = CompanyProfile(code='000001', is_index=True)
    index.update_all(start_date)
    market_open_days_init('daily')
    market_open_days_init('weekly')
    main()
