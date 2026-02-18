from django.core.paginator import Paginator
from django.db.models import ExpressionWrapper, F, IntegerField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.accounts.models import Profile
from apps.discussions.models import Comment, Post, Subject


INFO_PAGES = {
    "mission": {
        "title": "Нашата мисия",
        "sections": [
            {
                "id": "intro",
                "title": "Какво правим",
                "paragraphs": [
                    "„Знай повече“ е общностна платформа, която съчетава форум за въпроси и отговори, механизъм за гласове и репутация и маркетплейс за уроци. Целта ни е ученето да бъде по-достъпно, а качествените отговори и полезните преподаватели да се откриват по-лесно.",
                ],
            },
            {
                "id": "benefits",
                "title": "Защо е полезно",
                "points": [
                    {
                        "title": "Взаимопомощ по предмети",
                        "text": "Задаваш въпрос по конкретен предмет и получаваш решения, насоки и обяснения от общността.",
                    },
                    {
                        "title": "По-ефективно учене",
                        "text": "Системата за гласове и репутация откроява най-полезните отговори, за да стигаш по-бързо до вярната информация.",
                    },
                    {
                        "title": "Уроци по предмети",
                        "text": "В маркетплейса има обяви с цена на час, а контактите са видими само за влезли потребители.",
                    },
                ],
            },
            {
                "id": "vision",
                "title": "Нашият фокус",
                "paragraphs": [
                    "Развиваме платформа с ясни правила, активно модериране и инструменти срещу злоупотреби. За нас най-важни са безопасната среда, практическата стойност на съдържанието и устойчивото изграждане на доверие между хората в общността.",
                ],
            },
        ],
    },
    "terms": {
        "title": "Общи условия",
        "sections": [
            {
                "id": "service",
                "title": "Какво представлява услугата",
                "paragraphs": [
                    "„Знай повече“ предоставя форум за учебни въпроси, коментари и гласуване, както и маркетплейс за обяви за уроци. Платформата има образователна и общностна цел и може да се развива поетапно според нуждите на потребителите.",
                ],
            },
            {
                "id": "account",
                "title": "Акаунт и достъп",
                "paragraphs": [
                    "За публикуване и взаимодействие е нужен профил. Потребителят отговаря за сигурността на своя акаунт и за действията, извършени през него. При съмнение за злоупотреба достъпът може временно да бъде ограничен.",
                ],
            },
            {
                "id": "content",
                "title": "Потребителско съдържание",
                "paragraphs": [
                    "Всеки носи отговорност за съдържанието, което публикува – въпроси, отговори, коментари, снимки и обяви. Качвай само материали, които имаш право да споделяш, и не публикувай подвеждаща или незаконна информация.",
                ],
            },
            {
                "id": "behavior",
                "title": "Правила за поведение",
                "paragraphs": [
                    "Забранени са обиди, тормоз, дискриминация, спам и опити за измама. Очакваме уважителен тон и конструктивна комуникация, особено при учебни дискусии и договаряне на уроци.",
                ],
            },
            {
                "id": "moderation",
                "title": "Модерация и репорти",
                "paragraphs": [
                    "Сигнали за нередности могат да се подават чрез наличните инструменти за репорт. Екипът по модерация преглежда съдържанието и при нужда може да го скрие, редактира или премахне, както и да предприеме мерки към съответния акаунт.",
                ],
            },
            {
                "id": "marketplace",
                "title": "Маркетплейс (обяви)",
                "paragraphs": [
                    "Обявите за уроци са публикувани от потребители и условията по провеждането им се договарят между страните. Платформата не е страна по тези договорки, а предоставя място за свързване и обмен на информация.",
                ],
            },
            {
                "id": "liability",
                "title": "Ограничение на отговорност",
                "paragraphs": [
                    "Полагаме разумни усилия за надеждна работа и безопасност, но не гарантираме непрекъсваем достъп или пълна липса на грешки. Не носим отговорност за преки договорки между потребители или за съдържание, публикувано от трети лица.",
                ],
            },
            {
                "id": "changes",
                "title": "Промени в условията",
                "paragraphs": [
                    "Възможно е условията да бъдат актуализирани при развитие на услугата или нормативни изисквания. При съществени промени публикуваме обновена версия на тази страница с актуална информация.",
                ],
            },
        ],
    },
    "privacy": {
        "title": "Политика за поверителност",
        "sections": [
            {
                "id": "data",
                "title": "Какви данни събираме",
                "paragraphs": [
                    "Съхраняваме потребителско име и идентификатор на акаунт, публикувано съдържание (постове, коментари, снимки), действия в платформата (гласове и репорти) и ограничени технически логове като IP адрес за сигурност. Не събираме и не изискваме имейл адрес за използване на основните функции.",
                ],
            },
            {
                "id": "purpose",
                "title": "Защо ги използваме",
                "paragraphs": [
                    "Данните се използват за управление на акаунти, публикуване и показване на съдържание, функциониране на гласуване и репутация, както и за защита от злоупотреби, спам и неоторизиран достъп.",
                ],
            },
            {
                "id": "storage",
                "title": "Къде се съхраняват / споделяне",
                "paragraphs": [
                    "Данните се пазят в инфраструктурата на платформата и при доставчик за хостинг само доколкото е необходимо за техническа поддръжка. Не продаваме лични данни и не ги споделяме за маркетингови цели.",
                ],
            },
            {
                "id": "retention",
                "title": "Колко време се пазят",
                "paragraphs": [
                    "Пазим данните за периода, необходим за работа на услугата, сигурност и спазване на приложими изисквания. При изтриване или ограничаване на акаунт част от данните може да се съхраняват минимално за защита на платформата и разрешаване на спорове.",
                ],
            },
            {
                "id": "rights",
                "title": "Твоите права",
                "paragraphs": [
                    "Можеш да поискаш преглед, корекция или изтриване на информацията в рамките на възможностите на системата и приложимото право. При въпроси относно поверителността можеш да се свържеш с администраторите на платформата чрез наличните канали в сайта.",
                ],
            },
            {
                "id": "cookies",
                "title": "Бисквитки",
                "paragraphs": [
                    "Използваме само необходими бисквитки за работата на сайта: сесийна бисквитка за вход и бисквитка за CSRF защита при форми. Не използваме аналитични или маркетингови бисквитки.",
                    "Ако изключиш бисквитките в браузъра, е възможно входът и публикуването на съдържание да не работят коректно.",
                ],
            },
        ],
    },
}


