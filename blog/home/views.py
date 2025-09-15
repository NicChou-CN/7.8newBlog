from django.shortcuts import render
from django.views import View
# Create your views here.
from home.models import ArticleCategory,Article,Comment
from django.http.response import HttpResponseNotFound
from django.shortcuts import redirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage
class IndexView(View):
    def get(self, request):
        # 获取所有分类信息
        categories = ArticleCategory.objects.all()
        # 接收用户点击的分类ID
        cat_id = request.GET.get('cat_id', 1)
        # 根据分类id进行分类查询
        try:
            category = ArticleCategory.objects.get(id=cat_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseNotFound('没有此分类')
        # 获取分页参数
        page_num = request.GET.get('page_num',1)
        page_size = request.GET.get('page_size',10)
        # 根据分类信息查询文章数据
        articles = Article.objects.filter(category=category)
        # 创建分页器
        paginator = Paginator(articles,per_page=page_size)
        # 进行分页处理
        try:
            page_articles = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('Empty page')
        # 总页数
        total_page = paginator.num_pages
        # 组织数据传递给模板
        context = {
            'categories': categories, # 分类信息
            'category': category, # 当前分类
            'articles': page_articles,
            'page_size': page_size,
            'page_num': page_num,
            'total_page': total_page,
        }
        return render(request, 'index.html', context=context)

class DetailView(View):
    def get(self, request):
        # 接收文章id信息
        id = request.GET.get('id')
        # 根据文章id进行数据查询
        try:
            article = Article.objects.get(id=id)
        except Article.DoesNotExist:
            return render(request,'404.html')
        else:
            # 让浏览量+1
            article.total_views += 1
            article.save()
        # 查询分类数据
        categories = ArticleCategory.objects.all()
        # 获取分页请求参数
        page_num = request.GET.get('page_num',1)
        page_size = request.GET.get('page_size',10)
        # 根据文章信息查询评论数据
        comments = Comment.objects.filter(article=article).order_by('-created')
        # 获取评论总数
        total_count = comments.count()
        # 创建分页器
        paginator = Paginator(comments,per_page=page_size)
        # 进行分页处理
        try:
            page_comments = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('Empty page')
        # 总页数
        total_page = paginator.num_pages
        # 组织模板数据
        # 查询浏览量前10的文章数据
        hot_articles = Article.objects.order_by('-total_views')[:9]


        # 组织模板数据
        context = {
            'categories': categories,
            'category': article.category,
            'article': article,
            'hot_articles':hot_articles,
            'comments': page_comments,
            'total_count': total_count,
            'page_size': page_size,
            'total_page': total_page,
            'page_num': page_num
        }
        return render(request,'detail.html',context=context)
    def post(self, request):
        # 接收用户信息
        user = request.user
        # 判断用户是否登录
        if user and user.is_authenticated:
            # 登录用户可以接收form数据
            #    接收评论数据
            id = request.POST.get('id')
            content = request.POST.get('content')
            #    验证文章是否存在
            try:
                article = Article.objects.get(id=id)
            except Article.DoesNotExist:
                return render(request, '404.html')
            #    保存评论数据
            Comment.objects.create(
                user=user,
                article=article,
                content=content
            )
            #    修改文章的评论数量
            article.comment_count += 1
            article.save()
            # 刷新当前页面
            path = reverse('home:detail')+'?id='+id
            return redirect(path)
        # 如果没有登录 返回登录页面
        else:
            return redirect(reverse('users:login'))
