import logging as log
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.views import generic as views
from haystack.query import SearchQuerySet

from main import feeds
from main import forms

import haystack.views
import bookmarks.views
import opinions.views
import phillyleg.models
import subscriptions.forms
import subscriptions.models
import subscriptions.views


class NewLegislationFeed (Feed):
    title = u'New Legislation'
    link = 'http://localhost:8000'
    description = u'Newly introduced legislation'
    max_items = 100

    def items(self):
        return phillyleg.models.LegFile.objects.all()[:self.max_items]

    def item_title(self, legfile):
        return u'{0.type} {0.id}'.format(legfile)

    def item_pubdate(self, legfile):
        import datetime
        d = legfile.intro_date
        current = datetime.datetime(d.year, d.month, d.day)
        return current


class CustomContentFeedView (Feed):
    def get_object(self, request, subscription_id):
        return get_object_or_404(subscription.models.Subscription,
                                 pk=subscription_id)

    def title(self, sub):
        return unicode(sub)

    def link(self, sub):
#        return sub.get_absolute_url()
        return u'http://localhost:8000/'

    def description(self, sub):
        return unicode(sub)


class SearchBarMixin (object):
    def get_searchbar_form(self):
        return forms.SimpleSearchForm()

    def get_context_data(self, **kwargs):
        context_data = super(SearchBarMixin, self).get_context_data(**kwargs)
        context_data.update({'searchbar_form': self.get_searchbar_form()})
        return context_data


class AppDashboardView (SearchBarMixin,
                        bookmarks.views.BaseBookmarkMixin,
                        views.TemplateView):
    template_name = 'main/app_dashboard.html'

    def get_context_data(self, **kwargs):
        search_form = forms.FullSearchForm()

        legfiles = phillyleg.models.LegFile.objects.all().order_by('-key')[:8]
        bookmark_data = self.get_bookmarks_data(legfiles)

        context_data = super(AppDashboardView, self).get_context_data(
            **kwargs)
        context_data.update({'legfiles': legfiles, 'bookmark_data': bookmark_data, 'search_form': search_form})

        return context_data


class SearchView (SearchBarMixin,
                  subscriptions.views.SingleSubscriptionMixin,
                  views.ListView):
    template_name = 'search/search.html'
    paginate_by = 20
    feed_data = None

    def dispatch(self, request, *args, **kwargs):
        # Construct and run a haystack SearchView so that we can use the
        # resulting values.
        self.search_view = haystack.views.SearchView(form_class=forms.FullSearchForm, searchqueryset=SearchQuerySet().order_by('-order_date'))
        self.search_view.request = request

        self.search_view.form = self.search_view.build_form()
        self.search_view.query = self.search_view.get_query()
        self.search_view.results = self.search_view.get_results()

        # The, continue with the dispatch
        return super(SearchView, self).dispatch(request, *args, **kwargs)

    def get_content_feed(self):
        queryset = self.search_view.results
        return feeds.SearchResultsFeed(queryset.query.query_filter)

    def get_queryset(self):
        search_queryset = self.search_view.results

        class SQSProxy (object):
            """
            Make a SearchQuerySet look enough like a QuerySet for a ListView
            not to notice the difference.
            """
            def __init__(self, sqs):
                self.sqs = sqs
            def __len__(self):
                return len(self.sqs)
            def __iter__(self):
                return (result.object for result in self.sqs)
            def __getitem__(self, key):
                if isinstance(key, slice):
                    return [result.object for result in self.sqs[key] if result is not None]
                else:
                    return self.sqs[key].object

        return SQSProxy(search_queryset)

    def get_context_data(self, **kwargs):
        """
        Generates the actual HttpResponse to send back to the user.
        """
        context = super(SearchView, self).get_context_data(**kwargs)
        context['form'] = self.search_view.form
        log.debug(context)
        return context


class LegislationStatsMixin (object):
    def get_queryset(self):
        queryset = super(LegislationStatsMixin, self).get_queryset()

        now = datetime.date.today()
        four_weeks = datetime.timedelta(days=28)
        queryset = queryset.filter(intro_date__gte=now-four_weeks)
        return queryset


class LegislationListView (SearchBarMixin,
                           subscriptions.views.SingleSubscriptionMixin,
                           bookmarks.views.MultipleBookmarkedObjectsMixin,
                           views.ListView):
    model = phillyleg.models.LegFile
    template_name = 'phillyleg/legfile_list.html'
    paginate_by = 10

    def get_content_feed(self):
        return feeds.NewLegislationFeed()

    def get_queryset(self):
        queryset = super(LegislationListView, self).get_queryset()
        return queryset.order_by('-intro_date', '-key')


class LegislationDetailView (SearchBarMixin,
                             subscriptions.views.SingleSubscriptionMixin,
                             bookmarks.views.SingleBookmarkedObjectMixin,
                             opinions.views.SingleOpinionTargetMixin,
                             views.DetailView):
    model = phillyleg.models.LegFile
    template_name = 'phillyleg/legfile_detail.html'

    def get_content_feed(self):
        legfile = self.object
        return feeds.LegislationUpdatesFeed(pk=legfile.pk)

#    def on_object_gotten(self, legfile):
#        # Construct the feed_data factory
#        if not self.feed_data:
#            self.feed_data = lambda: feeds.LegislationUpdatesFeed(pk=legfile.pk)

#    def get_object(self):
#        legfile = super(LegislationDetailView, self).get_object()

#        # Intercept the object
#        self.on_object_gotten(legfile)

#        return legfile


class BookmarkListView (SearchBarMixin,
                        views.ListView):
    template_name = 'main/bookmark_list.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated():
            return [bm.content for bm in user.bookmarks.all()]
        else:
            return []


class SubscriptionManagementView (SearchBarMixin,
                                  views.TemplateView):
    template_name = 'main/subscription_management.html'