@ensure_csrf_cookie
def home(request):
    return render(request, "common/home.html")


@ensure_csrf_cookie
def leaderboard(request):
    scope = request.GET.get("scope", "global")
    if scope not in {"global", "subject"}:
        scope = "global"

    subject_slug = request.GET.get("subject", "")
    selected_subject = None

    if scope == "subject":
        if subject_slug:
            selected_subject = get_object_or_404(Subject, slug=subject_slug)

    if scope == "subject" and selected_subject is not None:
        post_score_subquery = (
            Post.objects.filter(
                author_id=OuterRef("user_id"),
                subject=selected_subject,
            )
            .values("author_id")
            .annotate(total_score=Sum("score"))
            .values("total_score")
        )
        comment_score_subquery = (
            Comment.objects.filter(
                author_id=OuterRef("user_id"),
                post__subject=selected_subject,
            )
            .values("author_id")
            .annotate(total_score=Sum("score"))
            .values("total_score")
        )

        queryset = (
            Profile.objects.select_related("user")
            .annotate(
                post_score=Coalesce(
                    Subquery(post_score_subquery, output_field=IntegerField()),
                    0,
                ),
                comment_score=Coalesce(
                    Subquery(comment_score_subquery, output_field=IntegerField()),
                    0,
                ),
            )
            .annotate(
                subject_score=ExpressionWrapper(
                    F("post_score") + F("comment_score"),
                    output_field=IntegerField(),
                )
            )
            .filter(subject_score__gt=0)
            .order_by("-subject_score", "user_id")
        )
    else:
        queryset = Profile.objects.select_related("user").order_by(
            "-reputation_points",
            "user_id",
        )

    subjects = Subject.objects.all()

    top_profiles = list(queryset[:3])

    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    def serialize_row(profile, rank):
        username = profile.user.get_username()
        avatar_url = profile.avatar.url if profile.avatar else None
        return {
            "rank": rank,
            "user_id": profile.user_id,
            "username": username,
            "level": profile.level,
            "points": (
                int(profile.subject_score)
                if scope == "subject" and selected_subject is not None
                else profile.reputation_points
            ),
            "avatar_url": avatar_url,
            "initial": (username[:1] or "?").upper(),
        }

    leaderboard_rows = [
        serialize_row(profile, page_obj.start_index() + index)
        for index, profile in enumerate(page_obj.object_list)
    ]
    top_three = [
        serialize_row(profile, index + 1)
        for index, profile in enumerate(top_profiles)
    ]

    return render(
        request,
        "common/leaderboard.html",
        {
            "scope": scope,
            "subjects": subjects,
            "selected_subject": selected_subject,
            "top_three": top_three,
            "leaderboard_rows": leaderboard_rows,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "current_user_id": request.user.id if request.user.is_authenticated else None,
        },
    )


def info_page(request, page_key):
    page = INFO_PAGES[page_key]
    return render(
        request,
        "common/info_page.html",
        {
            "page_title": page["title"],
            "sections": page["sections"],
        },
    )


def mission(request):
    return info_page(request, "mission")


def terms(request):
    return info_page(request, "terms")


def privacy(request):
    return info_page(request, "privacy")
