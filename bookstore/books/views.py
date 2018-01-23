from django.shortcuts import render,redirect
from books.models import Books
# 常量文件
from books.enums import *
# 反向解析
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator


def index(request):
    '''显示首页'''
    # 查询每个种类的3个新品信息和4个销量最好的商品信息
    # 商品模型管理器的方法 get_books_by_type(self, type_id, limit=None, sort='default')
    
    # PYTHON
    python_new = Books.objects.get_books_by_type(PYTHON, 3, sort='new')
    python_hot = Books.objects.get_books_by_type(PYTHON, 4, sort='hot')
     
    # JAVASCRIPT
    javascript_new = Books.objects.get_books_by_type(JAVASCRIPT, 3, sort='new')
    javascript_hot = Books.objects.get_books_by_type(JAVASCRIPT, 4, sort='hot')
    
    # ALGORITHMS
    algorithms_new = Books.objects.get_books_by_type(ALGORITHMS, 3, sort='new')
    algorithms_hot = Books.objects.get_books_by_type(ALGORITHMS, 4, sort='hot')
    
    # MACHINELEARNING
    machinelearning_new = Books.objects.get_books_by_type(MACHINELEARNING, 3, sort='new')
    machinelearning_hot = Books.objects.get_books_by_type(MACHINELEARNING, 4, sort='hot')
    
    # OPERATINGSYSTEM
    operatingsystem_new = Books.objects.get_books_by_type(OPERATINGSYSTEM, 3, sort='new')
    operatingsystem_hot = Books.objects.get_books_by_type(OPERATINGSYSTEM, 4, sort='hot')
    
    # DATABASE
    database_new = Books.objects.get_books_by_type(DATABASE, 3, sort='new')
    database_hot = Books.objects.get_books_by_type(DATABASE, 4, sort='hot')
    
    sort_new = [python_new, javascript_new, algorithms_new, machinelearning_new, operatingsystem_new, database_new]
    sort_hot = [python_hot, javascript_hot, algorithms_hot, machinelearning_hot, operatingsystem_hot, database_hot]
    # 使用模板
    return render(request, 'books/index.html', locals())


# 显示商品详情页,需要展示当前商品细节以及推荐两本新书
def detail(request, books_id):
    # 获取当前商品
    books = Books.objects.get_books_by_id(books_id)
    if books is None:
        # 如果商品不存在
        return redirect(reverse('books:index'))
    # 获取两本新书
    books_list = Books.objects.get_books_by_type(books.type_id,2,'new')
    return render(request, 'books/detail.html', locals())


# 在首页中每一类商品点击查看更多，会进入list展示页面
# 所以需要的参数有type_id,分页page
def list(request, type_id, page):
    # request.GET.get取get请求问号后面的参数，sort,如果没传参那么默认值是default
    sort = request.GET.get('sort', 'default')
    book_list = Books.objects.get_books_by_type(type_id=type_id, sort=sort)
    # book_list要分页展示的内容，每1条为一页
    paginator = Paginator(book_list, 1)
    # 获取分页的数量num_pages
    num_pages = paginator.num_pages
    page = int(page)
    if page == '' or int(page) > num_pages:
        page = 1
    else:
        page = int(page)
    # 取第page页数据，返回值是一个Page类的实例对象
    # 参数是当前页
    book_list = paginator.page(page)
    if num_pages < 4:
        # 总页数 <= 3, 显示所有页码
        # 显示页码范围range
        pages = range(1, num_pages+1)
    elif page <= 2:
        # 总页数 > 3且当前页是前2页，显示前3页
        pages = range(1,4)
    elif num_pages-page <=1:
        # 总页数 > 4且当前页是后2页，显示后3页
        pages = range(num_pages-2, num_pages+1)
    else:
        # 其他情况，显示当前页前1页，后1页，当前页
        pages = range(page-1, page+2)
    # 新品推荐
    books_new = Books.objects.get_books_by_type(type_id, 2, 'new')
    type_title = BOOKS_TYPE[(int(type_id))]
    return render(request, 'books/list.html', locals())
    