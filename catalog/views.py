from django.http import Http404
from django.shortcuts import render

# Create your views here.
from .models import Book, Author, BookInstance, Genre
from django.contrib.auth.decorators import login_required


# @login_required
def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()   # The 'all()' is implied by default.

    num_genres = Genre.objects.count()
    num_books_first = Book.objects.filter(title__icontains='first').count()

    num_visits = request.session.get('num_visits', 0)      # Number of visits to this view, as counted in the session variable.
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_books_first': num_books_first,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

from django.views import generic

# class BookListView(generic.ListView):
#     model = Book
#     context_object_name = 'book_list'   # your own name for the list as a template variable
#     #queryset = Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war
#     queryset = Book.objects.all()
#     template_name = 'books/my_arbitrary_template_name_list.html'  # Specify your own template name/location

# class BookListView(generic.ListView):
#     model = Book
#
#     def get_queryset(self):
#         return Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war


# from django.contrib.auth.mixins import LoginRequiredMixin
# class MyView(LoginRequiredMixin, View):
#     login_url = '/login/'
#     redirect_field_name = 'redirect_to'


class BookListView(generic.ListView):
    model = Book
    # paginate_by = 2


    # def get_context_data(self, **kwargs):
    #     # Call the base implementation first to get the context
    #     context = super(BookListView, self).get_context_data(**kwargs)
    #     # Create any data and add it to the context
    #     context['some_data'] = 'This is just some data'
    #     return context

class BookDetailView(generic.DetailView):
    model = Book


# def book_detail_view(request, primary_key):
#     try:
#         book = Book.objects.get(pk=primary_key)
#     except Book.DoesNotExist:
#         raise Http404('Book does not exist')
#
#     return render(request, 'catalog/book_detail.html', context={'book': book})
#
# from django.shortcuts import get_object_or_404
#
# def book_detail_view(request, primary_key):
#     book = get_object_or_404(Book, pk=primary_key)
#     return render(request, 'catalog/book_detail.html', context={'book': book})
#
#

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10


    # def get_context_data(self, **kwargs):
    #     # Call the base implementation first to get the context
    #     context = super(BookListView, self).get_context_data(**kwargs)
    #     # Create any data and add it to the context
    #     context['some_data'] = 'This is just some data'
    #     return context

class AuthorDetailView(generic.DetailView):
    model = Author


from django.contrib.auth.mixins import LoginRequiredMixin

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


# from django.contrib.auth.decorators import permission_required
#
# @permission_required('catalog.can_mark_returned')
# @permission_required('catalog.can_edit')
# def my_view(request):
#     ...


# from django.contrib.auth.decorators import login_required, permission_required
#
# @login_required
# @permission_required('catalog.can_mark_returned', raise_exception=True)
# def my_view(request):


from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
class AllBorrowedBooksListView(PermissionRequiredMixin, LoginRequiredMixin, generic.ListView):

    permission_required = 'catalog.can_mark_returned'
    # Or multiple permissions
    # permission_required = ('catalog.can_mark_returned', 'catalog.can_edit')
    # Note that 'catalog.can_edit' is just an example
    # the catalog application doesn't have such permission!

    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10


    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')



import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from catalog.forms import RenewBookForm

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)



from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from catalog.models import Author

class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    # initial = {'date_of_death': '11/06/2020'}
    # permission_required = 'catalog.can_mark_returned'

class AuthorUpdate(UpdateView):
    model = Author
    fields = '__all__' # Not recommended (potential security issue if more fields added)

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')



from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from catalog.models import Book

class BookCreate(CreateView):
    model = Book
    fields = '__all__'
    # initial = {'date_of_death': '11/06/2020'}

class BookUpdate(UpdateView):
    model = Book
    fields = '__all__' # Not recommended (potential security issue if more fields added)

class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('books')









