from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.views.generic import ListView, DetailView, TemplateView
import phillyleg.models
import phillyleg.resources

import main.views
import subscriptions.views
import bookmarks.views
import haystack.views
import opinions.views

urlpatterns = patterns('',
    # Example:
    #(r'^philly_legislative/', include('philly_legislative.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^login/$', 'django.contrib.auth.views.login', name='registration_login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='registration_logout'),

    url(r'^social/', include('social_auth.urls')),
    url(r'', include('captcha.backends.default.urls')),

    url(r'^subscribe/$', subscriptions.views.CreateSubscriptionView.as_view(), name='subscribe'),
    url(r'^unsubscribe/(?P<pk>\d+)/$', subscriptions.views.DeleteSubscriptionView.as_view(), name='unsubscribe'),

    url(r'^bookmark/$', bookmarks.views.CreateBookmarkView.as_view(), name='bookmark'),
    url(r'^unbookmark/(?P<pk>\d+)/$', bookmarks.views.DeleteBookmarkView.as_view(), name='unbookmark'),

    url(r'express_opinion/$', opinions.views.ExpressOpinionView.as_view(), name='express_opinion'),
    url(r'revise_opinion/(?P<pk>\d+)/$', opinions.views.ReviseOpinionView.as_view(), name='revise_opinion'),

    url(r'^$',
        main.views.AppDashboardView.as_view(),
        name='main_dashboard'),

    url(r'^legislation/$',
        main.views.LegislationListView.as_view(),
        name='legislation_list'),
    url(r'^legislation/(?P<pk>\d+)$',
        main.views.LegislationDetailView.as_view(),
        name='legislation_detail'),

    url(r'^legislation.rss$',
        main.views.NewLegislationFeed(),
        name='legislation_feed'),

    url(r'^minutes/$', ListView.as_view(
        model=phillyleg.models.LegMinutes,
        template_name='phillyleg/legminutes_list.html'),
        name='minutes_list'),
    url(r'^minutes/(?P<pk>\d+)$', DetailView.as_view(
        model=phillyleg.models.LegMinutes,
        template_name='phillyleg/legminutes_detail.html'),
        name='minutes_detail'),

    url(r'^bookmarks/$',
        main.views.BookmarkListView.as_view(),
        name='bookmark_list'),

    url(r'^subscriptions/$',
        main.views.SubscriptionManagementView.as_view(),
        name='subscription_management'),

    url(r'^search/$', main.views.SearchView.as_view(),
        name='search'),

    url(r'^(?P<user_pk>\d+)/subscriptions/$', TemplateView.as_view(template_name='base.html'), name='user_subscriptions'),
    url(r'^(?P<user_pk>\d+)/subscriptions/(?P<bookmark_pk>\d+)/$', TemplateView.as_view(template_name='base.html'), name='user_subscription'),

    # RSS
    url(r'^rss/$', main.views.LegFileListFeedView(),
        name='rss_feed'),

    # API v1
    url(r'^api/v1/councilmembers/$',
        phillyleg.resources.CouncilMemberListView.as_view(),
        name='api_councilmember_list'),
    url(r'^api/v1/councilmembers/(?P<pk>.+)$',
        phillyleg.resources.CouncilMemberInstanceView.as_view(),
        name='api_concilmember_instance'),

    # Flat pages
    url(r'about/',
        TemplateView.as_view(template_name='about.html'),
        name='about')

)
