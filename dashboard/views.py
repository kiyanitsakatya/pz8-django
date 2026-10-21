from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate

from accounts.models import Department, Course, AcademicGroup, StudentProfile


def _parse_date(request, key):
    """Вспомогательная функция: парсит дату из GET-параметра."""
    val = request.GET.get(key)
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError:
        return None

#ДАШБОРД1"ПОЛЬЗОВАТЕЛИ"
def dashboard_users(request):
    date_from = _parse_date(request, "date_from")
    date_to   = _parse_date(request, "date_to")

    qs = User.objects.all()
    if date_from:
        qs = qs.filter(date_joined__date__gte=date_from)
    if date_to:
        qs = qs.filter(date_joined__date__lte=date_to)

    # KPI
    total         = qs.count()
    active        = qs.filter(is_active=True).count()
    staff         = qs.filter(is_staff=True).count()
    superusers    = qs.filter(is_superuser=True).count()
    never_logged  = qs.filter(last_login__isnull=True).count()
    week_ago      = datetime.now() - timedelta(days=7)
    new_last_week = qs.filter(date_joined__gte=week_ago).count()

    # График: регистрации по дням
    start = date_from or (datetime.now().date() - timedelta(days=30))
    regs = (
        User.objects.filter(date_joined__date__gte=start)
        .annotate(day=TruncDate("date_joined"))
        .values("day").annotate(c=Count("id")).order_by("day")
    )
    reg_labels = [r["day"].strftime("%d.%m") for r in regs]
    reg_data   = [r["c"] for r in regs]

    # Топ-5 последних
    latest_users = qs.order_by("-date_joined")[:5]

    context = {
        "page_title": "Дашборд пользователей",
        "total": total, "active": active, "staff": staff,
        "superusers": superusers, "never_logged": never_logged,
        "new_last_week": new_last_week,
        "chart_labels": reg_labels,
        "chart_series": [{"name": "Регистрации", "data": reg_data}],
        "latest_users": latest_users,
    }
    return render(request, "dashboard/users_dashboard.html", context)


#ДАШБОРД 2"КУРСЫ"

def dashboard_courses(request):

    dept_id = request.GET.get("department")
    dept_filter = None
    if dept_id and dept_id.isdigit():
        dept_filter = int(dept_id)

    courses = Course.objects.all()
    departments = Department.objects.all()

    if dept_filter:
        courses = courses.filter(department_id=dept_filter)

    total_courses     = courses.count()
    total_departments = departments.count()
    total_groups      = AcademicGroup.objects.count()
    total_students    = StudentProfile.objects.count()

    # Топ-5 популярных курсов
    top_courses = (
        Course.objects.annotate(students_count=Count("students"))
        .order_by("-students_count")[:5]
    )

    # График 1: курсы по кафедрам
    by_dept = (
        Department.objects.annotate(c=Count("courses"))
        .values("name", "c").order_by("-c")
    )
    pie_labels = [d["name"] for d in by_dept]
    pie_data   = [d["c"] for d in by_dept]

    # График 2 : студенты по кафедрам
    students_by_dept = (
        Department.objects.annotate(c=Count("students"))
        .values("name", "c").order_by("-c")
    )
    bar_labels = [d["name"] for d in students_by_dept]
    bar_data   = [d["c"] for d in students_by_dept]

    context = {
        "page_title": "Дашборд курсов",
        "total_courses": total_courses,
        "total_departments": total_departments,
        "total_groups": total_groups,
        "total_students": total_students,
        "departments": departments,
        "current_department": dept_filter,
        "top_courses": top_courses,
        # График 1
        "pie_labels": pie_labels,
        "pie_series": [{"name": "Курсы", "data": pie_data}],
        # График 2
        "chart_labels": bar_labels,
        "chart_series": [{"name": "Студенты", "data": bar_data}],
    }
    return render(request, "dashboard/courses_dashboard.html", context)


# ДАШБОРД 3"АКТИВНОСТЬ"

def dashboard_activity(request):

    dept_id = request.GET.get("department")
    dept_filter = None
    if dept_id and dept_id.isdigit():
        dept_filter = int(dept_id)

    profiles = StudentProfile.objects.all()
    if dept_filter:
        profiles = profiles.filter(department_id=dept_filter)

    # KPI
    total_students   = profiles.count()
    active_students  = profiles.filter(user__is_active=True).count()
    with_group       = profiles.filter(academic_group__isnull=False).count()
    without_group    = profiles.filter(academic_group__isnull=True).count()

    # График 1:
    last_week = datetime.now() - timedelta(days=7)
    activity = (
        User.objects.filter(last_login__gte=last_week)
        .annotate(day=TruncDate("last_login"))
        .values("day").annotate(c=Count("id")).order_by("day")
    )
    activity_labels = [r["day"].strftime("%d.%m") for r in activity]
    activity_data   = [r["c"] for r in activity]

    # График 2
    by_group = (
        AcademicGroup.objects.annotate(c=Count("students"))
        .filter(c__gt=0)
        .values("name", "c").order_by("-c")
    )
    if by_group:
        pie_title  = "Студенты по группам"
        group_labels = [g["name"] for g in by_group]
        group_data   = [g["c"] for g in by_group]
    else:
        pie_title = "Студенты по кафедрам"
        by_dept = (
            Department.objects.annotate(c=Count("students"))
            .filter(c__gt=0)
            .values("name", "c").order_by("-c")
        )
        group_labels = [d["name"] for d in by_dept]
        group_data   = [d["c"] for d in by_dept]

    # Если вообще нет данных — показываем «Без группы»
    if not group_data:
        pie_title = "Распределение студентов"
        group_labels = ["Без группы"]
        group_data   = [total_students]
    # Таблица: последние входы
    latest_logins = (
        User.objects.filter(last_login__isnull=False)
        .order_by("-last_login")[:5]
    )

    context = {
        "page_title": "Дашборд активности",
        "total_students": total_students,
        "active_students": active_students,
        "with_group": with_group,
        "without_group": without_group,
        "departments": Department.objects.all(),
        "current_department": dept_filter,
        # График 1
        "chart_labels": activity_labels,
        "chart_series": [{"name": "Входы", "data": activity_data}],
        # График 2
        "pie_labels": group_labels,
        "pie_series": [{"name": "Студенты", "data": group_data}],
        # Таблица
        "latest_logins": latest_logins,
    }
    return render(request, "dashboard/activity_dashboard.html", context)